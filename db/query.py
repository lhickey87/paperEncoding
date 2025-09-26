import os
from google.cloud import bigquery
import logging


def _get_field(paper,field):
    return paper[field]

def doiEntered(doi: str):
    client = bigquery.Client()
    full_doi_url = f"https://doi.org/{doi}"
    sql_query = """
    SELECT * FROM `hazel-quanta-470113-h4.openAlexDataset.EWORKS` WHERE doi = @doi
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
            related_works = _get_field(paper,"related_works") 
            referenced_works = _get_field(paper,"referenced_works") 
            oa_url = _get_field(paper,"oa_url") 
            cited_by_count = _get_field(paper,"cited_by_count")

            return {'authors':authors,
                    'author_ids': author_ids,
                    'title': title, 
                    'abstract': abstract, 
                    'related_works': related_works, 
                    'referenced_works': referenced_works,
                    'oa_url': oa_url,
                    'cited_by_count':cited_by_count}
        #This should return a dictionary of author_names, title and abstract
        else:
            logging.warning(f"No results found in BigQuery for DOI: {doi}")
            return None
    except Exception as e:
        # Use logging.error for exceptions
        logging.error(f"An exception occurred while querying for DOI {doi}: {e}", exc_info=True)
        return None
    
def vectorSearch(doi: str): 
    client = bigquery.Client()
    #may need to tweak fraction of lists searched as we go
    sql_query = """SELECT 
        works.doi, 
        works.title, 
        works.authors, 
        works.abstract,
        results.distance
    FROM 
        VECTOR_SEARCH(
            TABLE `hazel-quanta-470113-h4.openAlexDataset.EMBED_TEST`,
            'embedding',
            (SELECT embedding FROM `hazel-quanta-470113-h4.openAlexDataset.EMBED_TEST` WHERE doi = @doi),
            top_k => 10,
            distance_type => 'COSINE',
            options => '{"fraction_lists_to_search": 0.10}'  
        ) AS results
        JOIN (
            SELECT doi, authors, title, abstract 
            FROM `hazel-quanta-470113-h4.openAlexDataset.EWORKS_TEST`
        ) AS works
            ON results.base.doi = works.doi
        WHERE results.distance > 0
        ORDER BY results.distance ASC;"""

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("doi", "STRING", doi),
        ]
    )
    logging.info(f"trying to find reccomendations for {doi}")
    try:
        queryJob = client.query(sql_query, job_config)
        results = queryJob.result()
        papers = []
        
        for row in results:
            author_names = [author.get('name') for author in row['authors']]  
            paper_title = row['title']  
            distance = row['distance']    
            doi = row['doi']  
            abstract = row['abstract']  
            paper = {'authors': author_names, 'title': paper_title, 'distance': distance, 'doi': doi, 'abstract': abstract}
            papers.append(paper)
        
        return papers

    except Exception as e:
        return None


def titledPaper(title: str):
    client = bigquery.Client()
    sql_query = """SELECT
            t.title,
            t.doi,
            t.authors
        FROM
            `hazel-quanta-470113-h4.openAlexDataset.EWORKS` AS t
        WHERE
            LOWER(t.title) LIKE LOWER(CONCAT('%', @title, '%'))
        LIMIT 10
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("title", "STRING", title), 
        ]
    )

    logging.info(f"sql query for titled paper {sql_query}") 
    
    try:

        queryJob = client.query(sql_query, job_config) 
        results = queryJob.result()
        papers = []

        for row in results:
            authors = [author['name'] for author in row['authors']]
            title = row['title']
            doi = row['doi']
            paper = {'authors': authors, 'title': title, 'doi':doi}
            papers.append(paper)

        if not papers:
            return None

        return papers

    except Exception as e:
        return None