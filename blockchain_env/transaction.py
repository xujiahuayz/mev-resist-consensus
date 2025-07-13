import random
from typing import Optional, Dict, Any

random.seed(16)

class Transaction:
    _tx_counter: int = 0

    def __init__(self, gas_fee: int, mev_potential: int, creator_id: str, created_at: int, target_tx: Optional['Transaction'] = None):
        self.id: int = Transaction._tx_counter
        Transaction._tx_counter += 1
        self.gas_fee: int = gas_fee
        self.mev_potential: int = mev_potential
        self.creator_id: str = creator_id
        self.created_at: int = created_at
        self.included_at: Optional[int] = None
        self.target_tx: Optional['Transaction'] = target_tx
        self.position: Optional[int] = None
        self.attack_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
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

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, gas_fee={self.gas_fee}, mev_potential={self.mev_potential}, creator_id={self.creator_id})"
