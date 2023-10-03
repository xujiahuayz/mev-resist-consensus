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
        bid: float = 0
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
        self.bid = bid

        self.dict_timestamp = dict()
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

    def enter_blockpool(self, builder_address, selected_timestamp):
        """
        Enter the transaction into the mempool.
        """
        self.dict_timestamp[builder_address] = selected_timestamp



if __name__ == "__main__":
    # Create a Transaction instance
    transaction = Transaction(
        transaction_id="tx1",
        timestamp=0,
        sender="SenderAddress",
        recipient="RecipientAddress",
        gas=21000,
        amount=5.0,
        base_fee=2.0,
        priority_fee=1.0,
        bid=0.5
    )

    # Record timestamps
    transaction.enter_mempool("Builder1", 10)
    transaction.enter_blockpool("Builder1", 20)

    # Print the timestamps
    print("Create Timestamp:", transaction.create_timestamp)
    print("Mempool Timestamps:", transaction.dict_timestamp)
    print("Blockpool Timestamps:", transaction.dict_timestamp)
