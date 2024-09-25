import random

from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

random.seed(16)

BLOCKNUM = 50
USERNUM = 50

tx_counter = 1

class Transaction:
    def __init__(self, gas_fee, mev_potential, creator_id, created_at, included_at, target_tx=None):
        self.id = tx_counter
        tx_counter += 1
        self.gas_fee = gas_fee
        self.mev_potential = mev_potential
        self.creator_id = creator_id
        self.created_at = created_at
        self.included_at = included_at
        self.target_tx = target_tx

    def __repr__(self):
        return f"Transaction(gas_fee={self.gas_fee}, mev_potential={self.mev_potential})"

class Participant:
    def __init__(self, id, is_attacker):
        self.id = id
        self.is_attacker = is_attacker 
        self.transactions = []
        self.gas_fee = 0
        self.mempool = []

    def create_transactions(self, block_num):
        # create normal trasnctions with random gas fee and mev potential from the sample list
        for _ in range(num_transactions):
            gas_fee = random.choice(SAMPLE_GAS_FEES)
            mev_potential = random.choice(MEV_POTENTIALS)
            creator_id = self.id
            created_at = block_num
            self.transactions.append((gas_fee, mev_potential, creator_id, created_at))

    def launch_attack(self):
        # if there are profitable transctions in the mempool, user can launch attack
        # the attack could be front, back, or sandwich attack (let this be random)
        # attack the transaction with highest mev potential (if you see that there are already a lot transactions taregting the same transaction, try to attack another one)
        # other attack transactions could be spotted by seeing that gas fee is similar to the target transaction
        # the more they see others attacking the same transaction, the more likely they are to attack the same transaction
        # if no transactions are with non zero mev potential, just create benign transactions
        profitable_txs = [tx for tx in self.mempool if tx['mev_potential'] > 0]
        if profitable_txs:
            profitable_txs.sort(key=lambda x: x['mev_potential'], reverse=True)
            target_tx = profitable_txs[0]
            existing_attacks = [tx for tx in self.mempool if target_tx['gas_fee']]



    def broadcast_transactions(self):
        pass

class Builder(Participant):
    def __init__(self, id, is_attacker, balance):
        super().__init__(id, is_attacker)
        self.balance = balance

    def select_transactions(self):
        pass

    def bid(self):
        pass

def simulate():

    for j in BLOCKNUM:
        # create trasnation
        tx_list = []
        for i in range(USERNUM):
            random_number = random.randint(0, 100)
            if random_number < 50:  # 50% chance for 1 transaction
                num_transactions = 1
            elif random_number < 80:  # 30% chance for 0 transactions
                num_transactions = 0
            elif random_number < 95:  # 15% chance for 2 transactions
                num_transactions = 2
            else:  # 5% chance for 3 or more transactions
                num_transactions = random.randint(3, 5)

        # observe mempool: users should be able to see all transactions
        # create transactions: after observing the mempool, user see profitable transactions and try to attack
        # the attack could be front, back, or sandwich attack, user alter gas fee to achive the attack (alteration by 1 or 2 gwei)
        # launch attack if user is an attcker
        # otherwise create benign transactions

