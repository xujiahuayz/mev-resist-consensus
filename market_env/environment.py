# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=R0913
# pylint: disable=too-few-public-methods


from __future__ import annotations


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
        self.current_header_id += 1
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
        """the next header id is the current header id plus 1."""
        return self.current_header_id + 1


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
            node.receive_transaction(transaction)

class User(Node):
    """A user with user id that can create transactions."""
    def __init__(self, user_id) -> None:
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
    ) -> None:
        self.transaction_id = transaction_id
        self.amount = amount
        self.gas_price = gas_price
        self.sender = sender
        self.recipient = recipient
        self.timestamp = timestamp
        self.gas = gas


class Mempool:
    """A mempool that stores transactions."""
    def __init__(self) -> None:
        self.transactions: list[Transaction] = []

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)

    def remove_transaction(self, transaction: Transaction) -> None:
        if transaction in self.transactions:
            self.transactions.remove(transaction)

class Builder(Node):
    """A builder with builder id and gas limit that can build blocks."""
    def __init__(self, builder_id: str, gas_limit: int, chain: Chain) -> None:
        super().__init__()
        self.builder_id = builder_id
        self.gas_limit = gas_limit
        self.chain = chain

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
            else:
                break
        header_id = self.chain.get_next_header_id()
        block = Block(selected_transactions, header_id)
        header = block.extract_header(self.builder_id)
        return block, header

class Block:
    """A block with the list of transactions packed by builder."""
    def __init__(self, transactions: list[Transaction], header_id: int) -> None:
        self.transactions = transactions
        self.header_id = header_id

    def extract_header(self, builder_id: str) -> Header:
        """Extract header information from the block."""
        total_gas_price = sum(t.gas_price for t in self.transactions)
        return Header(self.header_id, 1, total_gas_price, builder_id)

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
