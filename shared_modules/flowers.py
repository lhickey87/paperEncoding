

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


# def embed(input):
#   return model(input)

# def toVector(vec):
#    return vec.numpy().tolist()

# def compute_similarity_score(vec1: list, vec2: list):
#     total = 0
#     for i in range(0,512):
#        total += vec1[i]*vec2[i] 
#     return total 


