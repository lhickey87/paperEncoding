

import networkx as nx
import matplotlib.pyplot as plt
import model.py
from model.py import toVector, compute_similarity_score

def create_influence_flower(central_node: str, related_nodes: dict[str, int]):
    G = nx.Graph()

    G.add_node(central_node, size=2000, color='white', edgecolor='black')
    sorted_nodes = sorted(related_nodes.items(), key=lambda item: item[1], reverse=True)

    pos = {central_node: (0, 0)}  
    num_nodes = len(sorted_nodes)
    
    start_angle = np.pi * 1 # Approximately 162 degrees (left side)
    end_angle = 0 

    if num_nodes > 0:
        angles = np.linspace(start_angle, end_angle, num_nodes)
        print(angles)
        radius = 1 # Distance from the center

        for i, (key, value) in enumerate(sorted_nodes):
            x = radius * np.cos(angles[i])
            y = radius * np.sin(angles[i])
            pos[key] = (x, y)
    
    if related_nodes:
        min_val = min(related_nodes.values())
        max_val = max(related_nodes.values())
        norm = plt.Normalize(vmin=min_val, vmax=max_val)

    for key, value in sorted_nodes:
        node_size = 500 * value + 300
        G.add_node(key, size=node_size, color='gray', edgecolor='black')
        G.add_edge(central_node, key, weight=value)

    node_sizes = [G.nodes[n]['size'] for n in G.nodes]
    node_colors = [G.nodes[n].get('color', 'gray') for n in G.nodes]
    node_edge_colors = [G.nodes[n].get('edgecolor', 'black') for n in G.nodes]
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    
    plt.figure(figsize=(12, 12))
    
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors=node_edge_colors)
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif', font_weight='bold')

    for u, v, d in G.edges(data=True):
        weight = d['weight']
        edge_color = "#8A4B37" if weight > 2 else "#99B2BE" # Light red vs. light blue
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], width=weight, edge_color=edge_color, alpha=0.7)

    plt.title("Influence Flower", fontsize=20)
    plt.axis('off')
    plt.show()

    plt.title("Influence Flower", fontsize=20)
    plt.axis('off')
    plt.show()