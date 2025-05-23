import networkx as nx
import numpy as np
import random
import matplotlib.pyplot as plt
from typing import List, Any, Type
from dataclasses import dataclass

random.seed(16)
np.random.seed(16)

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
        self.mempool: List[Any] = []  # Store transactions for all node types

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
                # Calculate delivery round based on latency (using float)
                latency = self.network[self.id][receiver_id]['weight']
                delivery_round = current_round + latency
                message.round = delivery_round
                receiver.message_queue.append(message)

    def receive_messages(self) -> List[Message]:
        """Get all messages from the queue and process them"""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        
        # Process each message
        for message in messages:
            # If it's a transaction, propagate it and add to mempool
            if hasattr(message.content, 'creator_id'):  # Check if it's a Transaction
                # Add to mempool first to avoid duplicates
                if message.content not in self.mempool:
                    self.mempool.append(message.content)
                    # Then propagate to neighbors
                    self.propagate_transaction(message.content, message.round, message.sender_id)
            # If it's a bid amount (float), just pass it through
            elif isinstance(message.content, (int, float)):
                pass  # Don't add to mempool, just pass through
        
        return messages

    def propagate_transaction(self, transaction: Any, current_round: int, sender_id: int, seen: set = None) -> None:
        """Propagate a transaction to all neighbors except the sender"""
        # Initialize seen set if not provided
        if seen is None:
            seen = set()
        
        # Add transaction to seen set to prevent loops
        if transaction in seen:
            return
        seen.add(transaction)
        
        # Forward to all neighbors except sender
        for neighbor_id in self.visible_nodes:
            if neighbor_id != sender_id:
                # Calculate delivery round based on latency
                latency = self.network[self.id][neighbor_id]['weight']
                delivery_round = current_round + latency
                self.send_message(neighbor_id, transaction, delivery_round)

    def get_mempool(self) -> List[Any]:
        """Get all transactions in the node's mempool"""
        return self.mempool.copy()

    def clear_mempool(self, block_num: int) -> None:
        """Clear transactions that have been included in blocks or are too old"""
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at >= block_num - 5]

    def get_visible_transactions(self) -> List[Any]:
        """Get all transactions that have propagated to this node"""
        transactions = []
        messages = self.receive_messages()
        for msg in messages:
            if hasattr(msg.content, 'creator_id'):  # If it's a transaction
                transactions.append(msg.content)
        return transactions

def build_network(users: List[Node], builders: List[Node], proposers: List[Node], p=0.05) -> nx.Graph:
    nodes: List[Node] = users + builders + proposers
    N = len(nodes)
    # Step 1: Create the graph with integer labels
    G = nx.erdos_renyi_graph(N, p, seed=16)
    # Step 2: Relabel nodes to use your string IDs
    mapping = {i: nodes[i].id for i in range(N)}
    G = nx.relabel_nodes(G, mapping)
    # Step 3: Add node objects as attributes
    for node in nodes:
        G.nodes[node.id]['node'] = node
    # Step 4: Add edges with random latency as weight
    for u, v in G.edges():
        latency = float(np.clip(np.random.normal(1.0, 1.0), 0.1, 3.0))
        G[u][v]['weight'] = latency
    # Step 5: Set network reference for all nodes
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
    users = [TestNode(f"user_{i}") for i in range(50)]
    builders = [TestNode(f"builder_{i}") for i in range(20)]
    proposers = [TestNode(f"proposer_{i}") for i in range(20)]
    
    # Build and visualize network with p=0.05
    G = build_network(users, builders, proposers, p=0.05)
    
    # Print network statistics
    print("\nNetwork Statistics:")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print("\nDegree distribution:")
    degrees = [G.degree(node) for node in G.nodes()]
    print(f"Average degree: {sum(degrees)/len(degrees):.2f}")
    print(f"Minimum degree: {min(degrees)}")
    print(f"Maximum degree: {max(degrees)}")
    print("\nSample node degrees:")
    for node in list(G.nodes())[:10]:  # Show first 10 nodes
        print(f"{node}: degree {G.degree(node)}")