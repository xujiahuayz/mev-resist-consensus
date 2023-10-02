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
        self.create_timestamp = timestamp
        self.sender = sender
        self.recipient = recipient
        self.gas = gas
        self.amount = amount
        self.base_fee = base_fee
        self.priority_fee = priority_fee
        self.fee = self.calculate_total_fee()

        # create time (one), enter-mempool time (multiple: dict), building time (multiple: dict), confirm time
        # # builder 1, proposer 1
        # self.create_timestamp
        # self.builder_timestamp[1]
        # self.proposer_timestamp[1]
        # self.confirm_timestamp
        
        self.builder_timestamp = dict()
        self.proposer_timestamp = dict()
    
    def calculate_total_fee(self):
        """
        Calculate the total fee of the transaction.
        """
        return self.amount * (self.base_fee + self.priority_fee)
    
    def enter_mempool(self, builder_address, enter_timestamp):
        """
        Enter the transaction into the mempool.
        """
        self.dict_timestamp[builder_address] = enter_timestamp