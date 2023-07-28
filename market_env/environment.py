# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations


class User:
    def __init__(self, user_id):
        self.user_id = user_id

    def create_transaction(
        self, transaction_id, recipient, amount, gas_price, gas, timestamp, mempool
    ):
        transaction = Transaction(
            transaction_id, self.user_id, recipient, amount, gas_price, gas, timestamp
        )
        mempool.add_transaction(transaction)


class Transaction:
    def __init__(
        self, transaction_id, sender, recipient, amount, gas_price, gas, timestamp
    ):
        self.transaction_id = transaction_id
        self.amount = amount
        self.gas_price = gas_price
        self.sender = sender
        self.recipient = recipient
        self.timestamp = timestamp
        self.gas = gas


class Mempool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)


class Builder:
    def __init__(self, builder_id, gas_limit):
        self.builder_id = builder_id
        self.gas_limit = gas_limit

    def build_block(self, mempool):
        sorted_transactions = sorted(
            mempool.transactions, key=lambda t: t.gas_price, reverse=True
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
    def __init__(self, transactions):
        self.transactions = transactions

    def extract_header(self, builder_id):
        total_gas_price = sum(t.gas_price for t in self.transactions)
        header_id = 1  # Use a simple integer as header_id for simplicity
        return Header(header_id, 1, total_gas_price, builder_id)


class Header:
    def __init__(self, header_id, timestamp, total_gas_price, builder_id):
        self.header_id = header_id
        self.timestamp = timestamp
        self.total_gas_price = total_gas_price
        self.builder_id = builder_id


class Proposer:
    def __init__(self, signature, fee_recipient):
        self.chain = Chain()
        self.signature = signature
        self.fee_recipient = fee_recipient

    def receive_bid(self, header, bid, builder):
        if not hasattr(self, "highest_bid") or bid > self.highest_bid:
            self.highest_bid = bid
            self.winning_builder = builder
            self.winning_header = header

    def publish_block(self, mempool):
        block, _ = self.winning_builder.build_block(mempool)
        signed_block = self.sign_block(block)
        self.chain.add_block(signed_block)

    def sign_block(self, block):
        # Signing process is simplified
        return f"Block id: {self.winning_header.header_id}, Signed by: {self.signature}"


class Chain:
    def __init__(self):
        self.blocks = []

    def add_block(self, block):
        self.blocks.append(block)


if __name__ == "__main__":
    # Create a mempool
    mempool = Mempool()

    # Create users and transactions
    user1 = User("User1")
    user2 = User("User2")
    user1.create_transaction(1, "User2", 50, 5, 10, 1, mempool)
    user2.create_transaction(2, "User1", 100, 10, 20, 2, mempool)

    # Create a builder and a block
    builder = Builder("Builder1", 30)
    block, header = builder.build_block(mempool)
    print("Header ID: ", header.header_id)

    # Create a proposer and have them receive a bid
    proposer = Proposer("Signature1", "FeeRecipient1")
    proposer.receive_bid(header, 200, builder)

    # Have the proposer publish the block
    proposer.publish_block(mempool)

    # Check the blocks in the chain
    for block in proposer.chain.blocks:
        print(block)
