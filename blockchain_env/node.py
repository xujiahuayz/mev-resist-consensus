import networkx as nx
import numpy as np
import random

random.seed(16)

class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.visible_builders = []

def build_network(users, builders, proposers):
    nodes = users + builders + proposers
    G = nx.Graph()

    # Add all nodes
    for node in nodes:
        G.add_node(node.id, node=node)

    # Generate latency edges
    for i, node_i in enumerate(nodes):
        for j, node_j in enumerate(nodes):
            if i < j:
                # Sample latency in rounds from N(2.5, 1), clip to [0.5, 5]
                latency = np.clip(np.random.normal(2.5, 1.0), 0.5, 5.0)
                G.add_edge(node_i.id, node_j.id, weight=latency)

    # Assign visible builders (20–80% randomly selected)
    builder_ids = [b.id for b in builders]
    for node in nodes:
        visible_count = random.randint(int(0.2 * len(builder_ids)), int(0.8 * len(builder_ids)))
        node.visible_builders = random.sample(builder_ids, visible_count)

    return G
