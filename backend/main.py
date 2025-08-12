# Save this code as 'main.py' in your project directory

from fastapi import FastAPI, HTTPException
from db.connection import returnPaper  # Your function to query MongoDB
import httpx  # A modern, async-friendly requests library
import asyncio
import certifi

# Create a FastAPI app instance
app = FastAPI()

@app.get("/paper_details/{doi:path}")
async def get_paper_details(doi: str):
    # 1. Find the main paper in your local MongoDB
    full_doi_url = f"https://doi.org/{doi}"
    main_paper = returnPaper({'url': full_doi_url})
    if not main_paper:
        raise HTTPException(status_code=404, detail="Paper not found in the database.")
    
    print('ented app.get method from streamlit app')
    paper = {
        "id": main_paper.get("id"),
        "title": main_paper.get("title"),
        "publication_year": main_paper.get("publication_year"),
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
                        "doi": work_data.get('doi', 'DOI not found')
                    })

    # 3. Combine and return all the data
    return {
        "related_works": related_works_details
    }
