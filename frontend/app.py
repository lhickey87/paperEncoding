import streamlit as st
from db.connection import returnPaper
from shared_modules.flowers import create_influence_flower
import matplotlib.pyplot as plt
import requests
import networkx as nx
import os

st.title("Math Paper Encoder!")
st.markdown("This allows fellow researchers to look for papers which might be relevant to a current paper they are interested in!")

# --- Configuration ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
# --- Main Search Input --

with st.form(key='search_form'):
    doi_query = st.text_input("Enter the DOI of a known Paper (e.g., 10.1098/rspa.1927.0118)")
    search_button = st.form_submit_button(label="Search")

# --- Logic to run ONLY when the search button is clicked ---
if search_button:
    if not doi_query:
        st.warning("Please enter a DOI to search.")
    else:
        # FIX: Handle both full URL and bare DOI inputs from the user
        user_input = doi_query.strip()
      
        if "doi.org/" in user_input:
            # User pasted a full URL
            full_doi_url = user_input
            bare_doi = user_input.split("doi.org/")[-1]
        else:
            # User pasted just the DOI
            bare_doi = user_input
            full_doi_url = f"https://doi.org/{bare_doi}"
        
        # Query the database using the full URL
        with st.spinner("Searching for paper..."):
            paper = returnPaper({"url": full_doi_url})

        # --- Display the results ---
        if paper:
            st.success("Paper Found!")
            st.subheader(paper.get("title", "No Title Found"))
            
            authors = paper.get("authors", [])
            if authors:
                st.write(f"**Authors:** {', '.join(authors)}")
            
            st.write(f"**Publication Year:** {paper.get('publication_year', 'N/A')}")
            
            with st.expander("View Abstract"):
                st.write(paper.get("abstract", "No abstract available."))

            st.divider()
            st.subheader("Related Works")

            # Call the backend API to get related works using the bare DOI
            try:
                response = requests.get(f"{BACKEND_URL}/paper_details/{bare_doi}")
                print('We have tried')
                response.raise_for_status()
                data = response.json()
                
            
                related_works = data.get("related_works", [])

                titles = {}
                count = 0
                for work in related_works:
                    titles[work.get('title')] = count +1
                    count += 1
                
                [G,pos] = create_influence_flower(authors[0],titles)

                node_sizes = [G.nodes[n]['size'] for n in G.nodes]
                node_colors = [G.nodes[n].get('color', 'gray') for n in G.nodes]
                node_edge_colors = [G.nodes[n].get('edgecolor', 'black') for n in G.nodes]

                fig, ax = plt.subplots(figsize=(12, 12))

                nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors=node_edge_colors, ax=ax)
                nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif', font_weight='bold', ax=ax)
                for u, v, d in G.edges(data=True):
                    weight = d['weight']
                    # Use hexadecimal color codes for edge_color
                    edge_color = "#CD5C5C" if weight > 2 else "#A9CCE3" # Light red (IndianRed) vs. light blue (LightSteelBlue)
                    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=weight, edge_color=edge_color, alpha=0.7, ax=ax)

                ax.set_facecolor("#F0F2F6") # Light background for the plot area
                ax.set_xticks([])
                ax.set_yticks([])
                plt.tight_layout() 

                st.pyplot(fig)
                if related_works:
                    for work in related_works:
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            st.write(f"**Related Title:** {work.get('title')}")
                        with col2:
                            st.write(f"**Related DOI:** {work.get('doi')}")
                else:
                    st.info("No related works found for this paper.")

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend. Is it running? Error: {e}")

        else:
            st.error(f"No paper found in the database with the DOI: {doi_query}")

# --- Sidebar with Filters (for a future feature) ---
st.sidebar.header("Find Similar Papers (Filters)")
years = st.sidebar.slider("Select Publication Year Range", 1990, 2025, (2015, 2025))
authName = st.sidebar.text_input("Author Name")
# ... (rest of your filter code)
