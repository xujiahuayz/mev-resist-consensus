import networkx as nx
import numpy as np
import random
import matplotlib.pyplot as plt
from typing import List, Any, Type
from dataclasses import dataclass

random.seed(16)

@dataclass
class Message:
    sender_id: int
    receiver_id: int
    content: Any
    round: int

class Node:
    def __init__(self, node_id: int) -> None:
        self.id: int = node_id
        self.visible_nodes: List[int] = []  # List of node IDs that this node can see
        self.message_queue: List[Message] = []  # Queue of messages to process
        self.network: nx.Graph = None  # Reference to the network graph

    def set_network(self, network: nx.Graph) -> None:
        self.network = network
        # Update visible nodes based on network connections
        self.visible_nodes = list(network.neighbors(self.id))

    def send_message(self, receiver_id: int, content: Any, current_round: int) -> None:
        """Send a message to another node through the network"""
        if receiver_id in self.visible_nodes:
            message = Message(
                sender_id=self.id,
                receiver_id=receiver_id,
                content=content,
                round=current_round    
            )
            # Add message to receiver's queue
            receiver = self.network.nodes[receiver_id]['node']
            if receiver:
                receiver.message_queue.append(message)

    def receive_messages(self) -> List[Message]:
        """Get all messages from the queue"""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages

def build_network(users: List[Node], builders: List[Node], proposers: List[Node]) -> nx.Graph:
    nodes: List[Node] = users + builders + proposers
    G: nx.Graph = nx.Graph()

    # Add all nodes
    for node in nodes:
        G.add_node(node.id, node=node)

    # Generate latency edges
    for i, node_i in enumerate(nodes):
        for j, node_j in enumerate(nodes):
            if i < j:
                # Sample latency in rounds from N(1.0, 1.0), clip to [0.1, 3.0]
                latency: float = np.clip(np.random.normal(1.0, 1.0), 0.1, 3.0)
                G.add_edge(node_i.id, node_j.id, weight=latency)

    # Set network reference for all nodes
    for node in nodes:
        node.set_network(G)

    return G

def visualize_network(network: nx.Graph) -> None:
    """Visualize the network structure with different node types."""
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(network)
    
    # Get node types
    users = [n for n in network.nodes() if 'user' in str(n)]
    builders = [n for n in network.nodes() if 'builder' in str(n)]
    proposers = [n for n in network.nodes() if 'proposer' in str(n)]
    
    # Draw nodes
    nx.draw_networkx_nodes(network, pos, nodelist=users, node_color='lightblue', node_size=500, label='Users')
    nx.draw_networkx_nodes(network, pos, nodelist=builders, node_color='lightgreen', node_size=500, label='Builders')
    nx.draw_networkx_nodes(network, pos, nodelist=proposers, node_color='pink', node_size=500, label='Proposers')
    
    # Draw edges with width based on latency
    edge_widths = [1/network[u][v]['weight'] for u,v in network.edges()]
    nx.draw_networkx_edges(network, pos, width=edge_widths, alpha=0.5)
    
    # Add labels and legend
    nx.draw_networkx_labels(network, pos)
    plt.title("Network Visualization with Latency-Based Edge Widths")
    plt.legend()
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    # Create test nodes
    class TestNode(Node):
        def __init__(self, node_id: str) -> None:
            super().__init__(node_id)
    
    # Create sample nodes for testing
    users = [TestNode(f"user_{i}") for i in range(5)]
    builders = [TestNode(f"builder_{i}") for i in range(3)]
    proposers = [TestNode(f"proposer_{i}") for i in range(2)]
    
    # Build and visualize network
    G = build_network(users, builders, proposers)
    visualize_network(G)
    
    # Print network statistics
    print("\nNetwork Statistics:")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print("\nNode connections:")
    for node in G.nodes():
        print(f"{node} is connected to: {list(G.neighbors(node))}")
    print("\nEdge latencies:")
    for u, v, data in G.edges(data=True):
        print(f"{u} <-> {v}: {data['weight']:.2f} rounds")