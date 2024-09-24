from blockchain_env import *
import random

random.seed(16)

BLOCKNUM = 50
BLOCK_CAP = 100
USERNUM = 50
BUILDERNUM = 20

# initialise builders
builders = []
for i in range(BUILDERNUM):
    pass
# initialise users
users = []
for i in range(USERNUM):
    pass

# users create transactions
for i in range(BLOCKNUM):
    # normal users create transactions first
    for user in users:
        if not user.is_attacker:
            # the number of transactions by each user follows a distribution
            random_number = random.randint(0, 100)
            if random_number < 50:  # 50% chance for 1 transaction
                num_transactions = 1
            elif random_number < 80:  # 30% chance for 0 transactions
                num_transactions = 0
            elif random_number < 95:  # 15% chance for 2 transactions
                num_transactions = 2
            else:  # 5% chance for 3 or more transactions
                num_transactions = random.randint(3, 5)
            for _ in range(num_transactions):
                user.create_transactions(i)
    
    # attacker users create transactions after normal users
    for user in users:
        if user.is_attacker:
            # the number of transactions by each user follows a distribution
            random_number = random.randint(0, 100)
            if random_number < 50:  # 50% chance for 1 transaction
                num_transactions = 1
            elif random_number < 80:  # 30% chance for 0 transactions
                num_transactions = 0
            elif random_number < 95:  # 15% chance for 2 transactions
                num_transactions = 2
            else:  # 5% chance for 3 or more transactions
                num_transactions = random.randint(3, 5)
            
            for _ in range(num_transactions):
                user.create_transactions(i)