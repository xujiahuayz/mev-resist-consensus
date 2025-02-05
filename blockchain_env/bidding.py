import random
import csv
from copy import deepcopy
from blockchain_env.transaction import Transaction
from blockchain_env.user import User

# Constants
BLOCK_CAP = 100
MAX_ROUNDS = 24
BUILDER_COUNT = 20
BLOCK_NUM = 3

random.seed(16)

class ModifiedBuilder:
    def __init__(self, builder_id, is_attacker, strategy="reactive"):
        self.id = builder_id
        self.is_attacker = is_attacker
        self.strategy = strategy
        self.mempool = []
        self.selected_transactions = []
        self.bid_history = []  # Stores bids for historical rounds

    def launch_attack(self, block_num, target_transaction, attack_type):
        # Launch an attack with specific gas fee and mev potential, targeting a specific transaction
        mev_potential = 0
        gas_fee = 0

        creator_id = self.id
        created_at = block_num
        target_tx = target_transaction

        # Create the attack transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction):
        # Builder receives transaction and adds to mempool
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num):
        selected_transactions = []
        if self.is_attacker:
            # Sort transactions by mev potential + gas fee for attackers
            self.mempool.sort(key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    if transaction.mev_potential > 0:
                        attack_type = random.choice(['front', 'back'])
                        attack_transaction = self.launch_attack(block_num, transaction, attack_type)

                        if attack_type == 'front':
                            selected_transactions.append(attack_transaction)
                            selected_transactions.append(transaction)
                        elif attack_type == 'back':
                            selected_transactions.append(transaction)
                            selected_transactions.append(attack_transaction)
                    else:
                        selected_transactions.append(transaction)
        else:
            # Sort transactions by gas fee for non-attackers
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    selected_transactions.append(transaction)

        self.selected_transactions = selected_transactions  # Update the selected_transactions attribute
        return selected_transactions

    def calculate_block_value(self):
        if not self.selected_transactions:
            return 0

        gas_fee = sum(tx.gas_fee for tx in self.selected_transactions)
        mev_value = sum(tx.mev_potential for tx in self.selected_transactions)
        return gas_fee + mev_value

    def place_bid(self, round_num, block_value, last_round_bids):
        highest_last_bid = max(last_round_bids, default=0)
        if self.strategy == "reactive":
            # Reactive strategy logic
            my_last_bid = self.bid_history[-1] if self.bid_history else 0
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
        elif self.strategy == "late_enter":
            # Late enter strategy: bid aggressively in later rounds
            if round_num < 20:
                bid = 0
            elif round_num >= 20:
                bid = min(1.05 * highest_last_bid, block_value)
        else:
            # Default bid (for the first round or non-reactive builders)
            bid = 0.5 * block_value

        self.bid_history.append(bid)
        return bid

    def get_mempool(self):
        return self.mempool

    def clear_mempool(self, winning_block_transactions):
        # Clear transactions that are included in the winning block
        self.mempool = [tx for tx in self.mempool if tx not in winning_block_transactions]


def simulate_auction(builders, users, num_blocks=BLOCK_NUM):
    all_block_data = []

    for block_num in range(num_blocks):
        print(f"\n=== Starting Block {block_num} ===")
        auction_end = random.randint(20, MAX_ROUNDS)
        last_round_bids = [0] * len(builders)  # Initialize with zeros for the first round

        for round_num in range(auction_end):
            print(f"\n--- Round {round_num} ---")

            # Users create and broadcast transactions to their visible builders
            for user in users:
                tx_count = random.randint(1, 5)
                for _ in range(tx_count):
                    tx = user.create_transactions(block_num)
                    # print(f"User {user.id} created transaction with gas_fee={tx.gas_fee}, mev_potential={tx.mev_potential}")
                    for builder in user.visible_builders:
                        builder.receive_transaction(tx)
                        # print(f"Transaction sent to Builder {builder.id}")

            # Builders select transactions, calculate block value, and place bids
            round_bids = []
            for builder in builders:
                selected_txs = builder.select_transactions(block_num)
                block_value = builder.calculate_block_value()
                bid = builder.place_bid(round_num, block_value, last_round_bids)
                round_bids.append(bid)
                all_block_data.append((block_num, round_num, builder.id, builder.strategy, bid, block_value))
                # print(f"Builder {builder.id} (strategy={builder.strategy}): "
                #       f"selected {len(selected_txs)} transactions, block_value={block_value}, bid={bid}")

            last_round_bids = round_bids  # Update for the next round

        # After the auction ends, determine the winning builder and clear their transactions from all mempools
        winning_builder_index = round_bids.index(max(round_bids))
        winning_builder = builders[winning_builder_index]
        winning_block_transactions = winning_builder.selected_transactions

        # print(f"\n=== Winning Builder for Block {block_num} ===")
        # print(f"Builder {winning_builder.id} won with bid {max(round_bids)}")

        # Clear winning block transactions from all builders' mempools
        for builder in builders:
            builder.clear_mempool(winning_block_transactions)
            # print(f"Builder {builder.id} mempool cleared. Remaining transactions: {len(builder.mempool)}")

    return all_block_data


def save_results(block_data, num_attack_builders):
    output_file = f"data/same_seed/bid_builder{num_attack_builders}.csv"
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
        builders = (
            [ModifiedBuilder(f"builder_{i}", is_attacker=True, strategy="late_enter") for i in range(5)] +
            [ModifiedBuilder(f"builder_{i+10}", is_attacker=True, strategy="reactive") for i in range(15)]
        )
        users = [User(f"user_{i}", False, builders) for i in range(50)]
        block_data = simulate_auction(builders, users, BLOCK_NUM)
        save_results(block_data, num_attack_builders)
        # print_visible_users(builders, users)