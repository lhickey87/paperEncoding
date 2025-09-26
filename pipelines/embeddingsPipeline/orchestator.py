import subprocess
import time
from google.cloud import storage

def count_files_to_process():
    client = storage.Client()
    bucket = client.bucket("paperrank")
    blobs = list(bucket.list_blobs(prefix="bq-export/"))
    json_files = [b for b in blobs if b.name.endswith('.json.gz')]
    return len(json_files)

def launch_jobs():
    PROJECT_ID = "hazel-quanta-470113-h4"  # UPDATE THIS
    REGION = "us-east1"
    JOB_NAME = "embedding-processor"
    FILES_PER_JOB = 10  
    
    total_files = count_files_to_process()
    num_jobs = (total_files + FILES_PER_JOB - 1) // FILES_PER_JOB
    
    print(f"Launching {num_jobs} jobs, {FILES_PER_JOB} files each")
    
    BATCH_SIZE = 20 
    
    for i in range(0, num_jobs, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, num_jobs)
        
        for job_idx in range(i, batch_end):
            cmd = [
                "gcloud", "run", "jobs", "execute", JOB_NAME,
                "--region", REGION,
                "--update-env-vars", f"FILE_INDEX={job_idx},FILES_PER_JOB={FILES_PER_JOB}",
                "--async"
            ]
            
            
            subprocess.run(cmd)
        
        if batch_end < num_jobs:
            print(f"Waiting 30 seconds before next batch...")
            time.sleep(30)

if __name__ == "__main__":
    launch_jobs()