import copy
import random
import uuid

from blockchain_env.account import Account
from blockchain_env.proposer import Proposer
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
from blockchain_env.constants import BASE_FEE

class Block:
    def __init__(self,
        block_id,
        previous_block_id,
        builder_id,
        timestamp: int,
        total_fee: float,
        transactions: list[Transaction] = None,
        proposer_id = None,
    ):
        """
        Initialize a new block.
        """
        self.block_id = str(uuid.uuid4())
        self.previous_block_id = previous_block_id
        self.builder_id = builder_id
        self.proposer_id = proposer_id
        self.timestamp = timestamp
        self.total_fee = total_fee
        if transactions == None:
            self.transactions = []
        else:
            self.transactions = copy.deepcopy(transactions)
        self.header = self.extract_header()

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


class Chain:
    def __init__(self,
        accounts: list[Account] = [],
        proposers: list[Proposer] = [],
        builders: list[Builder] = [],
        blocks: list[Block] = [],
    ):
        """
        Initialize a new chain.
        Use deepcopy to avoid modifying the original lists.
        """
        self.accounts = copy.deepcopy(accounts)
        self.proposers = copy.deepcopy(proposers)
        self.builders = copy.deepcopy(builders)
        self.blocks = copy.deepcopy(blocks)
    
    def add_block(self, block: Block, confirm_time: int, trasnaction: Transaction, proposer: Proposer):
        """
        Add a block to the chain.
        """
        self.blocks.append(copy.deepcopy(block))
        trasnaction.confirm(proposer_address=proposer.address, confirm_timestamp=confirm_time)
    
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
        
        print(f"Longest chain: {longest_chain}")
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