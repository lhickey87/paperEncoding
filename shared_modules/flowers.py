

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
# import model.py
# from model.py import toVector, compute_similarity_score

def display_influence_flower(paper_details):
    st.subheader(f"Influence Network for: {paper_details['Title']}")

    # Create mock data for the graph
    nodes_data = [
        {'id': 0, 'name': paper_details['Title'], 'label': 'Current Paper', 'group': 'core'},
    ]
    edges_data = []

    # Add mock papers
    mock_papers = [
        {'id': 1, 'name': 'Energy-Efficient Inference for CNNs', 'label': 'Citing Paper', 'group': 'citing'},
        {'id': 2, 'name': 'Hardware Accelerators for Deep Learning', 'label': 'Citing Paper', 'group': 'citing'},
        {'id': 3, 'name': 'Efficient Neural Network Architectures', 'label': 'Cited Paper', 'group': 'cited'},
        {'id': 4, 'name': 'Survey of IoT and Machine Learning', 'label': 'Cited Paper', 'group': 'cited'},
    ]
    nodes_data.extend(mock_papers)

    for mock_paper in mock_papers:
        edges_data.append({'source': 0, 'target': mock_paper['id']})

    # Prepare data for Plotly
    node_x = [0, 1, -1, 0.5, -0.5]
    node_y = [0, 1, 1, -1, -1]
    
    edge_x = []
    edge_y = []
    for edge in edges_data:
        x0, y0 = node_x[edge['source']], node_y[edge['source']]
        x1, y1 = node_x[edge['target']], node_y[edge['target']]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    # Create the figure
    fig = go.Figure()

    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none'
    ))

    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        name='Papers',
        marker=dict(
            symbol='circle',
            size=[25, 15, 15, 15, 15],
            color=['rgba(175, 55, 202, 0.8)', 'rgba(55, 175, 202, 0.8)', 'rgba(55, 175, 202, 0.8)', 'rgba(255, 140, 0, 0.8)', 'rgba(255, 140, 0, 0.8)']
        ),
        text=[node['name'] for node in nodes_data],
        textposition='top center',
        textfont=dict(size=10),
        hovertemplate='<b>%{text}</b><br><i>%{customdata}</i><extra></extra>',
        customdata=[node['label'] for node in nodes_data]
    ))
    
    # Configure the plot layout
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    st.plotly_chart(fig, use_container_width=True)

# Sidebar navigation
st.sidebar.title("PaperRank")
st.sidebar.markdown("---")
page = st.sidebar.selectbox(
    "Choose a page",
    ["🔍 Find Papers", "🎯 Get Recommendations", "Author Spotlight"]
)