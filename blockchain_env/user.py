import random
from copy import deepcopy
from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS
from blockchain_env.transaction import Transaction
from blockchain_env.builder import Builder
from blockchain_env.node import Node 
import uuid
from typing import List, Optional

random.seed(16)

class User:
    def __init__(self, user_id: int, is_attacker: bool) -> None:
        super().__init__(user_id)
        self.id: int = user_id
        self.is_attacker: bool = is_attacker
        # self.visible_builders = random.sample(builders, int(0.8 * len(builders)))
        self.balance: int = 0

    def create_transactions(self, block_num: int) -> Transaction:
        # Create a normal transaction with random gas fee and mev potential from the sample list
        gas_fee: int = random.choice(SAMPLE_GAS_FEES)
        mev_potential: int = random.choice(MEV_POTENTIALS)
        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Optional[Transaction] = None
        return Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        
    def launch_attack(self, block_num: int) -> Transaction:
        # Launch front, back, or sandwich attack on the transaction with the highest MEV potential
        # Get the mempool content from the visible builders
        mempool_content: List[Transaction] = []
        for builder in self.visible_builders:
            mempool_content.extend(deepcopy(builder.get_mempool()))

        # Filter for transactions with MEV potential greater than zero
        profitable_txs: List[Transaction] = [tx for tx in mempool_content if tx.mev_potential > 0]
        if profitable_txs:
            # Sort by highest MEV potential
            profitable_txs.sort(key=lambda x: x.mev_potential, reverse=True)

            for i in range(min(len(profitable_txs), 5)):  # Limit to 5 attempts or less
                target_tx: Transaction = profitable_txs[i]
                # Look for existing attacks by comparing gas fees
                existing_attacks: List[Transaction] = [tx for tx in mempool_content if tx.gas_fee - 2 <= target_tx.gas_fee <= tx.gas_fee + 2]
                # Calculate switch probability based on the number of existing attacks
                switch_prob: float = min(0.9, len(existing_attacks) / 5)
                if random.random() >= switch_prob:
                    break

            # Determine attack type (front, back, sandwich) and adjust the gas fee accordingly
            attack_type: str = random.choice(['front', 'back'])
            if attack_type == 'front':
                gas_fee: int = target_tx.gas_fee + 1
                return Transaction(gas_fee, 0, self.id, block_num, target_tx)  # Front-run attack
            elif attack_type == 'back':
                gas_fee: int = target_tx.gas_fee - 1
                return Transaction(gas_fee, 0, self.id, block_num, target_tx)  # Back-run attack
            
        # If no profitable transaction is found, create a benign transaction
        return self.create_transactions(block_num)

    def broadcast_transactions(self, transaction: Transaction) -> None:
        # Broadcast transactions to all visible builders
        for builder in self.visible_builders:
            builder.receive_transaction(transaction)

    @classmethod
    def test_create_transactions(cls) -> None:
        builders: List[Builder] = [Builder(i, False) for i in range(10)]
        user: User = cls(0, False)

        for block_num in range(2):
            for i in range(2): 
                tx: Transaction = user.create_transactions(block_num)
        
                print(f"Created transaction: {tx}")
                print(f"Gas fee: {tx.gas_fee}")
                print(f"MEV potential: {tx.mev_potential}")
                print(f"Creator ID: {tx.creator_id}")
                print(f"Created at block number: {tx.created_at}")
                print(f"Target transaction: {tx.target_tx}")

    @classmethod
    def test_launch_attack(cls) -> None:
        builders: List[Builder] = [Builder(i, False) for i in range(10)]
        user: User = cls(1, True)
        
        # Populate builders' mempools with some transactions
        for builder in builders:
            builder.receive_transaction(Transaction(10, 5, 2, 1, None))
            builder.receive_transaction(Transaction(15, 10, 3, 1, None))

        tx: Transaction = user.launch_attack(1)
        
        assert isinstance(tx, Transaction), "Created object is not a Transaction"
        assert tx.gas_fee in [9, 11, 14, 16], "Gas fee not as expected for an attack"
        assert tx.mev_potential == 0, "MEV potential should be 0 for an attack"
        assert tx.creator_id == user.id, "Creator ID mismatch"
        assert tx.created_at == 1, "Created_at block number mismatch"
        assert tx.target_tx is not None, "Target transaction should not be None for an attack"
        
        print("test_launch_attack passed!")

    @classmethod
    def test_broadcast_transactions(cls) -> None:
        builders: List[Builder] = [Builder(i, False) for i in range(10)]
        user: User = cls(0, False)
        tx: Transaction = user.create_transactions(1)
        user.broadcast_transactions(tx)
        
        for builder in user.visible_builders:
            assert tx in builder.get_mempool(), "Transaction not found in builder's mempool"
        
        print("test_broadcast_transactions passed!")

# Run tests
if __name__ == "__main__":
    User.test_create_transactions()
    User.test_launch_attack()
    User.test_broadcast_transactions()
