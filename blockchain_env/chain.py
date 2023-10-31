import copy
import random

from blockchain_env.account import Account
from blockchain_env.proposer import Proposer
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
from blockchain_env.constants import BASE_FEE
from blockchain_env.block import Block

class Chain:
    def __init__(self,
        normal_users: list[Account] | None = None,
        proposers: list[Proposer] | None = None,
        builders: list[Builder] | None = None,
        blocks: list[Block] | None = None,
    ):
        """
        Initialize a new chain.
        Use deepcopy to avoid modifying the original lists.
        """
        self.normal_users = copy.deepcopy(normal_users)
        self.proposers = copy.deepcopy(proposers)
        self.builders = copy.deepcopy(builders)
        self.blocks = copy.deepcopy(blocks)

        if self.normal_users is None:
            self.normal_users = []
        if self.proposers is None:
            self.proposers = []
        if self.builders is None:
            self.builders = []
        if self.blocks is None:
            self.blocks = []

    def add_block(self, block: Block, confirm_time: float, transaction: Transaction, proposer: Proposer):
        """
        Add a block to the chain.
        """
        self.blocks.append(block)
        transaction.confirm(proposer_address=proposer.address, confirm_timestamp=confirm_time)

    def find_longest_chain(self):
        """
        Find the longest chain, return a list of block ID to represent that chain.
        For example: ['2', '1', '0']. '2' is the latest block, '0' is the genesis block.
        """
        if not self.blocks:
            # If there are no blocks in the chain, return None
            return None

        block_iterated = {block.block_id: False for block in self.blocks}
        block_previous_block = {block.block_id: block.previous_block_id for block in self.blocks}
        block_previous_chain = {block.block_id: [block.block_id] for block in self.blocks}

        def find_previous_block(block_id, block_iterated, block_previous_block, block_previous_chain):
            """
            Find the previous blocks of a block, including itself.
            """
            if block_iterated[block_id]:
                # If the block has been iterated, return None
                return block_previous_chain[block_id]

            if block_previous_block[block_id] == None:
                # If the previous block is None, return None
                block_iterated[block_id] = True
                return block_previous_chain[block_id]

            result = block_previous_chain[block_id] + \
                find_previous_block(block_previous_block[block_id], block_iterated, block_previous_block, block_previous_chain)
            block_previous_chain[block_id] = result
            block_iterated[block_id] = True
            return result

        for block_id in block_iterated:
            find_previous_block(block_id, block_iterated, block_previous_block, block_previous_chain)

        #iterate through the block_previous_chain to find the longest chain
        longest_chain = []
        for block_id in block_previous_chain:
            if len(block_previous_chain[block_id]) >= len(longest_chain):
                longest_chain = block_previous_chain[block_id]

        # print(f"Longest chain: {longest_chain}")
        return longest_chain

    def find_latest_block(self):
        """
        Find the latest block's block ID in the chain, which is the last block in the longest chain.
        """
        longest_chain = self.find_longest_chain()
        if longest_chain:
            return longest_chain[0]
        else:
            return None

    def select_proposer(self):
        """
        randomly select a proposer from the proposers list.
        """
        if not self.proposers:
            raise ValueError("No proposers available in the chain.")

        selected_proposer = random.choice(self.proposers)
        return selected_proposer

if __name__ == "__main__":
    pass