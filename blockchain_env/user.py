import random
from typing import List
from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS
from blockchain_env.transaction import Transaction
from blockchain_env.network import Node, build_network
from blockchain_env.builder import Builder

# =============================================================================
# SIMULATION PERIOD CONFIGURATION
# =============================================================================
# Change this parameter to test different market conditions:
# 
# HIGH VOLATILITY PERIODS:
#   'USDC_DEPEG_MARCH_2023'     - Post-merge high volatility (USDC depeg)
#   'FTX_COLLAPSE_NOV_2022'     - Post-merge high volatility (FTX collapse)
#   'LUNA_CRASH_MAY_2022'       - Pre-merge high volatility (Luna crash)
#
# STABLE PERIODS:
#   'STABLE_POST_MERGE_2023'    - Post-merge stable market
#   'STABLE_POST_MERGE_2022'    - Post-merge stable market
#   'STABLE_PRE_MERGE_2022'     - Pre-merge stable market
#
# ERA-BASED TESTING:
#   'post_merge'                 - All post-merge periods combined
#   'pre_merge'                  - All pre-merge periods combined
#
# PERIOD TYPE TESTING:
#   'high_volatility'           - All high volatility periods combined
#   'stable'                    - All stable periods combined
#
# Leave as None to use all available data
# =============================================================================

SIMULATION_PERIOD = 'USDC_DEPEG_MARCH_2023'  # Change this to test different periods

# Random seed for reproducibility
random.seed(16)

class User(Node):
    def __init__(self, user_id: int, is_attacker: bool) -> None:
        super().__init__(user_id)
        self.is_attacker: bool = is_attacker
        self.balance: int = 0

    def create_transactions(self, block_num: int) -> Transaction:
        # Use the configured period for gas fees and MEV potentials
        gas_fee: int = random.choice(SAMPLE_GAS_FEES(100, SIMULATION_PERIOD))
        mev_potential: int = random.choice(MEV_POTENTIALS(100, SIMULATION_PERIOD))
        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Transaction | None = None
        return Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)

    def launch_attack(self, block_num: int) -> Transaction:
        self.receive_messages()
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

    def broadcast_transactions(self, transaction: Transaction) -> None:
        self.propagate_transaction(transaction, transaction.created_at, self.id)

    @classmethod
    def test_create_transactions(cls) -> None:
        builders: List[Builder] = [Builder(i, False) for i in range(10)]
        user: User = cls(0, False)
        _network = build_network([user], builders, [])
        
        print(f"Testing with period: {SIMULATION_PERIOD or 'All periods'}")
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

    @classmethod
    def get_current_period_info(cls) -> str:
        """Get information about the currently configured simulation period."""
        if SIMULATION_PERIOD is None:
            return "Using all available periods (mixed market conditions)"
        
        period_descriptions = {
            'USDC_DEPEG_MARCH_2023': 'Post-merge high volatility (USDC depeg crisis)',
            'FTX_COLLAPSE_NOV_2022': 'Post-merge high volatility (FTX collapse)',
            'LUNA_CRASH_MAY_2022': 'Pre-merge high volatility (Luna crash)',
            'STABLE_POST_MERGE_2023': 'Post-merge stable market conditions',
            'STABLE_POST_MERGE_2022': 'Post-merge stable market conditions',
            'STABLE_PRE_MERGE_2022': 'Pre-merge stable market conditions',
            'post_merge': 'All post-merge periods combined (PoS consensus)',
            'pre_merge': 'All pre-merge periods combined (PoW consensus)',
            'high_volatility': 'All high volatility periods combined (crisis conditions)',
            'stable': 'All stable periods combined (normal conditions)'
        }
        
        return period_descriptions.get(SIMULATION_PERIOD, f"Unknown period: {SIMULATION_PERIOD}")

if __name__ == "__main__":
    print("=" * 60)
    print("MEV RESISTANCE CONSENSUS SIMULATION")
    print("=" * 60)
    print(f"Current Period: {SIMULATION_PERIOD or 'All periods'}")
    print(f"Period Description: {User.get_current_period_info()}")
    print("=" * 60)
    
    User.test_create_transactions()
    User.test_launch_attack()
    User.test_broadcast_transactions()
    
    print("\n" + "=" * 60)
    print("To test different market conditions, change SIMULATION_PERIOD at the top of this file")
    print("Available options:")
    print("  - Specific periods: 'USDC_DEPEG_MARCH_2023', 'LUNA_CRASH_MAY_2022', etc.")
    print("  - Era-based: 'post_merge', 'pre_merge'")
    print("  - Type-based: 'high_volatility', 'stable'")
    print("  - All data: None")
    print("=" * 60)
