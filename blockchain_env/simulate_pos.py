from blockchain_env.user import User
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
from copy import deepcopy
import random
import csv
import time
import multiprocessing as mp

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

def process_user(user, block_num, is_attacker):
    transactions = []
    num_transactions = transaction_number()
    for _ in range(num_transactions):
        if is_attacker:
            tx = user.launch_attack(block_num)
        else:
            tx = user.create_transactions(block_num)
        if tx:
            transactions.append(tx)
    return transactions

def simulate_pos():
    blocks = []
    all_transactions = []
    block_data = []

    with mp.Pool() as pool:
        for block_num in range(BLOCKNUM):
            # Process normal users in parallel
            normal_user_transactions = pool.starmap(process_user, [(user, block_num, False) for user in users if not user.is_attacker])
            
            # Process attacker users in parallel
            attacker_user_transactions = pool.starmap(process_user, [(user, block_num, True) for user in users if user.is_attacker])
            
            # Flatten the list of transactions
            all_block_transactions = [tx for user_txs in normal_user_transactions + attacker_user_transactions for tx in user_txs]
            
            # Broadcast transactions to validators
            for validator in validators:
                for tx in all_block_transactions:
                    validator.receive_transaction(tx)

            # Randomly select a proposer
            validator = random.choice(validators)

            # Select transactions for the block
            validator.selected_transactions = validator.select_transactions(BLOCK_CAP)
            for position, tx in enumerate(validator.selected_transactions):
                tx.position = position
                tx.included_at = block_num

            # Clear validators' mempools
            for v in validators:
                v.clear_mempool(block_num)

            # Calculate total gas fee and total MEV for the block
            total_gas_fee = sum(tx.gas_fee for tx in validator.selected_transactions)
            total_mev = sum(tx.mev_potential for tx in validator.selected_transactions)


            # Process MEV targets
            mev_targets = [tx for tx in validator.selected_transactions if tx.mev_potential > 0]
            for targeted_tx in mev_targets:
                targeting_txs = [tx for tx in validator.selected_transactions if tx.target_tx == targeted_tx.id]
                if targeting_txs:
                    closest_tx = min(targeting_txs, key=lambda tx: abs(tx.position - targeted_tx.position))
                    attacker = next((user for user in users if user.id == closest_tx.sender), None)
                    if not attacker:
                        attacker = next((v for v in validators if v.id == closest_tx.sender), None)
                    if attacker:
                        attacker.balance += targeted_tx.mev_potential

            # Prepare the full block content
            block_content = {
                "block_num": block_num,
                "validator_id": validator.id,
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
    start_time = time.time()

    # Initialize validators: half are attackers
    validators = []
    for i in range(PROPNUM):
        is_attacker = i < (PROPNUM // 2)  # First half are attackers, second half are non-attackers
        validator = Builder(f"validator_{i}", is_attacker)
        validators.append(validator)

    # Initialize users: half are attackers
    users = []
    for i in range(USERNUM):
        is_attacker = i < (USERNUM // 2)  # First half are attackers, second half are non-attackers
        user = User(f"user_{i}", is_attacker, validators)
        users.append(user)

    simulate_pos()

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Simulation completed in {execution_time:.2f} seconds")