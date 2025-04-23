import networkx as nx
import numpy as np
import random
from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.proposer import Proposer
from typing import List, Dict, Any
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
            receiver = next((n for n in self.network.nodes if n.id == receiver_id), None)
            if receiver:
                receiver.message_queue.append(message)

    def receive_messages(self) -> List[Message]:
        """Get all messages from the queue"""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages

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

    # Set network reference for all nodes
    for node in nodes:
        node.set_network(G)

    return G
