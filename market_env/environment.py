# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=R0913
# pylint: disable=too-few-public-methods


from __future__ import annotations

import random
import time

class Chain:
    def __init__(
        self,
        users: dict[str, User] | None = None,
        builders: dict[str, Builder] | None = None,
        proposers: dict[str, Proposer] | None = None,
        mempools: dict[str, Mempool] | None = None,
    ) -> None:
        if users is None:
            users = {}
        if builders is None:
            builders = {}
        if proposers is None:
            proposers = {}
        if mempools is None:
            mempools = {}

        self.users = users
        self.builders = builders
        self.proposers = proposers
        self.mempools = mempools
        self.blocks: list[Block] = []
        self.current_header_id = 0

    def add_block(self, block: Block) -> None:
        """Add a block to the chain."""
        self.blocks.append(block)
        self.current_header_id = block.header_id
        self.update_mempools(block)
        print(f"Added block with header ID {block.header_id} to chain")
        print(f"Current number of blocks in chain: {len(self.blocks)}")

    def update_mempools(self, block: Block) -> None:
        """Transaction should be removed from mempools after being packed into a block."""
        for transaction in block.transactions:
            for user in self.users.values():
                user.mempool.remove_transaction(transaction)
            for builder in self.builders.values():
                builder.mempool.remove_transaction(transaction)
            for proposer in self.proposers.values():
                proposer.mempool.remove_transaction(transaction)

    def get_next_header_id(self) -> int:
        """the next header id is the current header id plus 1."""
        next_header_id = self.current_header_id + 1
        print(f"Next header ID: {next_header_id}")
        return next_header_id

class Node:
    """Nodes include proposers, builders, and users."""
    def __init__(self, peers: list[Node] = None) -> None:
        self.mempool: Mempool = Mempool()
        self.peers: list[Node] = peers if peers is not None else []

    def add_peer(self, peer) -> None:
        """Add a peer node to the node's peer list."""
        self.peers.append(peer)

    def validate_transaction(self, transaction) -> bool:
        return transaction.amount > 0 and transaction.gas_price > 0 and transaction.gas > 0

    def receive_transaction(self, transaction: Transaction) -> None:
        if self.validate_transaction(transaction):
            self.mempool.add_transaction(transaction)
            self.broadcast_transaction(transaction)

    def broadcast_transaction(self, transaction: Transaction) -> None:
        for node in self.peers:
            if node not in transaction.broadcasted:
                transaction.broadcasted.append(node)
                node.receive_transaction(transaction)

class User(Node):
    """A user with user id that can create transactions."""
    def __init__(self, user_id) -> None:
        super().__init__()
        self.user_id = user_id

    def create_transaction(self, transaction_id: int, recipient: str, amount: float,
                            base_fee: float, priority_fee: float, gas: int, timestamp: int) -> None:
        transaction = Transaction(
            transaction_id, self.user_id, recipient, amount, base_fee, priority_fee, gas, timestamp
        )
        transaction.broadcasted.append(self)
        self.receive_transaction(transaction)


class Transaction:
    """
    A transaction with transaction id, sender, recipient, amount, gas price, gas, and timestamp. 
    For storage simplicity, we use a simple integer as transaction id.
    """
    def __init__(
        self, transaction_id: int, sender: str, recipient: str, amount: float,
        base_fee: float, priority_fee: float, gas: int, timestamp: int
    ) -> None:
        self.transaction_id = transaction_id
        self.amount = amount
        self.base_fee = base_fee
        self.priority_fee = priority_fee
        self.sender = sender
        self.recipient = recipient
        self.timestamp = timestamp
        self.gas = gas
        self.transaction_fee = self.gas * (self.base_fee + self.priority_fee)
        self.broadcasted = []


class Mempool:
    """A mempool that stores transactions."""
    def __init__(self) -> None:
        self.transactions: list[Transaction] = []

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def remove_transaction(self, transaction: Transaction) -> None:
        if transaction in self.transactions:
            self.transactions.remove(transaction)

class Account:
    def __init__(self, initial_balance):
        self.balance = initial_balance

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if self.balance < amount:
            print("Insufficient funds")
            return
        self.balance -= amount

class Builder(Node, Account):
    """A builder with builder id and gas limit that can build blocks."""
    def __init__(self, builder_id: str, gas_limit: int, chain: Chain) -> None:
        super().__init__()
        self.builder_id = builder_id
        self.gas_limit = gas_limit
        self.chain = chain
        self.transaction_count = 0 

    def build_block(self) -> tuple[Block, Header]:
        """
        Build a block from the mempool, and return the block and its header. 
        The ordering is based on gas price paied for the transaction.
        Add transactions to the block until the gas limit is reached.
        """
        sorted_transactions: list[Transaction] = sorted(
            self.mempool.transactions, key=lambda t: t.gas_price, reverse=True
        )
        selected_transactions: list[Transaction] = []
        gas_used: int = 0
        for transaction in sorted_transactions:
            if gas_used + transaction.gas <= self.gas_limit:
                selected_transactions.append(transaction)
                gas_used += transaction.gas
                self.transaction_count += 1 
            else:
                break
        header_id = self.chain.get_next_header_id()
        block = Block(selected_transactions, header_id)
        header = block.extract_header(self.builder_id)
        print(f"Builder {self.builder_id} built block with header ID {header_id}")
        return block, header
    
    # Example bidding strategy: 10% of total transaction fees
    def build_block_and_bid(self):
        block, header = self.build_block()
        bid = sum(t.transaction_fee for t in block.transactions) * 0.1  
        return block, header, bid

class Block:
    """A block with the list of transactions packed by builder."""
    def __init__(self, transactions: list[Transaction], header_id: int) -> None:
        self.transactions = transactions
        self.header_id = header_id
        self.signature = None

    def extract_header(self, builder_id: str) -> Header:
        """Extract header information from the block."""
        total_gas_price = sum(t.gas_price for t in self.transactions)
        return Header(self.header_id, 1, total_gas_price, builder_id)

class Header:
    """Header information stored."""
    def __init__(self, header_id: int, timestamp: int, total_gas_price: float,
                 builder_id: str) -> None:
        self.header_id = header_id
        self.timestamp = timestamp
        self.total_gas_price = total_gas_price
        self.builder_id = builder_id


class Proposer(Node, Account):
    """A proposer with signature and fee recipient that can receive bids, 
    sign and publish blocks."""
    def __init__(self, signature: str, fee_recipient: str, chain: Chain) -> None:
        super().__init__()
        self.chain = chain
        self.signature = signature
        self.fee_recipient = fee_recipient
        self.highest_bid = None
        self.winning_builder = None
        self.winning_header = None

    def receive_bid(self, header: Header, bid: float, builder: Builder) -> None:
        if self.highest_bid is None or bid > self.highest_bid:
            self.highest_bid = bid
            self.winning_builder = builder
            self.winning_header = header

    def publish_block(self) -> None:
        block, _ = self.winning_builder.build_block()
        signed_block = self.sign_block(block)
        self.chain.add_block(signed_block)
        print(f"Proposer published block with header ID {block.header_id}")

    def sign_block(self, block: Block) -> Block:
        # Signing process is simplified
        block.signature = f"Block id: {block.header_id}, Signed by: {self.signature}"
        return block


if __name__ == "__main__":
    # Create chain
    chain = Chain()

    # Create builders
    builders = {
        "builder1": Builder("builder1", 10000, chain),
        "builder2": Builder("builder2", 10000, chain),
        "builder3": Builder("builder3", 10000, chain),
        "builder4": Builder("builder4", 10000, chain),
    }

    # Create proposers
    proposers = {
        "proposer1": Proposer("proposer1_signature", "fee_recipient1", chain),
        "proposer2": Proposer("proposer2_signature", "fee_recipient2", chain),
        "proposer3": Proposer("proposer3_signature", "fee_recipient3", chain),
        "proposer4": Proposer("proposer4_signature", "fee_recipient4", chain),
    }

    # Create users
    users = {
        "user1": User("user1"),
        "user2": User("user2"),
        "user3": User("user3"),
        "user4": User("user4"),
        "user5": User("user5"),
        "user6": User("user6"),
    }

    # Add peers for all the nodes
    nodes = list(users.values()) + list(builders.values()) + list(proposers.values())
    for node in nodes:
        node.peers = [n for n in nodes if n is not node]

    # Transactions
    for i in range(50):
        user = random.choice(list(users.values()))
        recipient = random.choice([u for u in users.values() if u is not user]).user_id
        user.create_transaction(i, recipient, random.uniform(1, 100), random.uniform(1, 10),
                                random.randint(1, 500), int(time.time()))

    # Builders build blocks and make bids to proposers
    for builder in builders.values():
        block, header = builder.build_block()
        for proposer in proposers.values():
            proposer.receive_bid(header, random.uniform(1, 10), builder)

    # Proposers publish blocks
    for proposer in proposers.values():
        proposer.publish_block()

    # Display the number of transactions packed by each builder
        for builder in builders.values():
            print(f"Builder {builder.builder_id} packed {builder.transaction_count} transactions")

    # Print the ending result of the blocks
    for i, block in enumerate(chain.blocks):
        print(f"Block {i+1}:")
        print(f"  - Header ID: {block.header_id}")
        print(f"  - Signature: {block.signature}")

        for transaction in block.transactions:
            print(f"    - Transaction ID: {transaction.transaction_id}")
            print(f"      - Sender: {transaction.sender}")
            print(f"      - Recipient: {transaction.recipient}")
            print(f"      - Amount: {transaction.amount}")
            print(f"      - Gas price: {transaction.gas_price}")
            print(f"      - Gas: {transaction.gas}")
            print(f"      - Timestamp: {transaction.timestamp}")
