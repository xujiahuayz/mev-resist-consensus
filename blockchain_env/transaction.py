import random

from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

random.seed(16)

BLOCKNUM = 50
USERNUM = 50

tx_counter = 1

class Transaction:
    def __init__(self, gas_fee, mev_potential, creator_id, created_at, included_at, target_tx=None):
        # trasnaction id should be unique
        global tx_counter
        self.id = tx_counter
        tx_counter += 1
        self.gas_fee = gas_fee
        self.mev_potential = mev_potential
        self.creator_id = creator_id
        self.created_at = created_at
        self.included_at = included_at
        self.target_tx = target_tx

    def test_case_1(self):
        return self.id, self.gas_fee, self.mev_potential, self.creator_id, self.created_at, self.included_at, self.target_tx
    
    def test_case_2(self):
        # test tx how tx counter works when creating multiple transactions
        initial_counter = tx_counter
        
        # Generate some transactions without specifying id
        tx1 = Transaction(gas_fee=10, mev_potential=5, creator_id=1, created_at=0, included_at=1)
        tx2 = Transaction(gas_fee=20, mev_potential=10, creator_id=2, created_at=1, included_at=2)
        tx3 = Transaction(gas_fee=30, mev_potential=15, creator_id=3, created_at=2, included_at=3)
        
        # Check how id works
        print(f"Transaction 1 ID: {tx1.id}")
        print(f"Transaction 2 ID: {tx2.id}")
        print(f"Transaction 3 ID: {tx3.id}")
        print(f"Final tx_counter value: {tx_counter}")
        
        return tx1.id, tx2.id, tx3.id, tx_counter
    
if __name__ == "__main__":
    tx = Transaction(10, 5, 1, 0, 1)
    print(tx.test_case_1())
    print(tx.test_case_2())
