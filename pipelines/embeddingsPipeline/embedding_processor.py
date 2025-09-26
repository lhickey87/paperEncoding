import os
import json
import logging
import gzip
import time
import tempfile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from typing import List

import torch
import pyarrow as pa
import pyarrow.parquet as pq
from sentence_transformers import SentenceTransformer
from google.cloud import storage, bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingProcessor:
    def __init__(self):
        self.input_bucket = "paperrank"
        self.input_prefix = "bq-export/"
        self.output_bucket = os.environ.get("OUTPUT_BUCKET", "your-output-bucket")
        self.output_prefix = "embeddings/parquet/"
        
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.batch_size = 512
        self.max_text_length = 2048
        
        self.storage_client = storage.Client()
        self._setup_model()
        
    def _setup_model(self):
        cpu_count = os.cpu_count() or 4
        torch.set_num_threads(cpu_count)
        
        logger.info(f"Loading model {self.model_name} with {cpu_count} CPU threads")
        self.model = SentenceTransformer(self.model_name, device='cpu')
        self.model.max_seq_length = 128 
        
    def get_files_to_process(self) -> List[str]:
        all_files = self._list_input_files()
        processed_files = self._get_processed_file_ids()
        
        remaining = [f for f in all_files if self._extract_file_id(f) not in processed_files]
        
        logger.info(f"Files - Total: {len(all_files)}, Processed: {len(processed_files)}, Remaining: {len(remaining)}")
        return remaining
    
    def _list_input_files(self) -> List[str]:
        bucket = self.storage_client.bucket(self.input_bucket)
        blobs = bucket.list_blobs(prefix=self.input_prefix)
        return [f"gs://{self.input_bucket}/{blob.name}" for blob in blobs if blob.name.endswith('.json.gz')]
    
    def _get_processed_file_ids(self) -> set:
        bucket = self.storage_client.bucket(self.output_bucket)
        blobs = bucket.list_blobs(prefix=f"{self.output_prefix}markers/")
        return {blob.name.split('/')[-1].replace('.done', '') for blob in blobs if blob.name.endswith('.done')}
    
    def _extract_file_id(self, file_path: str) -> str:
        return file_path.split('/')[-1].replace('.json.gz', '')
    
    def _mark_file_processed(self, file_id: str):
        bucket = self.storage_client.bucket(self.output_bucket)
        blob = bucket.blob(f"{self.output_prefix}markers/{file_id}.done")
        blob.upload_from_string("")
    
    def process_file(self, file_path: str):
        file_id = self._extract_file_id(file_path)
        logger.info(f"Processing {file_id}")
        
        try:
            papers = self._extract_papers(file_path)
            if not papers:
                logger.warning(f"No valid papers found in {file_id}")
                self._mark_file_processed(file_id)
                return
            
            embeddings = self._generate_embeddings([paper['text'] for paper in papers])
            
            self._save_to_parquet(file_id, papers, embeddings)
            self._mark_file_processed(file_id)
            
            logger.info(f"Completed {file_id}: {len(papers)} papers processed")
            
        except Exception as e:
            logger.error(f"Failed to process {file_id}: {e}")
            raise
    
    def _extract_papers(self, file_path: str) -> List[dict]:
        papers = []
        
        with tempfile.NamedTemporaryFile(suffix='.json.gz', delete=False) as tmp_file:

            bucket_name, blob_name = file_path.replace('gs://', '').split('/', 1)
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(tmp_file.name)
            
            with gzip.open(tmp_file.name, 'rt', encoding='utf-8') as f:
                for line in f:
                    try:
                        paper = json.loads(line)
                        doi = paper.get('doi')
                        abstract = paper.get('abstract', '')
                        
                        if doi and abstract:
                            papers.append({'doi': doi, 'text': abstract})
                            
                    except json.JSONDecodeError:
                        continue  
            
            os.unlink(tmp_file.name)
        
        logger.info(f"Extracted {len(papers)} valid papers")
        return papers
    
    def _generate_embeddings(self, texts: List[str]):
        logger.info("Generating embeddings...")
        start_time = time.time()
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        elapsed = time.time() - start_time
        rate = len(texts) / elapsed
        logger.info(f"Generated {len(texts)} embeddings in {elapsed:.1f}s ({rate:.0f} docs/sec)")
        
        return embeddings.tolist()
    
    def _save_to_parquet(self, file_id: str, papers: List[dict], embeddings: List[List[float]]):
        logger.info("Saving to Parquet...")
        
        table = pa.table({
            'doi': [paper['doi'] for paper in papers],
            'embedding': embeddings
        })
        
        output_path = f"{self.output_prefix}data/{file_id}.parquet"
        bucket = self.storage_client.bucket(self.output_bucket)
        blob = bucket.blob(output_path)
        
        with BytesIO() as buffer:
            pq.write_table(table, buffer, compression='snappy')
            buffer.seek(0)
            blob.upload_from_file(buffer)


def main():
    file_index = int(os.environ.get("FILE_INDEX", "0"))
    files_per_job = int(os.environ.get("FILES_PER_JOB", "10"))
    
    processor = EmbeddingProcessor()
    all_files = sorted(processor.get_files_to_process())
    
    start_idx = file_index * files_per_job
    end_idx = min(start_idx + files_per_job, len(all_files))
    
    if start_idx >= len(all_files):
        logger.info(f"No files to process for job {file_index}")
        return
    
    job_files = all_files[start_idx:end_idx]
    logger.info(f"Job {file_index} processing {len(job_files)} files")
    
    num_threads = 4
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(processor.process_file, job_files)
    
    logger.info(f"Job {file_index} completed")

if __name__ == "__main__":
    main()