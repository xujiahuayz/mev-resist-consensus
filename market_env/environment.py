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
        """The next header ID is the current header ID plus 1."""
        self.current_header_id += 1
        print(f"Next header ID: {self.current_header_id}")
        return self.current_header_id

class Node:
    """Nodes include proposers, builders, and users."""
    def __init__(self, peers: list[Node] = None) -> None:
        self.mempool: Mempool = Mempool()
        self.peers: list[Node] = peers if peers is not None else []

    def add_peer(self, peer) -> None:
        """Add a peer node to the node's peer list."""
        self.peers.append(peer)

    def validate_transaction(self, transaction) -> bool:
        return transaction.amount > 0 and transaction.transaction_fee > 0 and transaction.gas > 0

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
        The ordering is based on the transaction fee paid for the transaction.
        Add transactions to the block until the gas limit is reached.
        """
        sorted_transactions: list[Transaction] = sorted(
            self.mempool.transactions, key=lambda t: t.transaction_fee, reverse=True
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
        total_transaction_fee = sum(t.transaction_fee for t in self.transactions)
        return Header(self.header_id, 1, total_transaction_fee, builder_id)

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
    # Initialize chain
    my_chain = Chain()

    # Initialize builder with initial balance of 1000
    my_builder = Builder("builder1", 10000, my_chain)
    my_builder.balance = 1000  # Initial balance

    # Initialize proposer with initial balance of 500
    my_proposer = Proposer("signature1", "fee_recipient1", my_chain)
    my_proposer.balance = 500  # Initial balance

    # Initialize user
    my_user = User("user1")
    my_user.balance = 200  # Initial balance

    # User creates a transaction
    my_user.create_transaction(
        transaction_id=1, recipient="user2", amount=10, base_fee=1, priority_fee=2, gas=100, timestamp=int(time.time())
    )

    # Builder builds a block
    new_block, new_header = my_builder.build_block()

    # Builder bids for the block
    _, _, bid = my_builder.build_block_and_bid()

    # Proposer receives the bid
    my_proposer.receive_bid(new_header, bid, my_builder)

    # Proposer publishes the block
    my_proposer.publish_block()

    # Check final chain status
    print(f"Final number of blocks in chain: {len(my_chain.blocks)}")
    print(f"Transactions in the last block: {[t.transaction_id for t in my_chain.blocks[-1].transactions]}")

    # Display balances
    print(f"Builder's final balance: {my_builder.balance}")
    print(f"Proposer's final balance: {my_proposer.balance}")
    print(f"User's final balance: {my_user.balance}")
