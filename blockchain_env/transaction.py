import random

from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

random.seed(16)

tx_counter = 0

class Transaction:
    def __init__(self, gas_fee: int, mev_potential: int, creator_id: str, created_at: int, target_tx=None):
        global tx_counter
        self.id = tx_counter
        tx_counter += 1
        self.gas_fee = gas_fee
        self.mev_potential = mev_potential
        self.creator_id = creator_id
        self.created_at = created_at
        self.included_at = None
        self.target_tx = target_tx
        self.position = None 

    def to_dict(self):
        return {
            "id": self.id,
            "position": self.position,
            "gas_fee": self.gas_fee,
            "mev_potential": self.mev_potential,
            "creator_id": self.creator_id,
            "created_at": self.created_at,
            "included_at": self.included_at,
            "target_tx": self.target_tx.id if self.target_tx else None
        }