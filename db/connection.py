import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import time
import certifi

load_dotenv()
# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "research_db"
COLLECTION_NAME = "papers"
API_BASE_URL = "https://api.openalex.org/works"

if MONGO_URI is None:
    print("Error: MONGO_URI not found. Make sure you have a .env file with your connection string.")
    # Exit or handle the error gracefully
    exit()

# --- Database Connection (Singleton Pattern) ---
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("Successfully connected to MongoDB Atlas.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None
    collection = None

def reconstructAbstract(inverted_index: dict):
    # when paper has no abstract
    if not inverted_index:
        return ""
    try:
        # Find the total number of words in the abstract
        max_index = max(pos for positions in inverted_index.values() for pos in positions)
        word_list = [""] * (max_index + 1)
        
        for word, positions in inverted_index.items():
            for pos in positions:
                word_list[pos] = word
                
        return " ".join(word_list)
    except (ValueError, IndexError):
        return "" # Return empty string if inverted_index is malformed

def fetchPapers(collection, numPages=10):
    """Fetches and stores papers from the OpenAlex API."""
    params = {
        'per_page': 10,
        'filter': 'primary_topic.field.id:26' # Mathematics
    }
    
    for page in range(1, numPages + 1):
        params['page'] = page
        
        try:
            response = requests.get(API_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            papers = data.get('results', [])
            
            if not papers:
                print("No more papers found. Stopping.")
                break

            # FIX 3: Clear the list for each new page of results
            papersToInsert = []
            for paper in papers:
                simplifiedPaper = {
                    "id": paper.get("id"), 
                    "title": paper.get("title"), 
                    "publication_year": paper.get("publication_year"), 
                    "publication_date": paper.get("publication_date"),
                    "authors": [author['author'].get('display_name') for author in paper.get('authorships', []) if author.get('author')],
                    "abstract": reconstructAbstract(paper.get("abstract_inverted_index")),
                    "url": paper.get("doi"),
                    "referenced_works": paper.get("referenced_works"),
                    "related_works": paper.get("related_works")
                }
                
                
                if collection.find_one({"id": paper.get("id")}):
                    continue 

                papersToInsert.append(simplifiedPaper)
             
            if papersToInsert:
                collection.insert_many(papersToInsert, ordered=False)
                # FIX 4: Corrected print formatting
                print(f"Page {page}: Inserting {len(papersToInsert)} Papers")
            
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"An API error occurred on page {page}: {e}")
            continue
        except Exception as e:
            if "duplicate key" not in str(e):
                print(f"A database error occurred: {e}")

def returnPaper(query_filter: dict):
    """Finds a single paper in the database."""
    if collection is None:
        return None
    try:
        paper = collection.find_one(query_filter)
        print('entered find_one operation')
        return paper
    except Exception as e:
        print(f"An error occurred during find_one: {e}")
        return None

if __name__ == "__main__":
    if collection:
        # FIX 5: Corrected syntax for function call
        fetchPapers(collection, numPages=100)
        