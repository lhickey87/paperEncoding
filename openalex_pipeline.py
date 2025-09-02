import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import json
import argparse
import logging

def reconstructAbstract(inverted_index):
    # when paper has no abstract
        if not inverted_index:
            return ""
        try:
            max_index = max(pos for positions in inverted_index.values() for pos in positions)
            word_list = [""] * (max_index + 1)
            
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_list[pos] = word

            if isinstance(" ".join(word_list), str):
                logging.info("ALL IS GOOD")
            return " ".join(word_list)
        except Exception as e:
            return ""
    
# Define your custom transformation logic
class ProcessOpenAlexRecord(beam.DoFn):

     # Return empty string if inverted_index is malformed
    """
    User-defined function (UDF) to transform a JSON record to match the target BigQuery schema.
    This mirrors the logic from your JavaScript UDF, adapted for Python.
    """
    def process(self, in_json_string):
        try:
            # Parse the input JSON string into a Python dictionary
            data = json.loads(in_json_string)
            
            # --- START: Added logic to handle null 'id' or 'doi' ---
            record_id = data.get('id')
            if record_id is None:
                logging.warning(f"Skipping record due to missing or null 'id' field: {in_json_string[:150]}...")
                return # Do not yield this record

            record_doi = data.get('doi')
            if record_doi is None:
                logging.warning(f"Skipping record due to missing or null 'doi' field: {in_json_string[:150]}...")
                return # Do not yield this record
            # --- END: Added logic ---

            record = {}
            # Get simple fields and handle potential missing values
            record['id'] = record_id
            record['doi'] = record_doi
            record['title'] = data.get('title')
            record['created_date'] = data.get('created_date')
            record['cited_by_count'] = data.get('cited_by_count')

            # Handle repeated fields (arrays)
            record['corresponding_author_ids'] = data.get('corresponding_author_ids', [])
            record['related_works'] = data.get('related_works', [])
            record['referenced_works'] = data.get('referenced_works', [])

            # Memory-optimized way to handle author names using a for loop.
            author_names = []
            authorships = data.get('authorships')
            if authorships:
                for authorship in authorships:
                    if authorship and authorship.get('author') and authorship['author'].get('display_name'):
                        author_names.append(authorship['author']['display_name'])
            record['author_names'] = author_names

            # 'primary_topic' is no longer included in the schema, so we don't extract it here.

            # Handle the JSON field (stored as a string in BigQuery, so no further parsing here)
            record['abstract'] = reconstructAbstract(data.get('abstract_inverted_index'))
            # Yield the transformed record (dictionary)
            yield record

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON record: {in_json_string[:150]}... Error: {e}")
            # Filter out malformed JSON records by not yielding anything
        except Exception as e:
            logging.error(f"Error processing record: {in_json_string[:150]}... Error: {e}")
            # Filter out records that cause other processing errors

# Define the BigQuery schema (important to match your target table)
# This schema now strictly matches the BigQuery table schema from your screenshot
BIGQUERY_SCHEMA = {
    'fields': [
        {'name': 'abstract', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'cited_by_count', 'type': 'INTEGER', 'mode': 'NULLABLE'},
        {'name': 'corresponding_author_ids', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'created_date', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'doi', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'related_works', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'title', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'author_names', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'referenced_works', 'type': 'STRING', 'mode': 'REPEATED'},
        {'name': 'id', 'type': 'STRING', 'mode': 'REQUIRED'}, # Moved 'id' to the end to match screenshot order (optional but good for debugging)
    ]
}

def run():
    parser = argparse.ArgumentParser(description="Dataflow pipeline to load compressed JSON from GCS to BigQuery.")
    parser.add_argument(
        '--input_gcs_path',
        required=True,
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
        default=50,
        help='Worker disk size in GB.')

    known_args, beam_args = parser.parse_known_args()

    beam_pipeline_args = [
        f'--temp_location={known_args.temp_location}',
        f'--staging_location={known_args.staging_location}',
        f'--project={known_args.project}',
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