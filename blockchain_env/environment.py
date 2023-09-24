from __future__ import annotations

import random
import copy
import time

class Chain:
    def __init__(
        self,
        accounts: dict[str, Account] | None = None,
        builders: dict[str, Builder] | None = None,
        proposers: dict[str, Proposer] | None = None,
        mempools: dict[str, Mempool] | None = None,
    ) -> None:
        if accounts is None:
            accounts = {}
        if builders is None:
            builders = {}
        if proposers is None:
            proposers = {}
        if mempools is None:
            mempools = {}

        self.accounts = copy.deepcopy(accounts)
        self.builders = copy.deepcopy(builders)
        self.proposers = copy.deepcopy(proposers)
        self.mempools = copy.deepcopy(mempools)
        self.blocks: list[Block] = []
        self.current_header_id = 0

    def add_block(self, block: Block) -> None:
        """
            Add a block to the chain.
        """
        self.blocks.append(block)
        self.current_header_id = block.header_id
        self.update_mempools(block)

    def update_mempools(self, block: Block) -> None:
        """
            Transaction should be removed from mempools after being packed into a block.
        """
        for transaction in block.transactions:
            for builder in self.builders.values():
                builder.mempool.remove_transaction(transaction)
            for proposer in self.proposers.values():
                proposer.mempool.remove_transaction(transaction)

    def get_next_header_id(self) -> int:
        """
            The next header ID is the current header ID plus 1.
        """
        self.current_header_id += 1
        print(f"Next header ID: {self.current_header_id}")
        return self.current_header_id

    def find_block_by_header_id(self, header_id: int) -> Block:
        """
            Find and return the block corresponding to the given header ID.
        """
        for block in self.blocks:
            if block.header_id == header_id:
                return block
        return None

    def select_proposer(self) -> Proposer:
        """
            Select a proposer randomly.
        """
        return random.choice(list(self.proposers.values()))

    def reset_proposers(self) -> None:
        """
            Reset proposers.
        """
        for proposer in self.proposers.values():
            proposer.reset()

class Node:
    """
        Nodes include proposers, builders, and users.
    """
    def __init__(self, peers: list[Node] = None) -> None:
        self.mempool: Mempool = Mempool()
        self.peers: list[Node] = peers if peers is not None else []

    def add_peer(self, peer) -> None:
        """
            Add a peer node to the node's peer list.
        """
        self.peers.append(peer)

    def validate_transaction(self, transaction) -> bool:
        return transaction.amount > 0 and transaction.transaction_fee > 0

    def receive_transaction(self, transaction: Transaction) -> None:
        if self.validate_transaction(transaction):
            self.mempool.add_transaction(transaction)
            self.broadcast_transaction(transaction)

    def broadcast_transaction(self, transaction: Transaction) -> None:
        """
            Broadcast a transaction to a random 50% of peers.
        """
        random.shuffle(self.peers)
        num_peers_to_broadcast = len(self.peers) // 2
        peers_to_broadcast = self.peers[:num_peers_to_broadcast]
        for node in peers_to_broadcast:
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
    """
        A mempool that stores transactions.
    """
    def __init__(self) -> None:
        self.transactions: list[Transaction] = []

    def add_transaction(self, transaction: Transaction) -> None:
        """
            Add a transaction to the mempool.
        """
        self.transactions.append(transaction)

    def remove_transaction(self, transaction: Transaction) -> None:
        """
            Remove a transaction from the mempool.
        """
        if transaction in self.transactions:
            self.transactions.remove(transaction)
class Account:
    def __init__(self, wallet_id, initial_balance: float) -> None:
        self.balance = initial_balance
        self.wallet_id = wallet_id

    def deposit(self, amount: float) -> None:
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if self.balance < amount:
            print("Insufficient funds")
            return
        self.balance -= amount

    # gas limit is usually 21000 for simple eth transaction
    def create_transaction(self, transaction_id: int, recipient, amount: float,
                            base_fee: float, priority_fee: float, gas: int, timestamp: int) -> None:
        '''Create a transaction and broadcast it to the network. Sender balance is immediately deducted.'''
        total_fee = gas * (base_fee + priority_fee)
        if self.balance < amount + total_fee:
            raise Exception("Insufficient funds")
        self.balance -= (amount + total_fee)
        transaction = Transaction(transaction_id, self.wallet_id, recipient.wallet_id, amount, 
                                  base_fee, priority_fee, gas, timestamp)
        transaction.broadcasted.append(self)

class Block:
    """A block with the list of transactions packed by builder."""
    def __init__(self, transactions: list[Transaction], header_id: int, timestamp: int,
                 total_fee: float, builder_id: str) -> None:
        self.transactions = transactions
        self.header_id = header_id
        self.timestamp = timestamp
        self.total_fee = total_fee
        self.builder_id = builder_id
        self.signature = None
        self.previous_block = None

    def extract_header(self) -> dict:
        """Extract header information from the block."""
        return {
            'header_id': self.header_id,
            'timestamp': self.timestamp,
            'total_fee': self.total_fee,
            'builder_id': self.builder_id,
        }

class Builder(Node, Account):
    """A builder with builder id and gas limit that can build blocks."""
    def __init__(self, builder_id: str, gas_limit: int, chain: Chain) -> None:
        super().__init__()
        self.builder_id = builder_id
        self.gas_limit = gas_limit
        self.chain = chain
        self.transaction_count = 0

    def build_block(self) -> Block:
        """
        Build a block from the mempool, and return the block.
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

        total_fee = sum(t.gas * (t.base_fee + t.priority_fee) for t in selected_transactions)
        header_id = self.chain.get_next_header_id()
        timestamp = time.time()
        builder_id = self.builder_id
        block = Block(selected_transactions, header_id, timestamp, total_fee, builder_id)

        print(f"Builder {self.builder_id} built block with ID {block.header_id}")

        return block

    # Example bidding strategy: 10% of total transaction fees
    def build_block_and_bid(self):
        block, header = self.build_block()
        bid = sum(t.transaction_fee for t in block.transactions) * 0.1
        return block, header, bid

class Proposer(Node, Account):
    """A proposer with signature and fee recipient that can receive bids,
    sign and publish blocks."""
    def __init__(self, chain: Chain, proposer_id: str) -> None:
        super().__init__()
        self.chain = chain
        self.candidate_blocks = []
        self.winning_builder = None
        self.winning_block = None
        self.builder_bids = {}
        self.proposer_id = proposer_id

    def receive_block(self, block: Block, builder_id: str) -> None:
        """Receive a block from a builder."""
        self.candidate_blocks.append((block, builder_id))

    def select_most_profitable_block(self) -> None:
        # Find the block with the highest (transaction_fee - bid)
        max_profit = -1
        selected_block = None
        selected_builder = None

        for block, builder_id in self.candidate_blocks:
            total_fee = block.total_fee
            bid = self.builder_bids.get(builder_id, 0)

            profit = total_fee - bid
            if profit > max_profit:
                max_profit = profit
                selected_block = block
                selected_builder = builder_id

        self.winning_block = selected_block
        self.winning_builder = selected_builder

    def publish_block(self) -> None:
        if self.winning_block is not None:
            self.chain.add_block(self.winning_block)

            # Pay the builder the bid amount
            bid_to_pay: float = self.builder_bids.get(self.winning_builder, 0)

            if self.balance >= bid_to_pay: 
                self.balance -= bid_to_pay  
                self.winning_builder.balance += bid_to_pay  

            remaining_fee: float = self.winning_block.total_fee - bid_to_pay
            self.balance += remaining_fee

            print(f"Proposer published block with ID {self.winning_block.header_id}")
            print(f"Proposer's final balance: {self.balance}")

    def update_balance(self, total_fee):
        self.balance += total_fee

    def reset(self) -> None:
        self.candidate_blocks.clear()
        self.winning_block = None
        self.winning_builder = None
        self.builder_bids.clear()


# if __name__ == "__main__":
#     # Initialize chain, builders, proposers, and users
#     chain = Chain()
#     builders = {f'builder_{i}': Builder(f'builder_{i}', 10, chain) for i in range(1, 4)}
#     proposers = {f'proposer_{i}': Proposer(chain, f'proposer_{i}') for i in range(1, 4)}
#     users = {f'user_{i}': User(f'user_{i}') for i in range(1, 4)}

#     # Set initialization balances
#     initial_builder_balance = 1000
#     initial_proposer_balance = 1000
#     initial_user_balance = 1000

#     for builder in builders.values():
#         builder.balance = initial_builder_balance

#     for proposer in proposers.values():
#         proposer.balance = initial_proposer_balance

#     # Initialize transactions
#     for i in range(1, 21):
#         users['user_1'].create_transaction(i, 'user_2', 10, 1, 1, 10, 1000+i)

#     # Add to Chain
#     chain.builders = builders
#     chain.proposers = proposers
#     chain.users = users

#     for _ in range(10):  # Creating 10 blocks
#         selected_proposer = chain.select_proposer()

#         for builder in chain.builders.values():
#             block, header, bid = builder.build_block_and_bid()
#             selected_proposer.receive_header(header, builder.builder_id)
#             selected_proposer.builder_bids[builder.builder_id] = bid

#         selected_proposer.select_most_profitable_header()
#         selected_proposer.publish_block()
#         selected_proposer.reset()

#     print(f"Total number of blocks in chain: {len(chain.blocks)}")

#     for i, block in enumerate(chain.blocks):
#         print(f"Block {i+1} details:")
#         print(f"  - Header ID: {block.header_id}")
#         print(f"  - Transaction IDs: {[tx.transaction_id for tx in block.transactions]}")

#     print("Remaining balances:")
#     for builder in chain.builders.values():
#         print(f"  - {builder.builder_id}: {builder.balance}")

#     for proposer in chain.proposers.values():
#         print(f"  - {proposer.proposer_id}: {proposer.balance}")  # Assuming there's a `proposer_id` attribute similar to `builder_id`.
