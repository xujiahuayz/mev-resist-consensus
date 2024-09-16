import random

BLOCKNUM = 50
USERNUM = 50





for j in BLOCKNUM:
    # create trasnation
    tx_list = []
    for i in range(USERNUM):
        random_number = random.randint(0, 100)
        if random_number < 50:  # 50% chance for 1 transaction
            num_transactions = 1
        elif random_number < 80:  # 30% chance for 0 transactions
            num_transactions = 0
        elif random_number < 95:  # 15% chance for 2 transactions
            num_transactions = 2
        else:  # 5% chance for 3 or more transactions
            num_transactions = random.randint(3, 5)

        # observe mempool
        # create transactions
        # launch attack if it is an attcker