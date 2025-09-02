import streamlit as st
from shared_modules.flowers import create_influence_flower, plot_influence_flower
import matplotlib.pyplot as plt
import requests
import networkx as nx
import os


def get_paper(doi: str, backend_url: str):
    try:
        response = requests.get(f"{backend_url}/paper_details/{doi}")
        print('We have tried')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could Not connect to backend: {e}") 
        return {} 

def doi_strip(doi_query: str):
    user_input = doi_query.strip()
    if "doi.org/" in user_input:
        # User pasted a full URL
        bare_doi = user_input.split("doi.org/")[-1]
        return bare_doi
    return user_input

def get_paper_details(paper_data: dict):
    paper = paper_data.get("paper")
    st.success("paper found!")
    st.subheader(paper.get("title", "no title found"))
    
    authors = paper.get("authors", [])
    if authors:
        st.write(f"**authors:** {', '.join(authors)}")
    
    # st.write(f"**publication year:** {paper.get('publication_year', 'n/a')}")
    
    with st.expander("view abstract"):
        st.write(paper.get("abstract", "no abstract available."))


def get_related_works(paper_data: dict):
    """displays the related works and influence flower."""
    st.divider()
    st.subheader("related works")
    
    related_works = paper_data.get("related_works", [])
    if related_works:
        titles = {}
        for count, work in enumerate(related_works):
            titles[work.get('title')] = count + 1
        
        # assuming the first author from the main paper is used for the flower
        main_authors = paper_data.get("paper").get("authors", [])
        if main_authors:
            g, pos = create_influence_flower(main_authors[0], titles)
            fig, ax = plot_influence_flower(g, pos) # assuming this returns fig, ax
            st.pyplot(fig)
        else:
            st.info("cannot generate influence flower without author information.")

        for work in related_works:
            col1, col2, col3 = st.columns([2, 3, 4])
            with col1:
                st.write(f"**created date:** {work.get('created_date')}")
            with col2:
                st.write(f"**title:** {work.get('title')}")
            with col3:
                st.write(f"**related doi:** {work.get('doi')}")
    else:
        st.info("no related works found for this paper.")

# --- logic to run only when the search button is clicked ---
if __name__ == "__main__":
    st.title("Welcome to paperRank!")
    st.markdown("this allows fellow researchers to look for papers which might be relevant to a current paper they are interested in!")

    backend_url = os.getenv("BACKEND_URL")
    st.text(f"Here is the backend url {backend_url}")
    with st.form(key='search_form'):
        doi_query = st.text_input("enter the doi of a known paper (e.g., 10.1098/rspa.1927.0118)")
        search_button = st.form_submit_button(label="search")

    # --- logic to run only when the search button is clicked ---
    if search_button:
        if not doi_query:
            st.warning("please enter a doi to search.")
        else:
            doi = doi_strip(doi_query)
            st.title(f"")
            paper_data = get_paper(doi, backend_url)

            if paper_data and paper_data.get("paper"):
                get_paper_details(paper_data)
                get_related_works(paper_data)
            else:
                st.error(f"No paper found in the database with the DOI: {doi_query} or backend error.")

    # --- Sidebar with Filters (for a future feature) ---
    st.sidebar.header("Find Similar Papers (Filters)")
    years = st.sidebar.slider("Select Publication Year Range", 1990, 2025, (2015, 2025))
    authName = st.sidebar.text_input("Author Name")

