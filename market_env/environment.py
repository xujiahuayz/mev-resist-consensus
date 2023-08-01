# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=R0913
# pylint: disable=too-few-public-methods


from __future__ import annotations


class Chain:
    def __init__(
        self,
        users: dict[str, User] = None,
        builders: dict[str, Builder] = None,
        proposers: dict[str, Proposer] = None,
        mempools: dict[str, Mempool] = None,
    ):
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
        self.blocks: list[str] = []

    def add_block(self, block: str):
        self.blocks.append(block)
        self.update_mempools(block)

    def update_mempools(self, block: str):
        # Assuming block.transactions is a list of transaction ids
        for mempool in self.mempools.values():
            mempool.transactions = [t for t in mempool.transactions if t.transaction_id not in block.transactions]

class Node:
    """Nodes include proposers, builders, and users."""
    def __init__(self):
        self.mempool = Mempool()

    def add_peer(self, peer):
        """Add a peer node to the node's peer list."""
        self.peers.append(peer)

    def validate_transaction(self, transaction):
        return transaction.amount > 0 and transaction.gas_price > 0 and transaction.gas > 0

    def receive_transaction(self, transaction):
        if self.validate_transaction(transaction):
            self.mempool.add_transaction(transaction)
            self.broadcast_transaction(transaction)

    def broadcast_transaction(self, transaction):
        for node in self.peers:
            node.receive_transaction(transaction)

class User(Node):
    """A user with user id that can create transactions."""
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    def create_transaction(self, transaction_id: int, recipient: str, amount: float, 
                           gas_price: float, gas: int, timestamp: int) -> None:
        transaction = Transaction(
            transaction_id, self.user_id, recipient, amount, gas_price, gas, timestamp
        )
        self.receive_transaction(transaction)


class Transaction:
    """
    A transaction with transaction id, sender, recipient, amount, gas price, gas, and timestamp. 
    For storage simplicity, we use a simple integer as transaction id.
    """
    def __init__(
        self, transaction_id: int, sender: str, recipient: str, amount: float,
        gas_price: float, gas: int, timestamp: int
    ):
        self.transaction_id = transaction_id
        self.amount = amount
        self.gas_price = gas_price
        self.sender = sender
        self.recipient = recipient
        self.timestamp = timestamp
        self.gas = gas


class Mempool:
    """A mempool that stores transactions."""
    def __init__(self):
        self.transactions: list[Transaction] = []

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)


class Builder(Node):
    """A builder with builder id and gas limit that can build blocks."""
    def __init__(self, builder_id: str, gas_limit: int):
        super().__init__()
        self.builder_id = builder_id
        self.gas_limit = gas_limit

    def build_block(self):
        """
        Build a block from the mempool, and return the block and its header. 
        The ordering is based on gas price paied for the transaction.
        Add transactions to the block until the gas limit is reached.
        """
        sorted_transactions = sorted(
            self.mempool.transactions, key=lambda t: t.gas_price, reverse=True
        )
        selected_transactions = []
        gas_used = 0
        for transaction in sorted_transactions:
            if gas_used + transaction.gas <= self.gas_limit:
                selected_transactions.append(transaction)
                gas_used += transaction.gas
            else:
                break
        block = Block(selected_transactions)
        header = block.extract_header(self.builder_id)
        return block, header


class Block:
    """A block with the list of transactions packed by builder."""
    def __init__(self, transactions: list[Transaction]):
        self.transactions = transactions

    def extract_header(self, builder_id: str) -> Header:
        total_gas_price = sum(t.gas_price for t in self.transactions)
        header_id = 1  # Use a simple integer as header_id for simplicity
        return Header(header_id, 1, total_gas_price, builder_id)


class Header:
    """Header information stored."""
    def __init__(self, header_id: int, timestamp: int, total_gas_price: float, builder_id: str):
        self.header_id = header_id
        self.timestamp = timestamp
        self.total_gas_price = total_gas_price
        self.builder_id = builder_id


class Proposer(Node):
    """A proposer with signature and fee recipient that can receive bids, 
    sign and publish blocks."""
    def __init__(self, signature: str, fee_recipient: str):
        super().__init__()
        self.chain = Chain()
        self.signature = signature
        self.fee_recipient = fee_recipient
        self.highest_bid = None
        self.winning_builder = None 
        self.winning_header = None

    def receive_bid(self, header: Header, bid: float, builder: Builder):
        if self.highest_bid is None or bid > self.highest_bid:
            self.highest_bid = bid
            self.winning_builder = builder
            self.winning_header = header

    def publish_block(self):
        block, _ = self.winning_builder.build_block()
        signed_block = self.sign_block(block)
        self.chain.add_block(signed_block)

    def sign_block(self, block: Block) -> str:
        # Signing process is simplified
        return f"Block id: {block.header.header_id}, Signed by: {self.signature}"




# if __name__ == "__main__":
#     # Create users, builder, and proposer
#     user1 = User("User1")
#     user2 = User("User2")
#     builder = Builder("Builder1", 30)
#     proposer = Proposer("Signature1", "FeeRecipient1")

#     # Interconnect the nodes as peers
#     user1.add_peer(user2)
#     user1.add_peer(builder)
#     user1.add_peer(proposer)
#     user2.add_peer(user1)
#     user2.add_peer(builder)
#     user2.add_peer(proposer)
#     builder.add_peer(user1)
#     builder.add_peer(user2)
#     builder.add_peer(proposer)
#     proposer.add_peer(user1)
#     proposer.add_peer(user2)
#     proposer.add_peer(builder)

#     # Create transactions
#     user1.create_transaction(1, "User2", 50, 5, 10, 1)
#     user2.create_transaction(2, "User1", 100, 10, 20, 2)

#     # Builder builds a block and sends bid to proposer
#     block, header = builder.build_block()
#     proposer.receive_bid(header, 200, builder)

#     # Proposer publishes the block
#     proposer.publish_block()

#     # Check the blocks in the chain
#     for block in proposer.chain.blocks:
#         print(block)


