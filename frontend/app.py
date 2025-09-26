import streamlit as st
import plotly.graph_objects as go
import os
import requests
# Set the page configuration for a wide layout
st.set_page_config(layout="wide", page_title="PaperRank")

# Initialize session state
if 'show_flower' not in st.session_state:
    st.session_state.show_flower = False
if 'selected_paper' not in st.session_state:
    st.session_state.selected_paper = None
if 'selected_doi' not in st.session_state:
    st.session_state.selected_doi = None

backend_url = os.getenv("BACKEND_URL")

def get_paper(doi: str):
    try:
        response = requests.get(f"{backend_url}/paper_details/{doi}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error retrieving paper: {e}")
        return None

def get_reccomendations(doi: str):
    try:
        response = requests.get(f"{backend_url}/vector_search/{doi}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning("No papers found with that DOI.")
            return []
        else:
            st.error(f"Error retrieving recommendations: {e}")
            return []
    

def get_titled_paper(title: str):
    try:
        response = requests.get(f"{backend_url}/titled_paper/{title}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning("No papers found matching that title.")
            return []
        else:
            st.error(f"Error searching for papers: {e}")
            return []

def doi_strip(doi_query: str):
    user_input = doi_query.strip()
    if "doi.org/" in user_input:
        # User pasted a full URL
        bare_doi = user_input.split("doi.org/")[-1]
        return bare_doi
    return user_input

# Sidebar navigation
st.sidebar.title("PaperRank")
st.sidebar.markdown("---")
page = st.sidebar.selectbox(
    "Choose a page",
    ["🔍 Find Papers", "🎯 Get Recommendations", "Author Spotlight"]
)

# Page 1: Find Papers
if page == "🔍 Find Papers":
    st.title("🔍 Find Academic Papers")
    st.markdown("Search for papers by title, author, or keywords to find their DOI")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search for papers",
            placeholder="Enter title, author name, or keywords...",
            help="Try searching for: 'deep learning mobile devices' or 'John Smith neural networks'"
        )
        
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        search_button = st.button("🔍 Search", type="primary")

    # Advanced search options
    with st.expander("🔧 Advanced Search Options"):
        col3, col4, col5 = st.columns(3)
        
        with col3:
            year_filter = st.slider("Publication Year", 2000, 2024, (2020, 2024))
            
        with col4:
            venue_filter = st.selectbox(
                "Publication Venue",
                ["All", "IEEE", "ACM", "Nature", "Science", "arXiv", "Springer"]
            )
            
        with col5:
            field_filter = st.selectbox(
                "Field of Study",
                ["All", "Computer Science", "Engineering", "Biology", "Physics", "Mathematics"]
            )
    
    # Sample search results
    if search_query and search_button:
        st.markdown("---")
        st.subheader("📚 Search Results")

        papers = get_titled_paper(search_query)
       
        # Display results with better formatting
        for paper in papers:
            with st.container():
                col_main, col_button = st.columns([0.85, 0.15])
                
                with col_main:
                    st.markdown(f"""
                    <div style="padding: 15px; border-left: 4px solid #1f77b4; margin-bottom: 10px; background-color: #f8f9fa;">
                        <h4 style="margin: 0 0 8px 0; color: #1f77b4;">{paper['title']}</h4>
                        <p style="margin: 5px 0; color: #666;"><strong>Authors:</strong> {paper['authors']}</p>
                        <p style="margin: 5px 0; font-family: monospace; font-size: 0.9em; color: #333;"><strong>DOI:</strong> {paper['doi']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_button:
                    st.markdown("<br><br>", unsafe_allow_html=True)  # Spacing
                    if st.button("Use This Paper", key=f"select_{paper['doi']}", type="secondary"):
                        st.session_state.selected_doi = paper['doi']
                        st.success(f"Selected: {paper['title']}")
                        st.info("💡 Now go to 'Get Recommendations' to find related papers!")

# Page 2: Get Recommendations
elif page == "🎯 Get Recommendations":
    st.title("🎯 Get Paper Recommendations")
    
    # Check if DOI was selected from previous page
    if st.session_state.selected_doi:
        st.success(f"✅ Using selected paper with DOI: {st.session_state.selected_doi}")
        default_doi = st.session_state.selected_doi
    else:
        default_doi = "10.1109/TNNLS.2023.3340570"
    
    st.markdown("Enter a paper's DOI to find related research papers")
    
    # DOI input
    col1, col2, col3 = st.columns([0.5, 0.3, 0.2])
    
    with col1:
        doi_input = st.text_input(
            "Paper DOI",
            help="Enter the DOI of the paper you want to find recommendations for"
        )
        if doi_input:
            doi = doi_strip(doi_input)
            paper_data = get_paper(doi)
            if not paper_data:
                st.error(f"No paper found in the database with the DOI: {doi_input} or backend error.")
        else:
            st.error(f"Please enter a doi")
    
    with col2:
        search_button = st.button("🔍 Find Recommendations", type="primary")
    
    with col3:
        if st.button("Clear Selection"):
            st.session_state.selected_doi = None
            st.rerun()
    
    # Filters section
    with st.expander("🎛️ Recommendation Filters"):
        col4, col5, col6 = st.columns(3)
        
        with col4:
            year_range = st.slider("Publication Year Range", 1950, 2025, (2020, 2025))
            similarity_threshold = st.slider("Minimum Similarity", 0.0, 1.0, 0.7, 0.05)
        
        with col5:
            field_filter = st.selectbox("Field of Study", ["All", "Computer Science", "Engineering", "Biology", "Physics"])
            paper_type = st.multiselect("Paper Type", ["Journal", "Conference", "Preprint"], default=["Journal", "Conference"])
        
        with col6:
            max_results = st.number_input("Max Results", min_value=5, max_value=50, value=10)
            keywords = st.text_input("Additional Keywords", placeholder="Optional: neural networks, mobile...")
    
    # Show recommendations
    if search_button:
        st.markdown("---")
        st.subheader("📋 Related Papers")

        recommendations = get_reccomendations(paper_data['doi']) #this will return a list of papers by similarity score 
        
        for paper in recommendations:
            with st.container():
                col_content, col_actions = st.columns([0.8, 0.2])
                
                with col_content:
                    # Color code similarity score
                    similarity_score = 1 - paper['distance']  # Convert distance to similarity

                    if similarity_score >= 0.9:
                        score_color = "#28a745"  # Green
                    elif similarity_score >= 0.8:
                        score_color = "#ffc107"  # Yellow  
                    else:
                        score_color = "#fd7e14"  # Orange 
                                        
                    st.markdown(f"""
                    <div style="padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; margin-bottom: 15px; background-color: white;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: #495057; flex: 1;">{paper['title']}</h4>
                            <span style="font-weight: bold; font-size: 1.4em; color: {score_color}; margin-left: 15px;">
                                {int(paper['distance'] * 100)}%
                            </span>
                        </div>
                        <p style="margin: 8px 0; color: #6c757d;"><strong>Authors:</strong> {paper['authors']}</p>
                        <p style="margin: 8px 0; font-family: monospace; font-size: 0.9em; color: #495057;"><strong>DOI:</strong> {paper['doi']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                col_actions = st.columns([1, 1, 3]) 
                with col_actions:
                    with col_actions[0]:
                        if st.button("🌸 View Network", key=f"network_{paper.get('doi', '')}", help="View citation network"):
                            st.session_state.show_flower = True
                            st.session_state.selected_paper = paper
                    with col_actions[1]:
                        st.link_button("🔗 Open Paper", url=paper.get('oa_url', '#'), help="Open paper link in a new tab")
        
        # Show influence network if requested
        if st.session_state.show_flower and st.session_state.selected_paper is not None:
            st.markdown("---")
            with st.container():
                # display_influence_flower(st.session_state.selected_paper)
                
                col_close, _, _ = st.columns([0.2, 0.4, 0.4])
                with col_close:
                    if st.button("✖️ Close Network"):
                        st.session_state.show_flower = False
                        st.rerun()

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 How to Use")
st.sidebar.markdown("""
1. **Find Papers**: Search for papers by title, author, or keywords
2. **Get DOI**: Select a paper from search results
3. **Get Recommendations**: Use the DOI to find related papers
4. **Explore Networks**: View citation relationships
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Stats")
st.sidebar.metric("Papers Indexed", "19.8M")