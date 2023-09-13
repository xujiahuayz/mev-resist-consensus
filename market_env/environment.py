# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=R0913
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes


from __future__ import annotations

import random

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

    def find_block_by_header(self, header: Header) -> Block:
        """Find and return the block corresponding to the given header."""
        for block in self.blocks:
            if block.header_id == header.header_id:
                return block
        return None

    def select_proposer(self) -> Proposer:
        """Select a proposer randomly."""
        return random.choice(list(self.proposers.values()))

    def reset_proposers(self) -> None:
        """Reset proposers."""
        for proposer in self.proposers.values():
            proposer.reset()
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
    def __init__(self, initial_balance: float) -> None:
        self.balance = initial_balance

    def deposit(self, amount: float) -> None:
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if self.balance < amount:
            print("Insufficient funds")
            return
        self.balance -= amount

class Block:
    """A block with the list of transactions packed by builder."""
    def __init__(self, transactions: list[Transaction], header_id: int) -> None:
        self.transactions = transactions
        self.header_id = header_id
        self.signature = None

    def extract_header(self, builder_id: str, total_fee: int) -> Header:
        """Extract header information from the block."""
        return Header(self.header_id, 1, total_fee, builder_id)

class Header:
    """Header information stored."""
    def __init__(self, header_id: int, timestamp: int, total_fee: float, builder_id: str) -> None:
        self.header_id = header_id
        self.timestamp = timestamp
        self.total_fee = total_fee
        self.builder_id = builder_id

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
        The ordering is based on the total transaction fee paid for the transaction.
        Add transactions to the block until the gas limit is reached.
        """

        # Sort transactions by total transaction fee in descending order
        sorted_transactions: list[Transaction] = sorted(
            self.mempool.transactions,
            key=lambda t: t.gas * (t.base_fee + t.priority_fee),
            reverse=True
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

        # Calculate total transaction fee for the block
        total_fee = sum(t.gas * (t.base_fee + t.priority_fee) for t in selected_transactions)

        header_id = self.chain.get_next_header_id()
        block = Block(selected_transactions, header_id)

        # Extract block header, including the total transaction fee
        header = block.extract_header(self.builder_id, total_fee)

        print(f"Builder {self.builder_id} built block with header ID {header_id}")

        return block, header

    # Example bidding strategy: 10% of total transaction fees
    def build_block_and_bid(self):
        block, header = self.build_block()
        bid = sum(t.transaction_fee for t in block.transactions) * 0.1
        return block, header, bid

class Proposer(Node, Account):
    """A proposer with signature and fee recipient that can receive bids,
    sign and publish blocks."""
    def __init__(self, chain: Chain) -> None:
        super().__init__()
        self.chain = chain
        self.candidate_headers = []
        self.winning_builder = None
        self.winning_header = None
        self.builder_bids = {}

    def receive_header(self, header: Header, builder_id: str) -> None:
        """Receive a header from a builder."""
        self.candidate_headers.append((header, builder_id))

    def select_most_profitable_header(self) -> None:
        # Find the header with the highest (transaction_fee - bid)
        max_profit = -1
        selected_header = None
        selected_builder = None

        for header, builder_id in self.candidate_headers:
            total_fee = header.total_fee
            bid = self.builder_bids.get(builder_id, 0)

            profit = total_fee - bid
            if profit > max_profit:
                max_profit = profit
                selected_header = header
                selected_builder = builder_id

        self.winning_header = selected_header
        self.winning_builder = selected_builder

    def publish_block(self) -> None:
        if self.winning_header is not None:
            corresponding_block = self.chain.find_block_by_header(self.winning_header)

            if corresponding_block is not None:
                self.chain.add_block(corresponding_block, self.winning_header)

                # Pay the builder the bid amount
                bid_to_pay: float = self.builder_bids.get(self.winning_builder, 0)

                if self.balance >= bid_to_pay:  # Make sure Proposer has enough balance
                    self.balance -= bid_to_pay  # Deduct from Proposer's balance
                    self.winning_builder.balance += bid_to_pay  # Add to Builder's balance

                # Update Proposer's balance with the remaining transaction fee
                remaining_fee: float = self.winning_header.total_fee - bid_to_pay
                self.balance += remaining_fee

                print(f"Proposer published block with header ID {self.winning_header.header_id}")
                print(f"Proposer's final balance: {self.balance}")

    def update_balance(self, total_fee):
        self.balance += total_fee

    def reset(self) -> None:
        self.candidate_headers.clear()
        self.winning_header = None
        self.winning_builder = None
        self.builder_bids.clear()

if __name__ == "__main__":
    pass
