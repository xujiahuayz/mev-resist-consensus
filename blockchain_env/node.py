import networkx as nx
import numpy as np
import random
from typing import List

random.seed(16)

class Node:
    def __init__(self, node_id: int) -> None:
        self.id: int = node_id
        self.visible_builders: List[int] = []  # List of builder IDs that this node can see

def build_network(users: List['User'], builders: List['Builder'], proposers: List['Proposer']) -> nx.Graph:
    nodes: List[Node] = users + builders + proposers
    G: nx.Graph = nx.Graph()

    # Add all nodes
    for node in nodes:
        G.add_node(node.id, node=node)

    # Generate latency edges
    for i, node_i in enumerate(nodes):
        for j, node_j in enumerate(nodes):
            if i < j:
                # Sample latency in rounds from N(2.5, 1), clip to [0.5, 5]
                latency: float = np.clip(np.random.normal(2.5, 1.0), 0.5, 5.0)
                G.add_edge(node_i.id, node_j.id, weight=latency)

    # Assign visible builders (20–80% randomly selected)
    builder_ids: List[int] = [b.id for b in builders]
    for node in nodes:
        visible_count: int = random.randint(int(0.2 * len(builder_ids)), int(0.8 * len(builder_ids)))
        node.visible_builders = random.sample(builder_ids, visible_count)

    return G
