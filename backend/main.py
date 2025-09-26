# Save this code as 'main.py' in your project directory
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db.query import doiEntered, vectorSearch, titledPaper
from google.cloud import bigquery
# from db.connection import returnPaper  # Your function to query MongoDB
import httpx  
import asyncio
import certifi
import concurrent
import urllib.parse
import logging

app = FastAPI()


origins = [
    "https://paperrank-backend-651365523485.us-east1.run.app/",
    "http://localhost:8501",  # for local testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

@app.get("/paper_details/{doi:path}")
async def get_paper_details(doi: str):

    main_paper = doiEntered(doi)
    # This needs doiEntered as well
    if not main_paper:
        raise HTTPException(status_code=404, detail="Paper not found in the database.")
    
    print('ented app.get method from streamlit app')
    paper = {
        "title": main_paper.get("title"),
        "author_ids": main_paper.get('author_ids'),
        "referenced_works": main_paper.get('referenced_works'),
        "oa_url": main_paper.get('oa_url'),
        "cited_by_count":main_paper.get("cited_by_count"),
        "authors": main_paper.get("authors", []),
        "abstract": main_paper.get("abstract", ""),
        "related_works": main_paper.get("related_works", [])
    }
    print(paper['title'])

    related_works_urls = paper.get('related_works', [])
    related_works_details = []

    async with httpx.AsyncClient(verify=certifi.where()) as client:

        tasks = []
        for work_url in related_works_urls: 
            api_url = work_url.replace("openalex.org/", "api.openalex.org/works/")
            tasks.append(client.get(api_url))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for response in responses:
            if isinstance(response, httpx.Response) and response.status_code == 200:
                work_data = response.json()
                if work_data.get('doi'):
                    print(work_data.get('doi'))
                    related_works_details.append({
                        "title": work_data.get('title'),
                        "doi": work_data.get('doi'),
                        'publication_year': work_data.get('publication_year')
                    })

    return {
        "paper": paper, 
        "related_works": related_works_details
    }

@app.get("/vector_search/{doi:path}")
async def get_vector_search(doi: str):
    logging.info(f"Received request for vector search with raw DOI: {doi}")
    
    if not doi.startswith("https://doi.org/"):
        if doi.startswith("doi.org/"):
            full_doi = f"https://{doi}"
        else:
            full_doi = f"https://doi.org/{doi}"
    else:
        full_doi = doi
    
    logging.info(f"Full URL for query: {full_doi}")
    
    loop = asyncio.get_event_loop()
    try:
        papers = await loop.run_in_executor(executor, vectorSearch, full_doi)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching data: {e}")
    if not papers:
        raise HTTPException(status_code=404, detail=f"Paper with DOI '{doi}' not found.")
    return papers


@app.get("/titled_paper/{title}")
async def get_titled_paper(title: str):
    logging.info(f"request for titled paper with raw title: {title}")
    
    decoded_title = urllib.parse.unquote(title)
    
    logging.info(f"Decoded title for query: {decoded_title}")
    
    try:
        papers = await asyncio.get_event_loop().run_in_executor(executor, titledPaper, decoded_title)
        logging.info(f"Titled paper search completed for title: {decoded_title}")
    except Exception as e:
        logging.error(f"error occurred during search for title '{decoded_title}': {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching data: {e}")
        
    if not papers:
        logging.warning(f"No papers found for title {decoded_title}")
        return []
        
    return papers


@app.get("/test_bigquery")
async def test_bigquery():
    def test_connection():
        try:
            client = bigquery.Client()
            # Simple test query
            sql_query = "SELECT 1 as test"
            results = client.query(sql_query).result()
            return {"status": "success", "result": list(results)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, test_connection)
    return result