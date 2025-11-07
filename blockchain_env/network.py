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
    """Node class representing a participant in the network.
    
    Simplified version: No network graph needed. Transactions are distributed
    directly to receivers based on probability.
    """
    def __init__(self, node_id: int, restaking_factor: float = None, transaction_inclusion_probability: float = None) -> None:
        """Initialize a Node.
        
        Args:
            node_id: Unique identifier for the node
            restaking_factor: Factor for restaking behavior
            transaction_inclusion_probability: Probability (0-1) of including a transaction in mempool when received.
                                              If None, defaults to a random value between 0.5 and 1.0.
        """
        self.id: int = node_id
        self.mempool: List[Any] = []
        self.pending_mempool: List[Any] = []  # Transactions waiting to be included
        
        # Transaction inclusion probability (0-1)
        if transaction_inclusion_probability is None:
            # Default: random probability between 0.5 and 1.0
            self.transaction_inclusion_probability: float = random.uniform(0.5, 1.0)
        else:
            self.transaction_inclusion_probability: float = max(0.0, min(1.0, transaction_inclusion_probability))
        
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

    def receive_transaction_direct(self, transaction: Any) -> None:
        """Directly receive a transaction with probability-based inclusion.
        
        This replaces the network graph propagation. When a transaction is broadcast,
        it's sent directly to all potential receivers, and each receiver uses their
        probability to decide if it should be in mempool or pending_mempool.
        """
        # Check if transaction is already in mempool or pending_mempool
        if transaction not in self.mempool and transaction not in self.pending_mempool:
            # Use probability to decide if transaction should be included
            if random.random() < self.transaction_inclusion_probability:
                # Include in mempool immediately
                self.mempool.append(transaction)
            else:
                # Add to pending mempool to try again next round
                self.pending_mempool.append(transaction)
    
    def process_pending_mempool(self, current_round: int) -> None:
        """Process pending mempool transactions, trying to include them based on probability.
        
        Transactions in pending_mempool are retried each round until they are:
        - Successfully received (added to mempool), OR
        - Already confirmed on-chain (have included_at set)
        """
        transactions_to_remove = []
        for transaction in self.pending_mempool:
            # Skip if already in mempool (shouldn't happen, but safety check)
            if transaction in self.mempool:
                transactions_to_remove.append(transaction)
                continue
            
            # Skip if transaction is already confirmed on-chain
            if hasattr(transaction, 'included_at') and transaction.included_at is not None:
                transactions_to_remove.append(transaction)
                continue
            
            # Try again with probability
            if random.random() < self.transaction_inclusion_probability:
                # Include in mempool
                self.mempool.append(transaction)
                transactions_to_remove.append(transaction)
        
        # Remove transactions that were successfully included or already confirmed
        for transaction in transactions_to_remove:
            self.pending_mempool.remove(transaction)

    def get_mempool(self) -> List[Any]:
        """Get all transactions in the node's mempool."""
        return self.mempool.copy()

    def clear_mempool(self, block_num: int) -> None:
        """Clear transactions that have been included in blocks or are too old."""
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at >= block_num - 5]
        # Also clear old transactions from pending mempool
        self.pending_mempool = [tx for tx in self.pending_mempool if tx.included_at is None and tx.created_at >= block_num - 5]

    def get_visible_transactions(self) -> List[Any]:
        """Get all transactions in mempool (for backward compatibility)."""
        return self.mempool.copy()
    
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
        print("Network built successfully:")
        print(f"  Nodes: {test_graph.number_of_nodes()}")
        print(f"  Edges: {test_graph.number_of_edges()}")
        print(f"  Connected: {nx.is_connected(test_graph)}")
        print(f"  Density: {nx.density(test_graph):.4f}")
