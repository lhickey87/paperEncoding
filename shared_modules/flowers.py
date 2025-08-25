

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
# import model.py
# from model.py import toVector, compute_similarity_score

def create_influence_flower(central_node: str, related_nodes: dict[str, int]):
    G = nx.Graph()

    # Add the central node with a base size and color
    G.add_node(central_node, size=2000, color='white', edgecolor='black')

    sorted_nodes = sorted(related_nodes.items(), key=lambda item: item[1], reverse=True)
    pos = {central_node: (0, 0)}
    num_nodes = len(sorted_nodes)
    start_angle = np.pi
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
        G.add_node(key, size=node_size, color= 'gray', edgecolor='black')
        G.add_edge(central_node, key, weight=value)


    return [G,pos]

def plot_influence_flower(G, pos:list[int]):
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
    return [fig,ax]


# def embed(input):
#   return model(input)

# def toVector(vec):
#    return vec.numpy().tolist()

# def compute_similarity_score(vec1: list, vec2: list):
#     total = 0
#     for i in range(0,512):
#        total += vec1[i]*vec2[i] 
#     return total 


