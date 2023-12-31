# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring, too-many-instance-attributes, too-many-arguments,too-few-public-methods
import uuid

from blockchain_env.transaction import Transaction

class Block:
    def __init__(self,
        previous_block_id,
        builder_id,
        timestamp: int,
        total_fee: float,
        transactions: list[Transaction] | None = None,
        proposer_address = None,
        bid = None,
    ):
        self.block_id = str(uuid.uuid4())
        self.previous_block_id = previous_block_id
        self.builder_id = builder_id
        self.proposer_address = proposer_address
        self.timestamp = timestamp
        self.total_fee = total_fee
        self.transactions = transactions if transactions is not None else []
        self.header = self.extract_header()
        self.bid = bid

    def extract_header(self) -> dict:
        """
        Extract the header of the block.
        """
        return {
            "block_id": self.block_id,
            "previous_block_id": self.previous_block_id,
            "builder_id": self.builder_id,
            "timestamp": self.timestamp,
            "total_fee": self.total_fee,
        }

    # def __init__(self, block_id, previous_block_id):
    #     """
    #     FOR TESTING ONLY: Initialize a new block.
    #     """
    #     self.block_id = block_id
    #     self.previous_block_id = previous_block_id
