import random
import csv
from copy import deepcopy
from blockchain_env.transaction import Transaction
from blockchain_env.user import User

BLOCK_CAP = 100
MAX_ROUNDS = 24
BUILDER_COUNT = 20
BLOCK_NUM = 100

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

                        if len(selected_transactions) > BLOCK_CAP:
                            selected_transactions.pop()
                    else:
                        selected_transactions.append(transaction)
        else:
            # Sort transactions by gas fee for non-attackers
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    selected_transactions.append(transaction)

        return selected_transactions

    def calculate_block_value(self):
        gas_fee = sum(tx.gas_fee for tx in self.selected_transactions)
        mev_value = sum(tx.mev_potential for tx in self.selected_transactions)
        return gas_fee + mev_value

    def place_bid(self, round_num, block_value, last_round_bids):
        highest_last_bid = max(last_round_bids, default=0)
        if self.strategy == "reactive" and round_num > 0:
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
        elif self.strategy == "late_enter" and round_num > 20:
            # Late enter strategy: bid aggressively in later rounds
            bid = min (1.05 * highest_last_bid, block_value)
        else:
            # Default bid (for the first round or non-reactive builders)
            bid = 0.5 * block_value

        self.bid_history.append(bid)
        return bid

    def get_mempool(self):
        return self.mempool
    
    def clear_mempool(self, block_num):
        # clear any transsaction that is already included onchain, and also clear pending transactions that has been in mempool for too long
        timer = block_num - 5
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at < timer]



def simulate_auction(builders, users, num_blocks=BLOCK_NUM):
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
        builders = (
            [ModifiedBuilder(f"builder_{i}", is_attacker=True, strategy="late_enter") for i in range(5)] +
            [ModifiedBuilder(f"builder_{i+10}", is_attacker=True, strategy="reactive") for i in range(15)]
        )
        # builders = [ModifiedBuilder(f"builder_{i}", strategy="reactive") for i in range(BUILDER_COUNT)]
        users = [User(f"user_{i}", False, builders) for i in range(50)]
        block_data = simulate_auction(builders, users, num_blocks=100)
        save_results(block_data, num_attack_builders)