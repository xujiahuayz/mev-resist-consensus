from environment import Node, Mempool, Transaction, Builder, Proposer
import copy

class Account:
    def __init__(self, address: str, balance: float):
        """
        Initialize a new account.
        """
        self.address = address
        self.balance = balance

    def deposit(self, amount: float):
        """
        Deposit amount to the account.
        """
        self.balance += amount
    
    def withdraw(self, amount: float):
        """
        Withdraw amount from the account.
        """
        if self.balance < amount:
            print(f"Insufficient balance. the amount to withdraw is {amount} but address {self.address} only has {self.balance}")
            return
        self.balance -= amount

class Block:
    def __init__(self,
        block_id: str,
        previous_block_id: str,
        builder_id: str,
        proposer_id: str,
        timestamp: int,
        total_fee: float,
        transactions: list[Transaction] = [],
    ):
        """
        Initialize a new block.
        """
        self.block_id = block_id
        self.previous_block_id = previous_block_id
        self.builder_id = builder_id
        self.proposer_id = proposer_id
        self.timestamp = timestamp
        self.total_fee = total_fee
        self.transactions = copy.deepcopy(transactions)
    
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
        nodes: list[Node] = [],
        blocks: list[Block] = [],
    ):
        """
        Initialize a new chain.
        Use deepcopy to avoid modifying the original lists.
        """
        self.accounts = copy.deepcopy(accounts)
        self.proposers = copy.deepcopy(proposers)
        self.nodes = copy.deepcopy(nodes)
        self.blocks = copy.deepcopy(blocks)
    
    def add_block(self, block: Block):
        """
        Add a block to the chain.
        """
        self.blocks.append(copy.deepcopy(block))
    
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
            return longest_chain[-1]
        else:
            return None