from blockchain_env.account import Account
from blockchain_env.constants import PROPOSER_STRATEGY_LIST

class Proposer(Account):
    def __init__(self, address, balance: float, proposer_strategy: str = "greedy"):
        super().__init__(address, balance)
        assert proposer_strategy in PROPOSER_STRATEGY_LIST, f"The proposer_strategy must be one of {PROPOSER_STRATEGY_LIST}."
        self.proposer_strategy = proposer_strategy
    
    def select_block(self):
        pass