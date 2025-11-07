import random
from typing import List, Optional, Any
from transaction import Transaction
from network import Node
from builder import Builder

# Random seed for reproducibility
random.seed(16)

class User(Node):
    def __init__(self, user_id: int, is_attacker: bool, restaking_factor: float = None) -> None:
        super().__init__(user_id, restaking_factor)
        self.is_attacker: bool = is_attacker
        self.balance: int = 0

    def create_transactions(self, block_num: int) -> Transaction:
        # Use fallback hardcoded values to avoid data loading warnings
        from constants import get_fallback_gas_fees, get_fallback_mev_potentials
        gas_fee: int = random.choice(get_fallback_gas_fees(100))
        mev_potential: int = random.choice(get_fallback_mev_potentials(100))
        
        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Optional[Transaction] = None
        return Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)

    def launch_attack(self, block_num: int) -> Transaction:
        # Process pending mempool to get latest transactions
        self.process_pending_mempool(block_num)
        profitable_txs: List[Transaction] = [tx for tx in self.mempool if tx.mev_potential > 0]
        if profitable_txs:
            profitable_txs.sort(key=lambda x: x.mev_potential, reverse=True)
            for i in range(min(len(profitable_txs), 5)):
                target_tx: Transaction = profitable_txs[i]
                existing_attacks: List[Transaction] = [tx for tx in self.mempool if tx.gas_fee - 2 <= target_tx.gas_fee <= tx.gas_fee + 2]
                switch_prob: float = min(0.9, len(existing_attacks) / 5)
                if random.random() >= switch_prob:
                    break
            attack_type: str = random.choice(['front', 'back'])
            if attack_type == 'front':
                gas_fee: int = target_tx.gas_fee + 1
                return Transaction(gas_fee, 0, self.id, block_num, target_tx)
            if attack_type == 'back':
                gas_fee: int = target_tx.gas_fee - 1
                return Transaction(gas_fee, 0, self.id, block_num, target_tx)
        return self.create_transactions(block_num)

    def broadcast_transactions(self, transaction: Transaction, receivers: List[Any] = None) -> None:
        """Broadcast transaction directly to all receivers using probability-based distribution.
        
        Args:
            transaction: The transaction to broadcast
            receivers: List of nodes (builders/proposers) that should receive this transaction.
                      If None, broadcasting is skipped (receivers should be provided by simulation).
        """
        if receivers is None:
            # Backward compatibility: if no receivers provided, do nothing
            # The simulation should provide the receiver list
            return
        
        # Send transaction directly to all receivers
        # Each receiver will use their own probability to decide inclusion
        for receiver in receivers:
            receiver.receive_transaction_direct(transaction)

    @classmethod
    def test_create_transactions(cls) -> None:
        builders: List[Builder] = [Builder(i, False) for i in range(10)]
        user: User = cls(0, False)
        _network = build_network([user], builders, [])
        
        print("Testing with fallback hardcoded values")
        print("=" * 50)
        
        for block_num in range(2):
            for _ in range(2):
                tx: Transaction = user.create_transactions(block_num)
                print(f"Created transaction: {tx}")
                print(f"Gas fee: {tx.gas_fee}")
                print(f"MEV potential: {tx.mev_potential}")
                print(f"Creator ID: {tx.creator_id}")
                print(f"Created at block number: {tx.created_at}")
                print(f"Target transaction: {tx.target_tx}")
                print("-" * 30)

    @classmethod
    def test_launch_attack(cls) -> None:
        builders: List[Builder] = [Builder(i, False) for i in range(10)]
        user: User = cls(1, True)
        _network = build_network([user], builders, [])
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
        network = build_network([user], builders, [])
        tx: Transaction = user.create_transactions(1)
        user.broadcast_transactions(tx)
        for node_id in user.visible_nodes:
            node = network.nodes[node_id]['node']
            if hasattr(node, 'get_mempool'):
                assert tx in node.get_mempool(), "Transaction not found in builder's mempool"
        print("test_broadcast_transactions passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("MEV RESISTANCE CONSENSUS SIMULATION")
    print("=" * 60)
    print("Using fallback hardcoded values for gas fees and MEV potentials")
    print("=" * 60)
    
    User.test_create_transactions()
    User.test_launch_attack()
    User.test_broadcast_transactions()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
