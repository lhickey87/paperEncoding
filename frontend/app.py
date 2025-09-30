import streamlit as st
import requests
import os
import re

st.set_page_config(
    page_title="PaperRank",
    page_icon="📚",
    layout="wide"
)

# Backend URL
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'similar_papers' not in st.session_state:
    st.session_state.similar_papers = []
if 'viewing_similar_for' not in st.session_state:
    st.session_state.viewing_similar_for = None

def get_paper(doi: str):
    try:
        response = requests.get(f"{backend_url}/paper_details/{doi}")
        response.raise_for_status()
        return response.json()
    except:
        return None

def get_recommendations(doi: str):
    try:
        response = requests.get(f"{backend_url}/vector_search/{doi}")
        response.raise_for_status()
        return response.json()
    except:
        return []

def get_titled_paper(title: str):
    try:
        response = requests.get(f"{backend_url}/titled_paper/{title}")
        response.raise_for_status()
        return response.json()
    except:
        return []

def detect_search_type(query):
    doi_pattern = r'10\.\d{4,9}/[-._;()/:\w]+'
    if re.search(doi_pattern, query) or 'doi.org' in query.lower():
        return 'doi'
    
    words = query.split()
    if len(words) <= 3 and len(words) >= 2:

        if all(word[0].isupper() for word in words if len(word) > 1):
            return 'author_likely'
        
        if ',' in query and len(words) == 2:
            return 'author_likely'
    
    return 'general'

def doi_strip(doi_query: str):
    user_input = doi_query.strip()
    if "doi.org/" in user_input:
        return user_input.split("doi.org/")[-1]
    return user_input

def format_authors(authors):
    if isinstance(authors, list):
        if len(authors) > 3:
            return f"{', '.join(authors[:3])}, et al."
        return ', '.join(authors)
    return authors

def perform_search(query):
    if not query:
        return [], None
    
    search_type = detect_search_type(query)
    
    if search_type == 'doi':
        paper = get_paper(query)
        return [paper] if paper else [], 'doi'
    else:
        # For both author and general searches, use the same endpoint
        # Your backend should handle searching across all fields
        results = get_titled_paper(query)
        return results, search_type

st.title("PaperRank")
st.markdown("Find research papers and discover similar work through the power of sentence embeddings and vector search!")

search_query = st.text_input(
    "",
    placeholder='Search by paper title, author name, keywords, or DOI (e.g., "attention mechanism" or "Yoshua Bengio")',
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    search_button = st.button("Search", type="primary", use_container_width=True)

if search_button and search_query:
    with st.spinner("Searching..."):
        results, search_type = perform_search(search_query)
        st.session_state.search_results = results
        st.session_state.viewing_similar_for = None  # Reset similar papers view
    
    # Provide feedback about search type
    if search_type == 'doi':
        if results:
            st.success(f"Found paper with DOI: {search_query}")
        else:
            st.error("No paper found with this DOI. Please check the DOI and try again.")
    elif search_type == 'author_likely':
        if results:
            st.success(f"Found {len(results)} papers for author: {search_query}")
        else:
            st.warning(f"No papers found for '{search_query}'. Try the full name or different spelling.")
    else:
        if results:
            st.success(f"Found {len(results)} papers matching: {search_query}")
        else:
            st.warning("No papers found. Try different keywords or check spelling.")

if st.session_state.viewing_similar_for:
    st.markdown("---")
    
    st.info(f"**Finding papers similar to:** {st.session_state.viewing_similar_for['title']}")
    
    if st.button("← Back to Search Results"):
        st.session_state.viewing_similar_for = None
        st.rerun()
    
    with st.spinner("Finding similar papers..."):
        similar = get_recommendations(st.session_state.viewing_similar_for.get('doi', ''))
        st.session_state.similar_papers = similar
    
    if similar:
        st.success(f"Found {len(similar)} similar papers")
        
        col1, col2 = st.columns([4, 1])
        with col2:
            sort_by = st.selectbox("Sort by", ["Relevance", "Year", "Citations"], label_visibility="collapsed")
        
        st.markdown("### Similar Papers")
        
        for idx, paper in enumerate(similar[:20]):  
            similarity = 1 - paper.get('distance', 0.5)
            percent = int(similarity * 100)
            with st.container(border=True):
                if percent >= 90:
                    st.success(f"**{percent}% Match**")
                elif percent >= 80:
                    st.warning(f"**{percent}% Match**")
                else:
                    st.info(f"**{percent}% Match**")
                
                # Paper details
                st.markdown(f"#### {paper.get('title', 'Untitled')}")
                st.caption(format_authors(paper.get('authors', 'Unknown')))
                
                if 'year' in paper:
                    st.caption(f"Published: {paper['year']}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("View", key=f"view_sim_{idx}", use_container_width=True):
                        with st.expander("Paper Details", expanded=True):
                            st.write(f"**DOI:** {paper.get('doi', 'Not available')}")
                            if 'abstract' in paper:
                                st.write(f"**Abstract:** {paper['abstract']}")
                
                with col_b:
                    if st.button("Find Similar", key=f"similar_sim_{idx}", type="primary", use_container_width=True):
                        st.session_state.viewing_similar_for = paper
                        st.rerun()
    else:
        st.warning("No similar papers found. This might be a very unique paper.")

elif st.session_state.search_results:
    # SEARCH RESULTS VIEW
    st.markdown("---")
    
    # Results header with count
    st.markdown(f"### Search Results ({len(st.session_state.search_results)} papers)")
    
    # Sort/filter options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        sort_by = st.selectbox("Sort by", ["Relevance", "Year", "Citations"], label_visibility="collapsed")
    with col3:
        if st.button("Clear Results"):
            st.session_state.search_results = []
            st.rerun()
    
    
    for idx, paper in enumerate(st.session_state.search_results[:20]):  # Limit to 20
        with st.container(border=True):
            # Paper title
            st.markdown(f"#### {paper.get('title', 'Untitled')}")
            
            # Authors
            st.caption(format_authors(paper.get('authors', 'Unknown')))
            
            metadata = []
            if 'year' in paper:
                metadata.append(f"{paper['year']}")
            if 'citations' in paper:
                metadata.append(f"{paper['citations']:,} citations")
            if 'field' in paper:
                metadata.append(paper['field'])
            
            if metadata:
                st.caption(" • ".join(metadata))
            
            # Action buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("View Details", key=f"view_{idx}", use_container_width=True):
                    with st.expander("Paper Details", expanded=True):
                        st.write(f"**DOI:** {paper.get('doi', 'Not available')}")
                        if 'abstract' in paper:
                            st.write(f"**Abstract:** {paper.get('abstract', 'Not available')}")
                        if 'url' in paper:
                            st.write(f"**URL:** {paper['url']}")
                        if 'year' in paper:
                            st.write(f"**Year:** {paper['year']}")
            
            with col_b:
                if st.button("Find Similar", key=f"similar_{idx}", type="primary", use_container_width=True):
                    st.session_state.viewing_similar_for = paper
                    st.rerun()
    
    if len(st.session_state.search_results) > 20:
        st.markdown("---")
        if st.button("Load More Results", use_container_width=True):
            st.info("Showing first 20 results. Pagination coming soon!")

else:
    st.markdown("---")
    
    # Help section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 How to Search")
        st.markdown("""
        **You can search by:**
        - **Keywords:** machine learning, climate change
        - **Paper title:** "Attention Is All You Need"
        - **Author name:** Yoshua Bengio, Hinton
        - **DOI:** 10.1038/nature14539
        
        Our AI will automatically detect what you're searching for!
        """)
    
    with col2:
        st.markdown("### 📊 How It Works")
        st.markdown("""
        1. **Search** for any paper or topic
        2. **Find Similar** to discover related research
        3. **Explore** recursively through similar papers
        4. **Build** your research knowledge graph
        
        Powered by semantic similarity using vector embeddings.
        """)
    
    # Stats to build trust
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Papers Indexed", "19.8M")
    with col2:
        st.metric("Research Fields", "127")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - **email**: <hickey.liams@gmail.com>
        - **github**: https://github.com/lhickey87""", unsafe_allow_html = True)
    with col2:
        st.markdown("""Please feel free to reach out!""")
        
with st.sidebar:
    st.markdown("### About PaperRank")
    
    st.markdown("---")
    
    # Advanced search in sidebar (optional)
    with st.expander("Advanced Search"):
        adv_title = st.text_input("Title contains")
        adv_author = st.text_input("Author name")
        adv_year_from = st.number_input("Year from", 1900, 2024, 2020)
        adv_year_to = st.number_input("Year to", 1900, 2024, 2024)
        
        if st.button("Advanced Search"):
            st.info("Advanced search coming soon!")