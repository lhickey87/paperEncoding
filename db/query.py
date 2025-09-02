import os
from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
client = bigquery.Client()

table="hazel-quanta-470113-h4.openAlexDataset.WORKS" 

def doiEntered(doi: str):
    client = bigquery.Client()
    full_doi_url = f"https://doi.org/{doi}"
    sql_query = f"""
    SELECT * FROM `{table}` WHERE doi = @doi
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("doi", "STRING", full_doi_url)
        ]
    )
    try:
        # Corrected line
        queryJob = client.query(sql_query, job_config=job_config)

        results = queryJob.result() 

        paper = next(results, None)
        if paper:
            logging.info("Paper is found")
            author_names = paper['author_names']
            title = paper['title']
            abstract = paper['abstract']
            Id = paper['id']
            related_works = paper['related_works']
            referenced_works = paper['referenced_works']
            created_date = paper['created_date']


            return {'author_names':author_names, 
                    'title': title, 
                    'abstract': abstract, 
                    'id': Id, 
                    'related_works': related_works, 
                    'referenced_works': referenced_works,
                    'created_date': created_date}
        #This should return a dictionary of author_names, title and abstract
        else:
            logging.warning(f"No results found in BigQuery for DOI: {doi}")
            return None
    except Exception as e:
        # Use logging.error for exceptions
        logging.error(f"An exception occurred while querying for DOI {doi}: {e}", exc_info=True)
        return None