"""Bidding module for blockchain environment."""

import random
import csv
from copy import deepcopy
from typing import List, Tuple
from blockchain_env.transaction import Transaction
from blockchain_env.user import User

# Constants
BLOCK_CAP: int = 100
MAX_ROUNDS: int = 24
BUILDER_COUNT: int = 20
BLOCK_NUM: int = 10

random.seed(16)

class ModifiedBuilder:
    """Builder class with attack and bidding strategies."""
    def __init__(self, builder_id: str, is_attacker: bool, strategy: str = "reactive") -> None:
        """Initialize a ModifiedBuilder."""
        self.id: str = builder_id
        self.is_attacker: bool = is_attacker
        self.strategy: str = strategy
        self.mempool: List[Transaction] = []
        self.selected_transactions: List[Transaction] = []
        self.bid_history: List[float] = []

    def launch_attack(self, block_num: int, target_transaction: Transaction, attack_type: str) -> Transaction:
        """Launch an attack transaction targeting a specific transaction."""
        mev_potential: int = 0
        gas_fee: int = 0
        creator_id: str = self.id
        created_at: int = block_num
        target_tx: Transaction = target_transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction: Transaction) -> None:
        """Receive a transaction and add to mempool."""
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num: int) -> List[Transaction]:
        """Select transactions for block proposal."""
        selected_transactions: List[Transaction] = []
        sorted_mempool = sorted(self.mempool, key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
        if self.is_attacker:
            for transaction in sorted_mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    if transaction.mev_potential > 0:
                        attack_type: str = random.choice(['front', 'back'])
                        attack_transaction: Transaction = self.launch_attack(block_num, transaction, attack_type)
                        if attack_type == 'front':
                            selected_transactions.append(attack_transaction)
                            selected_transactions.append(transaction)
                        elif attack_type == 'back':
                            selected_transactions.append(transaction)
                            selected_transactions.append(attack_transaction)
                    else:
                        selected_transactions.append(transaction)
        else:
            sorted_mempool = sorted(self.mempool, key=lambda x: x.gas_fee, reverse=True)
            selected_transactions = sorted_mempool[:BLOCK_CAP]
        self.selected_transactions = selected_transactions[:BLOCK_CAP]
        return self.selected_transactions

    def calculate_block_value(self) -> float:
        """Calculate the value of the block."""
        if not self.selected_transactions:
            return 0.0
        gas_fee: float = sum(tx.gas_fee for tx in self.selected_transactions)
        if self.is_attacker:
            mev_value: float = sum(tx.mev_potential for tx in self.selected_transactions)
            if mev_value < 0:
                print(f"Warning: Negative MEV value detected for Builder {self.id}")
        else:
            mev_value: float = 0.0
        return gas_fee + mev_value

    def place_bid(self, round_num: int, block_value: float, last_round_bids: List[float]) -> float:
        """Place a bid for the block."""
        highest_last_bid: float = max(last_round_bids, default=0.0)
        if self.strategy == "reactive":
            my_last_bid: float = self.bid_history[-1] if self.bid_history else 0.0
            second_highest_last_bid: float = sorted(last_round_bids, reverse=True)[1] if len(last_round_bids) > 1 else 0.0
            if my_last_bid < highest_last_bid:
                bid: float = min(highest_last_bid + 0.1 * highest_last_bid, block_value)
            elif my_last_bid == highest_last_bid:
                bid = my_last_bid + random.random() * (block_value - my_last_bid)
            else:
                bid = my_last_bid - 0.7 * (my_last_bid - second_highest_last_bid)
        elif self.strategy == "late_enter":
            if round_num < random.randint(17, 22):
                bid = 0.0
            else:
                bid = min(1.05 * highest_last_bid, block_value)
        else:
            bid = 0.5 * block_value
        self.bid_history.append(bid)
        return bid

    def get_mempool(self) -> List[Transaction]:
        """Get the builder's mempool."""
        return self.mempool

    def clear_mempool(self, winning_block_transactions: List[Transaction]) -> None:
        """Clear transactions included in the winning block from the mempool."""
        self.mempool = [tx for tx in self.mempool if tx not in winning_block_transactions]


def simulate_auction(builders: List[ModifiedBuilder], users: List[User], num_blocks: int = BLOCK_NUM) -> List[Tuple[int, int, str, str, float, float]]:
    """Simulate the auction process for a number of blocks."""
    all_block_data: List[Tuple[int, int, str, str, float, float]] = []
    for block_num in range(num_blocks):
        auction_end: int = random.randint(20, MAX_ROUNDS)
        last_round_bids: List[float] = [0.0] * len(builders)
        for round_num in range(auction_end):
            for user in users:
                tx_count: int = random.randint(1, 5)
                for _ in range(tx_count):
                    tx: Transaction = user.create_transactions(block_num)
                    for builder in user.visible_builders:
                        builder.receive_transaction(tx)
            round_bids: List[float] = []
            for builder in builders:
                selected_txs: List[Transaction] = builder.select_transactions(block_num)
                block_value: float = builder.calculate_block_value()
                bid: float = builder.place_bid(round_num, block_value, last_round_bids)
                round_bids.append(bid)
                all_block_data.append((block_num, round_num, builder.id, builder.strategy, bid, block_value))
            last_round_bids = round_bids
        winning_builder_index: int = round_bids.index(max(round_bids))
        winning_builder: ModifiedBuilder = builders[winning_builder_index]
        winning_block_transactions: List[Transaction] = winning_builder.selected_transactions
        for builder in builders:
            builder.clear_mempool(winning_block_transactions)
    return all_block_data


def save_results(block_data: List[Tuple[int, int, str, str, float, float]], num_attack_builders: int) -> None:
    """Save auction results to a CSV file."""
    output_file: str = f"data/same_seed/bid_builder{num_attack_builders}.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["block_num", "round_num", "builder_id", "strategy", "bid", "block_value"])
        writer.writerows(block_data)



if __name__ == "__main__":
    for num_attack_builders in [10]:
        builders: List[ModifiedBuilder] = (
            [ModifiedBuilder(f"builder_{i}", is_attacker=True, strategy="late_enter") for i in range(3)] +
            [ModifiedBuilder(f"builder_{i+3}", is_attacker=False, strategy="late_enter") for i in range(2)] +
            [ModifiedBuilder(f"builder_{i+5}", is_attacker=True, strategy="reactive") for i in range(10)] +
            [ModifiedBuilder(f"builder_{i+15}", is_attacker=False, strategy="reactive") for i in range(5)]
        )
        users: List[User] = [User(f"user_{i}", False, builders) for i in range(50)]
        block_data: List[Tuple[int, int, str, str, float, float]] = simulate_auction(builders, users, BLOCK_NUM)
        save_results(block_data, num_attack_builders)