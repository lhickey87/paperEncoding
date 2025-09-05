import os
from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

table="hazel-quanta-470113-h4.openAlexDataset.WORKS" 

def _get_field(paper,field):
    return paper[field]

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
        queryJob = client.query(sql_query, job_config=job_config)

        results = queryJob.result() 

        paper = next(results, None)
        if paper:
            logging.info("Paper is found")
            authors = [author.get('name') for author in paper['authors']] 
            author_ids = [author.get('id') for author in paper['authors']]
            title = _get_field(paper, "title")
            abstract = _get_field(paper,"abstract")
            Id = _get_field(paper,"paper_id")
            related_works = _get_field(paper,"related_works") 
            referenced_works = _get_field(paper,"referenced_works") 
            created_date = _get_field(paper, "created_date")
            cited_by_api_url = _get_field(paper,"cited_by_api_url")
            oa_url = _get_field(paper,"oa_url") 
            oa_status = _get_field(paper,"oa_status")  
            cited_by_count = _get_field(paper,"cited_by_count")

            return {'authors':authors,
                    'author_ids': author_ids,
                    'title': title, 
                    'abstract': abstract, 
                    'id': Id, 
                    'related_works': related_works, 
                    'referenced_works': referenced_works,
                    'created_date': created_date,
                    'cited_by_api_url':cited_by_api_url,
                    'oa_url': oa_url,
                    'oa_status':oa_status,
                    'cited_by_count':cited_by_count}
        #This should return a dictionary of author_names, title and abstract
        else:
            logging.warning(f"No results found in BigQuery for DOI: {doi}")
            return None
    except Exception as e:
        # Use logging.error for exceptions
        logging.error(f"An exception occurred while querying for DOI {doi}: {e}", exc_info=True)
        return None
    

def getRelatedAbstract(doi:str) -> str:
    client = bigquery.Client()
    sql_query = f"""
    SELECT abstract FROM `{table}` WHERE doi = @doi
    """
    jobConfig = bigquery.QueryJobConfig(
        query_parameters = [
            bigquery.ScalarQueryParameter("doi","STRING",doi)
        ]
    )
    try:
        queryJob = client.query(sql_query,jobConfig)
        results = queryJob.result()
        abstract = next(results,None)
        if not abstract:
            logging.warning("Abstract seems to be empty for {doi}")
            return None
        
        return abstract

    except Exception as e:
        logging.error(f"Was unable to load the following query for {doi}: {e}")
        return None