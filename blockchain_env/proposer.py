from blockchain_env.account import Account
from blockchain_env.constants import PROPOSER_STRATEGY_LIST

import random
class Chainpool():
    def __init__(self) -> None:
        self.bodys = []

    def add_body(self, body) -> None:
        self.bodys.append(body)

    def remove_body(self, body) -> None:
        if body in self.bodys:
            self.bodys.remove(body)
class Proposer(Account):
    def __init__(self, 
                 address, balance: float, 
                 proposer_strategy: str = "greedy", 
                 chainpool: dict[str, Chainpool] | None = None):
        super().__init__(address, balance)
        assert proposer_strategy in PROPOSER_STRATEGY_LIST, f"The proposer_strategy must be one of {PROPOSER_STRATEGY_LIST}."
        self.proposer_strategy = proposer_strategy
        self.chainpool = chainpool
    
    def select_block(self) -> str | None:
        if self.proposer_strategy == "greedy":
            # Select the body with the highest profit (priority * gas - bid)
            if not self.chainpool:
                return None  
            selected_body = max(self.chainpool.values(), key=lambda x: x.calculate_profit())
            return selected_body

        elif self.proposer_strategy == "random":
            # Choose a body randomly from the chainpool
            if not self.chainpool:
                return None  
            selected_body = random.choice(list(self.chainpool.values()))
            return selected_body

        elif self.proposer_strategy == "cheap":
            # Select the body with the lowest bid price
            if not self.chainpool:
                return None  
            selected_body = min(self.chainpool.values(), key=lambda x: x.bid)
            return selected_body

        else:
            raise ValueError("Invalid proposer_strategy")




