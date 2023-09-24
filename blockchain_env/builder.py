from blockchain_env.constants import BUILDER_STRATEGY_LIST
from blockchain_env.account import Account

class Mempool:
    def __init__(self):
        """
        Initialize a new mempool.
        """
        self.transactions = []
        pass

class Builder(Account):
    def __init__(self, address,
                balance: float,
                builder_strategy: str = "greedy",
    ):
        """
        Initialize a new builder.
        """
        super().__init__(address, balance)
        # make sure builder_strategy is a str from the list of available strategies
        assert builder_strategy in BUILDER_STRATEGY_LIST, f"The builder_strategy must be one of {BUILDER_STRATEGY_LIST}."
        self.builder_strategy = builder_strategy
    
    def select_transactions(self):
        pass