from blockchain_env.constants import BASE_FEE

class Transaction:
    def __init__(self,
        transaction_id,
        timestamp: int,
        sender,
        recipient,
        gas: int,
        amount: float,
        base_fee: float = BASE_FEE,
        priority_fee: float = 0,
    ):
        """
        Initialize a new transaction.
        """
        self.transaction_id = transaction_id
        self.timestamp = timestamp
        self.sender = sender
        self.recipient = recipient
        self.gas = gas
        self.amount = amount
        self.base_fee = base_fee
        self.priority_fee = priority_fee
    
    def calculate_total_fee(self):
        """
        Calculate the total fee of the transaction.
        """
        return self.amount * (self.base_fee + self.priority_fee)