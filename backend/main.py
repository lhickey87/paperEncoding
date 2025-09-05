# Save this code as 'main.py' in your project directory

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db.query import doiEntered
# from db.connection import returnPaper  # Your function to query MongoDB
import httpx  # A modern, async-friendly requests library
import asyncio
import certifi

# Create a FastAPI app instance
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

@app.get("/paper_details/{doi:path}")
async def get_paper_details(doi: str):
    # 1. Find the main paper in your local MongoDB
    # full_doi_url = f"https://doi.org/{doi}"
    main_paper = doiEntered(doi)
    # This needs doiEntered as well
    if not main_paper:
        raise HTTPException(status_code=404, detail="Paper not found in the database.")
    
    print('ented app.get method from streamlit app')
    paper = {
        "id": main_paper.get("id"),
        "title": main_paper.get("title"),
        "author_ids": main_paper.get('author_ids'),
        "referenced_works": main_paper.get('referenced_works'),
        "oa_url": main_paper.get('oa_url'),
        "oa_status":main_paper.get('oa_status'),
        "cited_by_count":main_paper.get("cited_by_count"),
        "created_date": main_paper.get("created_date"),
        "authors": main_paper.get("authors", []),
        "abstract": main_paper.get("abstract", ""),
        "related_works": main_paper.get("related_works", [])
    }
    print(paper['title'])
    # 2. Asynchronously fetch details for all related works
    related_works_urls = paper.get('related_works', [])
    related_works_details = []

    async with httpx.AsyncClient(verify=certifi.where()) as client:
        # Create a list of tasks to run concurrently
        tasks = []
        for work_url in related_works_urls[:10]: # Limit to 10 for speed
            api_url = work_url.replace("openalex.org/", "api.openalex.org/works/")
            tasks.append(client.get(api_url))
        
        # Run all tasks at the same time and wait for them to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        print("inside paper retrieval method")
        # Process the results
        for response in responses:
            if isinstance(response, httpx.Response) and response.status_code == 200:
                work_data = response.json()
                if work_data.get('doi'):
                    print(work_data.get('doi'))
                    related_works_details.append({
                        "title": work_data.get('title', 'Title not found'),
                        "doi": work_data.get('doi', 'DOI not found'),
                        'publication_year': work_data.get('publication_year')
                    })

    # 3. Combine and return all the data
    return {
        "paper": paper, 
        "related_works": related_works_details
    }

# @app.get("/flower_details/{doi:path}")