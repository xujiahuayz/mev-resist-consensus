from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
from copy import deepcopy
import random
import csv

random.seed(16)

BLOCKNUM = 5
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 20

# Helper function to determine the number of transactions a user creates
def transaction_number():
    random_number = random.randint(0, 100)
    if random_number < 50:  # 50% chance for 1 transaction
        num_transactions = 1
    elif random_number < 80:  # 30% chance for 0 transactions
        num_transactions = 0
    elif random_number < 95:  # 15% chance for 2 transactions
        num_transactions = 2
    else:  # 5% chance for 3 or more transactions
        num_transactions = random.randint(3, 5)

    return num_transactions

def simulate_pbs():
    blocks = []
    all_transactions = []
    for block_num in range(BLOCKNUM):
        # Normal users create transactions first
        for user in users:
            if not user.is_attacker:
                num_transactions = transaction_number()
                print(f"User {user.id} created {num_transactions} transactions")
                for _ in range(num_transactions):
                    tx = user.create_transactions(block_num)
                    print(f"User {user.id} created transaction: {tx.id}")
                    user.broadcast_transactions(tx)
        for builder in builders:
            print(f"Builder mempool is {builder.mempool}")
        # Attacker users create transactions after normal users
        for user in users:
            if user.is_attacker:
                num_transactions = transaction_number()
                for _ in range(num_transactions):
                    tx = user.launch_attack(block_num)
                    if tx:
                        user.broadcast_transactions(tx)

        # Builders select transactions and calculate bids
        for builder in builders:
            selected_transactions = deepcopy(builder.select_transactions(block_num))
            bid_value = builder.bid(selected_transactions)
            builder.bid_value = bid_value  # Store the builder's bid value for later block selection

        # Select the block with the highest bid
        highest_bid_builder = max(builders, key=lambda b: b.bid_value)
        
        # Prepare the full block content
        block_content = {
            "block_num": block_num,
            "builder_id": highest_bid_builder.id,
            "bid_value": highest_bid_builder.bid_value,
            "transactions": [tx.__dict__ for tx in highest_bid_builder.selected_transactions]
        }
        
        # Add the block content to the list of blocks
        blocks.append(deepcopy(block_content))

        # Calculate rewards for the winning builder and participating users
        for builder in builders:
            if builder == highest_bid_builder:
                # Winning builder's reward: total gas fees of selected transactions minus the bid
                total_gas_fees = sum(tx.gas_fee for tx in builder.mempool)
                reward = total_gas_fees - builder.bid_value
                builder.balance += reward

                for tx in block_content["transactions"]:
                    if tx.creator_id == builder.id and tx.target_tx and tx.mev_potential > 0:
                        # If the builder successfully initiated and included an MEV transaction
                        target_tx = next((t for t in builder.mempool if t.id == tx.target_tx), None)
                        if target_tx:
                            builder.balance += target_tx.mev_potential

        # Calculate rewards for users based on successful transactions
        for user in users:
            user_profit = 0
            for builder in builders:
                for tx in builder.mempool:
                    if tx.creator_id == user.id:
                        if tx.target_tx and tx.mev_potential > 0:
                            # Attacker user who successfully captured MEV
                            user_profit += tx.mev_potential - tx.gas_fee
                        else:
                            # Normal transaction (benign or attacker transaction without MEV)
                            user_profit -= tx.gas_fee
            user.balance += user_profit  # Update the user's balance with their profit/loss

    with open('data/transactions.csv', 'w', newline='') as f:
        # Flatten the transactions from all blocks
        all_transactions = [tx for block in blocks for tx in block['transactions']]
        
        if not all_transactions:
            print("No transactions were created during the simulation.")
            return blocks

        fieldnames = all_transactions[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for tx in all_transactions:
            writer.writerow(tx)

    return blocks



# --- Test Cases ---
def test_builder_initialization():
    assert len(builders) == BUILDERNUM, f"Expected {BUILDERNUM} builders, but got {len(builders)}"
    attackers = [builder for builder in builders if builder.is_attacker]
    assert len(attackers) == BUILDERNUM // 2, f"Expected {BUILDERNUM // 2} attacker builders, but got {len(attackers)}"
    assert all(isinstance(builder, Builder) for builder in builders), "All elements should be Builder instances"
    print("test_builder_initialization passed!")

def test_user_initialization():
    assert len(users) == USERNUM, f"Expected {USERNUM} users, but got {len(users)}"
    attackers = [user for user in users if user.is_attacker]
    assert len(attackers) == USERNUM // 2, f"Expected {USERNUM // 2} attacker users, but got {len(attackers)}"
    assert all(isinstance(user, User) for user in users), "All elements should be User instances"
    print("test_user_initialization passed!")

def test_transaction_creation():
    # Test for non-attacker user
    non_attacker_user = next(user for user in users if not user.is_attacker)
    tx = non_attacker_user.create_transactions(1)
    assert isinstance(tx, Transaction), "Transaction creation failed"
    assert tx.creator_id == non_attacker_user.id, "Transaction creator mismatch"
    print("test_transaction_creation for non-attacker passed!")

    # Test for attacker user
    attacker_user = next(user for user in users if user.is_attacker)
    tx = attacker_user.launch_attack(1)
    assert isinstance(tx, Transaction), "Attack transaction creation failed"
    assert tx.creator_id == attacker_user.id, "Transaction creator mismatch"
    print("test_transaction_creation for attacker passed!")

def test_simulate_pbs():
    simulate_pbs()  # Run the PBS simulation
    
    # Check that transactions are broadcast correctly
    any_broadcast = False
    for builder in builders:
        if builder.get_mempool():  # If the builder has any transactions in its mempool
            any_broadcast = True
            break
    assert any_broadcast, "No transactions were broadcast to the builders' mempools"
    print("test_simulate_pbs passed!")


# --- Run Tests ---
if __name__ == "__main__":
    # global variables

    # Initialize builders: half are attackers
    builders = []
    for i in range(BUILDERNUM):
        is_attacker = i < (BUILDERNUM // 2)  # First half are attackers, second half are non-attackers
        builder = Builder(f"builder_{i}", is_attacker)
        builders.append(builder)

    # Initialize users: half are attackers
    users = []
    for i in range(USERNUM):
        is_attacker = i < (USERNUM // 2)  # First half are attackers, second half are non-attackers
        user = User(f"user_{i}", is_attacker, builders)
        users.append(user)

    simulate_pbs()
