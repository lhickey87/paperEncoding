import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import json
import argparse
import logging

class ProcessOpenAlexRecord(beam.DoFn):
    def process(self, in_json_string):
        try:
            data = json.loads(in_json_string)

            # Apply filters in a performance-friendly order
            pType = data.get('type')
            if pType not in ['article', 'preprint']:
                logging.warning(f"Skipping non-article/preprint type: {pType}")
                return

            record_id = data.get('id')
            if record_id is None:
                logging.warning("Skipping record due to missing or null 'id' field.")
                return

            if data.get('abstract_inverted_index') is None:
                logging.warning("Skipping record with no abstract.")
                return

            openAccess_data = data.get('open_access', {})
            if not openAccess_data.get('is_oa'):
                logging.warning("Skipping record that is not open access.")
                return

            record = {
                'paper_id': record_id,
                'doi': data.get('doi'),
                'title': data.get('title'),
                'created_date': data.get('created_date'),
                'cited_by_count': data.get('cited_by_count'),
                'abstract': self.reconstructAbstract(data.get('abstract_inverted_index')),
                'related_works': data.get('related_works',[]),
                'referenced_works': data.get('referenced_works', []),
                'cited_by_api_url': data.get('cited_by_api_url'),
                'oa_status': openAccess_data.get('oa_status'),
                'oa_url': openAccess_data.get('oa_url')
            }

            author_info = []
            authorships = data.get('authorships')
            if authorships:
                for authorship in authorships:
                    author = authorship.get('author')
                    if author and author.get('display_name') and author.get('id'):
                        author_info.append({
                            'name': author.get('display_name'),
                            'id': author.get('id')
                        })
            record['authors'] = author_info

            yield record

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON record: {e}")
        except Exception as e:
            logging.error(f"Error processing record: {e}")

    def reconstructAbstract(self, inverted_index):
        if not inverted_index:
            return ""
        try:
            max_index = max(pos for positions in inverted_index.values() for pos in positions)
            word_list = [""] * (max_index + 1)
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_list[pos] = word
            return " ".join(word_list)
        except Exception as e:
            return "" 

# Define the BigQuery schema (important to match your target table)
# This schema now strictly matches the BigQuery table schema from your screenshot
BIGQUERY_SCHEMA = {
    'fields': [
        {'name': 'abstract', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'cited_by_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'cited_by_api_url', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'created_date', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'doi', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'related_works', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'title', 'type': 'STRING', 'mode': 'NULLABLE'},
        {
            'name': 'authors',
            'type': 'RECORD',
            'mode': 'REPEATED',
            'fields': [
                {'name': 'name', 'type': 'STRING', 'mode': 'NULLABLE'},
                {'name': 'id', 'type': 'STRING', 'mode': 'NULLABLE'}
            ]
        },
        {'name': 'referenced_works', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'oa_url', 'type': 'STRING', 'mode': 'NULLABLE'},        
        {'name': 'oa_status', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'paper_id', 'type': 'STRING', 'mode': 'REQUIRED'}
    ]
}

def run():
    parser = argparse.ArgumentParser(description="Dataflow pipeline to load compressed JSON from GCS to BigQuery.")
    parser.add_argument(
        '--input_gcs_path',
        default='gs://paperrank/data/works/updated_date=*/*.gz', 
        help='Path to the input compressed JSON file(s) in GCS (e.g., gs://your-bucket/data/*.json.gz)')
    parser.add_argument(
        '--output_bigquery_table',
        required=True,
        help='BigQuery table to write to (e.g., project_id:dataset.table_name)')
    parser.add_argument(
        '--temp_location',
        required=True,
        help='Cloud Storage location for temporary files (e.g., gs://your-bucket/temp)')
    parser.add_argument(
        '--staging_location',
        required=True,
        help='Cloud Storage location for staging files (e.g., gs://your-bucket/staging)')
    parser.add_argument(
        '--project',
        required=True,
        help='Your Google Cloud project ID')
    parser.add_argument(
        '--worker_machine_type',
        required = True,
        help = 'Worker Machine type'
    )
    parser.add_argument(
        '--region',
        default='us-east1',
        help='Google Cloud region for Dataflow job')
    parser.add_argument(
        '--runner',
        default='DataflowRunner',
        help='The pipeline runner to use (e.g., DirectRunner, DataflowRunner)')
    parser.add_argument(
        '--disk_size_gb',
        type=int,
        default=250,
        help='Worker disk size in GB.')

    known_args, beam_args = parser.parse_known_args()

    beam_pipeline_args = [
        f'--temp_location={known_args.temp_location}',
        f'--staging_location={known_args.staging_location}',
        f'--project={known_args.project}',
        f'--worker_machine_type={known_args.worker_machine_type}',
        f'--region={known_args.region}',
        f'--runner={known_args.runner}',
        f'--disk_size_gb={known_args.disk_size_gb}',
    ]
    beam_pipeline_args.extend(beam_args)

    pipeline_options = PipelineOptions(beam_pipeline_args)

    with beam.Pipeline(options=pipeline_options) as p:
        lines = p | 'ReadFromGCS' >> beam.io.ReadFromText(known_args.input_gcs_path)

        transformed_records = (
            lines
            | 'ProcessRecords' >> beam.ParDo(ProcessOpenAlexRecord())
        )

        transformed_records | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
            table=known_args.output_bigquery_table,
            schema=BIGQUERY_SCHEMA,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()