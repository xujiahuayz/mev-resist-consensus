import random
import csv
from copy import deepcopy
from blockchain_env.transaction import Transaction
from blockchain_env.user import User

BLOCK_CAP = 100
MAX_ROUNDS = 24
BUILDER_COUNT = 20

class ModifiedBuilder:
    def __init__(self, builder_id, strategy="reactive"):
        self.id = builder_id
        self.strategy = strategy
        self.mempool = []
        self.selected_transactions = []
        self.bid_history = []  # Stores bids for historical rounds

    def receive_transaction(self, transaction):
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self):
        self.mempool.sort(key=lambda tx: tx.mev_potential + tx.gas_fee, reverse=True)
        self.selected_transactions = self.mempool[:BLOCK_CAP]

    def calculate_block_value(self):
        gas_fee = sum(tx.gas_fee for tx in self.selected_transactions)
        mev_value = sum(tx.mev_potential for tx in self.selected_transactions)
        return gas_fee + mev_value

    def place_bid(self, round_num, block_value, last_round_bids):
        if self.strategy == "reactive" and round_num > 0:
            # Reactive strategy logic
            my_last_bid = self.bid_history[-1] if self.bid_history else 0
            highest_last_bid = max(last_round_bids, default=0)
            second_highest_last_bid = sorted(last_round_bids, reverse=True)[1] if len(last_round_bids) > 1 else 0

            if my_last_bid < highest_last_bid:
                # Not the highest bid: raise bid
                bid = min(highest_last_bid + 0.1 * highest_last_bid, block_value)
            elif my_last_bid == highest_last_bid:
                # Tied with another builder: raise bid
                bid = my_last_bid + 0.5 * (block_value - my_last_bid)
            else:
                # Highest bid: reduce bid
                bid = my_last_bid - 0.5 * (my_last_bid - second_highest_last_bid)
        elif self.strategy == "late_enter" and round_num > 18:
            # Late enter strategy: bid aggressively in later rounds
            bid = 0.5 * block_value + random.uniform(0.1, 0.3) * block_value
        elif self.strategy == "random":
            # Random strategy: random bid based on block value
            bid = random.uniform(0.4, 0.6) * block_value
        else:
            # Default bid (for the first round or non-reactive builders)
            bid = 0.5 * block_value

        self.bid_history.append(bid)
        return bid

    def clear_mempool(self):
        self.mempool = []

def simulate_auction(builders, users, num_blocks=100):
    all_block_data = []

    for block_num in range(num_blocks):
        auction_end = random.randint(20, MAX_ROUNDS)
        last_round_bids = [0] * len(builders)  # Initialize with zeros for the first round

        for round_num in range(auction_end):
            for user in users:
                tx_count = random.randint(1, 5)
                for _ in range(tx_count):
                    tx = user.create_transactions(round_num)
                    for builder in user.visible_builders:
                        builder.receive_transaction(tx)

            round_bids = []
            for builder in builders:
                builder.select_transactions()
                block_value = builder.calculate_block_value()
                bid = builder.place_bid(round_num, block_value, last_round_bids)
                round_bids.append(bid)
                all_block_data.append((block_num, round_num, builder.id, builder.strategy, bid, block_value))

            last_round_bids = round_bids  # Update for the next round

            for builder in builders:
                builder.clear_mempool()

    return all_block_data


def save_results(block_data, num_attack_builders):
    output_file = f"data/same_seed/bid_builder{num_attack_builders}.csv"
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["block_num", "round_num", "builder_id", "strategy", "bid", "block_value"])
        writer.writerows(block_data)


if __name__ == "__main__":
    for num_attack_builders in [0, 5, 10, 15, 20]:
        # Assign specific strategies: 5 late, 5 random, 10 reactive
        builders = (
            [ModifiedBuilder(f"builder_{i}", strategy="late_enter") for i in range(5)] +
            [ModifiedBuilder(f"builder_{i+5}", strategy="random") for i in range(5)] +
            [ModifiedBuilder(f"builder_{i+10}", strategy="reactive") for i in range(10)]
        )
        users = [User(f"user_{i}", False, builders) for i in range(50)]
        block_data = simulate_auction(builders, users, num_blocks=100)
        save_results(block_data, num_attack_builders)
