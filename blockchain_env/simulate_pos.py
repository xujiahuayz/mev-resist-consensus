from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
from copy import deepcopy
import random
import csv

random.seed(16)

BLOCKNUM = 1000
BLOCK_CAP = 100
USERNUM = 50
PROPNUM = 20

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

def simulate_pos():
    blocks = []
    all_transactions = []
    block_data = []

    for block_num in range(BLOCKNUM):
        # Normal users create transactions first
        for user in users:
            if not user.is_attacker:
                num_transactions = transaction_number()
                for _ in range(num_transactions):
                    tx = user.create_transactions(block_num)
                    user.broadcast_transactions(tx)

        # Attacker users create transactions after normal users
        for user in users:
            if user.is_attacker:
                num_transactions = transaction_number()
                for _ in range(num_transactions):
                    tx = user.launch_attack(block_num)
                    if tx:
                        user.broadcast_transactions(tx)

        # Randomly select a proposer
        validator = random.choice(validators)

        # Select transactions for the block
        validator.selected_transactions = validator.select_transactions(BLOCK_CAP)
        for tx in validator.selected_transactions:
            tx.included_at = block_num

        # clear validator's mempool
        for validator in validators:
            validator.clear_mempool(block_num)

        # Calculate total gas fee and total MEV for the block
        total_gas_fee = sum(tx.gas_fee for tx in validator.selected_transactions)
        total_mev = sum(tx.mev_potential for tx in validator.selected_transactions)

        # Prepare the full block content
        block_content = {
            "block_num": block_num,
            "builder_id": validator.id,
            "transactions": validator.selected_transactions
        }

        # Add the block content to the list of blocks
        blocks.append(deepcopy(block_content))
        all_transactions.extend(deepcopy(block_content["transactions"]))

        # Record block data for CSV export
        block_data.append({
            "block_num": block_num,
            "validator_id": validator.id,
            "total_gas_fee": total_gas_fee,
            "total_mev_available": total_mev
        })

    # Save transaction data to CSV
    with open('data/same_seed/pos_transactions.csv', 'w', newline='') as f:
        if not all_transactions:
            return blocks

        # Convert the first transaction to a dictionary to get the field names
        fieldnames = all_transactions[0].to_dict().keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        
        # Write each transaction after converting it to a dictionary
        for tx in all_transactions:
            writer.writerow(tx.to_dict())

    # Save block data to a separate CSV
    with open('data/same_seed/pos_block_data.csv', 'w', newline='') as f:
        fieldnames = ['block_num', 'validator_id', 'total_gas_fee', 'total_mev_available']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        
        # Write each block's data
        for block in block_data:
            writer.writerow(block)

    return blocks


if __name__ == "__main__":
    # global variables

    # Initialize builders: half are attackers
    validators = []
    for i in range(PROPNUM):
        is_attacker = i < (PROPNUM // 2)  # First half are attackers, second half are non-attackers
        validator = Builder(f"builder_{i}", is_attacker)
        validators.append(validator)

    # Initialize users: half are attackers
    users = []
    for i in range(USERNUM):
        is_attacker = i < (USERNUM // 2)  # First half are attackers, second half are non-attackers
        # is_attacker = None   # testing
        user = User(f"user_{i}", is_attacker, validators)
        users.append(user)

    simulate_pos()
