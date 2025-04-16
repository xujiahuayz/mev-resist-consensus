import random
import csv
from copy import deepcopy
from blockchain_env.transaction import Transaction
from blockchain_env.user import User
from typing import List, Tuple, Optional, Union, Dict, Any

# Constants
BLOCK_CAP: int = 100
MAX_ROUNDS: int = 24
BUILDER_COUNT: int = 20
BLOCK_NUM: int = 10

random.seed(16)

class ModifiedBuilder:
    def __init__(self, builder_id: str, is_attacker: bool, strategy: str = "reactive") -> None:
        self.id: str = builder_id
        self.is_attacker: bool = is_attacker
        self.strategy: str = strategy
        self.mempool: List[Transaction] = []
        self.selected_transactions: List[Transaction] = []
        self.bid_history: List[float] = []

    def launch_attack(self, block_num: int, target_transaction: Transaction, attack_type: str) -> Transaction:
        # Launch an attack with specific gas fee and mev potential, targeting a specific transaction
        mev_potential: int = 0
        gas_fee: int = 0

        creator_id: str = self.id
        created_at: int = block_num
        target_tx: Transaction = target_transaction

        # Create the attack transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction: Transaction) -> None:
        # Builder receives transaction and adds to mempool
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num: int) -> List[Transaction]:
        selected_transactions: List[Transaction] = []
        
        # Ensure the mempool is always sorted before selection
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
            # Non-attackers sort by gas fees only
            sorted_mempool = sorted(self.mempool, key=lambda x: x.gas_fee, reverse=True)
            selected_transactions = sorted_mempool[:BLOCK_CAP]
        
        self.selected_transactions = selected_transactions[:BLOCK_CAP]  # Ensure exact selection limit
        return self.selected_transactions

    def calculate_block_value(self) -> float:
        if not self.selected_transactions:
            return 0.0

        gas_fee: float = sum(tx.gas_fee for tx in self.selected_transactions)
        
        if self.is_attacker:
            mev_value: float = sum(tx.mev_potential for tx in self.selected_transactions)
            # Debugging: Ensure MEV value is being properly accounted
            if mev_value < 0:
                print(f"Warning: Negative MEV value detected for Builder {self.id}")
        else:
            mev_value: float = 0.0  # Non-attackers only get gas fees
        
        return gas_fee + mev_value

    def place_bid(self, round_num: int, block_value: float, last_round_bids: List[float]) -> float:
        highest_last_bid: float = max(last_round_bids, default=0.0)
        if self.strategy == "reactive":
            # Reactive strategy logic
            my_last_bid: float = self.bid_history[-1] if self.bid_history else 0.0
            second_highest_last_bid: float = sorted(last_round_bids, reverse=True)[1] if len(last_round_bids) > 1 else 0.0

            if my_last_bid < highest_last_bid:
                # Not the highest bid: raise bid
                bid: float = min(highest_last_bid + 0.1 * highest_last_bid, block_value)
            elif my_last_bid == highest_last_bid:
                # Tied with another builder: raise bid
                bid = my_last_bid + random.random() * (block_value - my_last_bid)
            else:
                # Highest bid: reduce bid
                bid = my_last_bid - 0.7 * (my_last_bid - second_highest_last_bid)
        elif self.strategy == "late_enter":
            # Late enter strategy: bid aggressively in later rounds
            if round_num < random.randint(17, 22):
                bid = 0.0
            else:
                bid = min(1.05 * highest_last_bid, block_value)
        else:
            # Default bid (for the first round or non-reactive builders)
            bid = 0.5 * block_value

        self.bid_history.append(bid)
        return bid

    def get_mempool(self) -> List[Transaction]:
        return self.mempool

    def clear_mempool(self, winning_block_transactions: List[Transaction]) -> None:
        # Clear transactions that are included in the winning block
        self.mempool = [tx for tx in self.mempool if tx not in winning_block_transactions]


def simulate_auction(builders: List[ModifiedBuilder], users: List[User], num_blocks: int = BLOCK_NUM) -> List[Tuple[int, int, str, str, float, float]]:
    all_block_data: List[Tuple[int, int, str, str, float, float]] = []

    for block_num in range(num_blocks):
        auction_end: int = random.randint(20, MAX_ROUNDS)
        last_round_bids: List[float] = [0.0] * len(builders)  # Initialize with zeros for the first round

        for round_num in range(auction_end):
            # Users create and broadcast transactions to their visible builders
            for user in users:
                tx_count: int = random.randint(1, 5)
                for _ in range(tx_count):
                    tx: Transaction = user.create_transactions(block_num)
                    for builder in user.visible_builders:
                        builder.receive_transaction(tx)

            # Builders select transactions, calculate block value, and place bids
            round_bids: List[float] = []
            for builder in builders:
                selected_txs: List[Transaction] = builder.select_transactions(block_num)
                block_value: float = builder.calculate_block_value()
                bid: float = builder.place_bid(round_num, block_value, last_round_bids)
                round_bids.append(bid)
                all_block_data.append((block_num, round_num, builder.id, builder.strategy, bid, block_value))

            last_round_bids = round_bids  # Update for the next round

        # After the auction ends, determine the winning builder and clear their transactions from all mempools
        winning_builder_index: int = round_bids.index(max(round_bids))
        winning_builder: ModifiedBuilder = builders[winning_builder_index]
        winning_block_transactions: List[Transaction] = winning_builder.selected_transactions

        # Clear winning block transactions from all builders' mempools
        for builder in builders:
            builder.clear_mempool(winning_block_transactions)

    return all_block_data


def save_results(block_data: List[Tuple[int, int, str, str, float, float]], num_attack_builders: int) -> None:
    output_file: str = f"data/same_seed/bid_builder{num_attack_builders}.csv"
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["block_num", "round_num", "builder_id", "strategy", "bid", "block_value"])
        writer.writerows(block_data)


# def print_visible_users(builders, users):
#     # Initialize a dictionary to count visible users per builder
#     visible_user_count = {builder.id: 0 for builder in builders}

#     # Iterate over all users and count how many times each builder is in the user's visible_builders
#     for user in users:
#         for builder in user.visible_builders:
#             visible_user_count[builder.id] += 1

#     # Now print the results
#     for builder_id, count in visible_user_count.items():
#         print(f"Builder {builder_id} has {count} visible users")

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
        # print_visible_users(builders, users)