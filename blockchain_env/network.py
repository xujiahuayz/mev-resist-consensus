"""Network module for blockchain environment."""

import random
import math
from typing import List, Any
from dataclasses import dataclass
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

random.seed(16)
np.random.seed(16)

@dataclass
class Message:
    """Message class for network communication."""
    sender_id: int
    receiver_id: int
    content: Any
    round: int

class Node:
    """Node class representing a participant in the network."""
    def __init__(self, node_id: int, restaking_factor: float = None) -> None:
        """Initialize a Node."""
        self.id: int = node_id
        self.visible_nodes: List[int] = []
        self.message_queue: List[Message] = []
        self.network: nx.Graph = None
        self.mempool: List[Any] = []
        
        # Restaking functionality
        if restaking_factor is None:
            # Default restaking factor: 50% chance of restaking
            self.restaking_factor: float = random.random() < 0.5
        else:
            self.restaking_factor: float = restaking_factor
        
        # Restaking state
        self.capital: int = 0  # Total accumulated capital
        self.active_stake: int = 0  # Active stake (only full validator units)
        self.profit_history: List[int] = []  # Track profits over time
        self.stake_history: List[int] = []  # Track stake evolution

    def set_network(self, network: nx.Graph) -> None:
        """Set the network graph and update visible nodes."""
        self.network = network
        self.visible_nodes = list(network.neighbors(self.id))

    def send_message(self, receiver_id: int, content: Any, current_round: int) -> None:
        """Send a message to another node through the network."""
        if receiver_id in self.visible_nodes:
            message = Message(
                sender_id=self.id,
                receiver_id=receiver_id,
                content=content,
                round=current_round
            )
            receiver = self.network.nodes[receiver_id]['node']
            if receiver:
                latency = self.network[self.id][receiver_id]['weight']
                # For direct neighbors, transactions arrive in the same block (round 0 delay)
                # For multi-hop propagation, add latency
                # This ensures transactions are available to builders quickly
                if latency <= 1.0:
                    # Fast connection: available in same block
                    delivery_round = current_round
                else:
                    # Slower connection: available in next block
                    delivery_round = current_round + 1
                message.round = delivery_round
                receiver.message_queue.append(message)

    def receive_messages(self, current_round: int = None) -> List[Message]:
        """Get and process all messages from the queue that should be delivered at current_round."""
        if current_round is None:
            # If no current_round specified, process all messages (backward compatibility)
            messages = self.message_queue.copy()
            self.message_queue.clear()
        else:
            # Only process messages that should be delivered at or before current_round
            messages = [msg for msg in self.message_queue if msg.round <= current_round]
            self.message_queue = [msg for msg in self.message_queue if msg.round > current_round]
        
        for message in messages:
            if hasattr(message.content, 'creator_id'):
                if message.content not in self.mempool:
                    self.mempool.append(message.content)
                    self.propagate_transaction(message.content, message.round, message.sender_id)
            elif isinstance(message.content, (int, float)):
                pass
        return messages

    def propagate_transaction(self, transaction: Any, current_round: int, sender_id: int, seen: set = None) -> None:
        """Propagate a transaction to all neighbors except the sender."""
        if seen is None:
            seen = set()
        if transaction in seen:
            return
        seen.add(transaction)
        for neighbor_id in self.visible_nodes:
            if neighbor_id != sender_id:
                # Use send_message which handles latency calculation
                latency = self.network[self.id][neighbor_id]['weight']
                if latency <= 1.0:
                    delivery_round = current_round
                else:
                    delivery_round = current_round + 1
                self.send_message(neighbor_id, transaction, delivery_round)

    def get_mempool(self) -> List[Any]:
        """Get all transactions in the node's mempool."""
        return self.mempool.copy()

    def clear_mempool(self, block_num: int) -> None:
        """Clear transactions that have been included in blocks or are too old."""
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at >= block_num - 5]

    def get_visible_transactions(self) -> List[Any]:
        """Get all transactions that have propagated to this node."""
        transactions = []
        messages = self.receive_messages()
        for msg in messages:
            if hasattr(msg.content, 'creator_id'):
                transactions.append(msg.content)
        return transactions
    
    def update_stake(self, profit: int, validator_threshold: int = 32 * 10**9) -> None:
        """Update capital and active stake based on profit and reinvestment."""
        # Add profit to capital
        self.capital += profit
        
        # Apply reinvestment factor
        if self.restaking_factor:
            # Reinvest profit (compound)
            reinvested_profit = profit
        else:
            # Extract all profit (no compounding)
            reinvested_profit = 0
        
        # Update capital with reinvestment
        self.capital += reinvested_profit
        
        # Update active stake only when crossing threshold boundaries
        # s_i(ℓ+1) = (32 × 10^9) × ⌊k_i(ℓ+1) / (32 × 10^9)⌋
        self.active_stake = validator_threshold * (self.capital // validator_threshold)
        
        # Record history
        self.profit_history.append(profit)
        self.stake_history.append(self.active_stake)
    
    def get_validator_count(self, validator_threshold: int = 32 * 10**9) -> int:
        """Get number of active validators this participant can run."""
        return self.active_stake // validator_threshold
    
    def get_stake_ratio(self, total_network_stake: int) -> float:
        """Get ratio of this participant's stake to total network stake."""
        return self.active_stake / total_network_stake if total_network_stake > 0 else 0.0

def build_network(user_list: List[Node], builder_list: List[Node], proposer_list: List[Node], p=0.05) -> nx.Graph:
    """Build a network graph with users, builders, and proposers."""
    if not nx or not np:
        raise ImportError("networkx and numpy are required for network building")
    
    nodes: List[Node] = user_list + builder_list + proposer_list
    n_nodes = len(nodes)
    # graph = nx.erdos_renyi_graph(n_nodes, p, seed=16)
    
    # Simple approach: use higher probability for better connectivity
    graph = nx.erdos_renyi_graph(n_nodes, p=0.15, seed=16)
    
    # Ensure graph is connected
    if not nx.is_connected(graph):
        components = list(nx.connected_components(graph))
        while len(components) > 1:
            comp1, comp2 = components[0], components[1]
            node1 = list(comp1)[0]
            node2 = list(comp2)[0]
            graph.add_edge(node1, node2)
            components = list(nx.connected_components(graph))
    
    # Map node indices to actual node IDs
    mapping = {i: nodes[i].id for i in range(n_nodes)}
    graph = nx.relabel_nodes(graph, mapping)
    
    # Add node objects and set network properties
    for node in nodes:
        graph.nodes[node.id]['node'] = node
    
    # Add edge weights (latency)
    for u, v in graph.edges():
        # latency = float(np.clip(np.random.normal(1.0, 1.0), 0.1, 3.0))
        latency = float(np.clip(np.random.normal(1.0, 0.5), 0.5, 2.0))
        graph[u][v]['weight'] = latency
    
    # Set network for each node
    for node in nodes:
        node.set_network(graph)
    
    return graph

if __name__ == "__main__":
    if not nx or not np or not plt:
        print("Required libraries not available. Skipping network test.")
    else:
        # Create test nodes
        class TestNode(Node):
            def __init__(self, node_id: str) -> None:
                super().__init__(node_id)

        # Create sample nodes for testing
        test_users = [TestNode(f"user_{i}") for i in range(50)]
        test_builders = [TestNode(f"builder_{i}") for i in range(20)]
        test_proposers = [TestNode(f"proposer_{i}") for i in range(20)]

        test_graph = build_network(test_users, test_builders, test_proposers, p=0.05)
        
        # Print basic stats
        print(f"Network built successfully:")
        print(f"  Nodes: {test_graph.number_of_nodes()}")
        print(f"  Edges: {test_graph.number_of_edges()}")
        print(f"  Connected: {nx.is_connected(test_graph)}")
        print(f"  Density: {nx.density(test_graph):.4f}")
