# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
import random

from blockchain_env.account import Account
from blockchain_env.block import Block

class Blockpool:
    # block should consist of a list of transactions
    # blockpool should be a list of blocks
    def __init__(self, address=None) -> None:
        self.blocks = []
        # here, the address is the address of the proposer
        self.address = address

    def add_block(self, block: Block, select_time) -> None:
        self.blocks.append(block)
        for transaction in block.transactions:
            transaction.enter_blockpool(proposer_address=self.address, 
                                        selected_timestamp=select_time)

    def remove_block(self, block) -> None:
        if block in self.blocks:
            self.blocks.remove(block)

class Proposer(Account):
    def __init__(self,
                 address, balance: float,
                 proposer_strategy: str = "greedy",
                 blockpool: Blockpool | None = None
    ):
        if blockpool is None:
            blockpool = Blockpool()
        else:
            self.blockpool = blockpool
        super().__init__(address, balance)
        self.proposer_strategy = proposer_strategy

    def select_block(self) -> Block | None:
        if self.proposer_strategy == "greedy":
            if not self.blockpool:
                return None

            def calculate_profit(block):
                total_profit = 0
                for transaction in block.transactions:
                    total_profit += (transaction.priority_fee * transaction.gas) - block.bid
                return total_profit

            selected_block = max(self.blockpool.blocks, key=lambda block:
                                 calculate_profit(block), default=None)
            return selected_block

        elif self.proposer_strategy == "random":
            # Choose a block randomly from the blockpool
            if not self.blockpool:
                return None
            selected_block = random.choice(list(self.blockpool.blocks()))
            return selected_block

        elif self.proposer_strategy == "cheap":
            # Select the block with the lowest bid price
            if not self.blockpool:
                return None
            selected_block = min(self.blockpool.blocks(), key=lambda x: x.bid)
            return selected_block

        else:
            raise ValueError("Invalid proposer_strategy")

    def clear_blockpool(self):
        self.blockpool = Blockpool()
