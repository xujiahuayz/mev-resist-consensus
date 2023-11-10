import random
import uuid
import copy
import matplotlib.pyplot as plt
import numpy as np

from blockchain_env.account import Account
from blockchain_env.chain import Chain
from blockchain_env.builder import Builder, Mempool
from blockchain_env.constants import BASE_FEE, FIGURE_PATH
from blockchain_env.proposer import Proposer, Blockpool
from blockchain_env.transaction import Transaction
from blockchain_env.block import Block

random.seed(1)

def generate_normal_users(num_users):
    normal_users = []
    for i in range(num_users):
        address = f"Address{i}"
        # balance = random.uniform(1000.0, 10000.0)
        balance = 100.0
        user = Account(address, balance)
        normal_users.append(user)
    return normal_users

# add percentage of invalid transactions
def generate_transactions(normal_users, num_transactions, valid_percentage):
    transactions = []
    num_valid = int(num_transactions * valid_percentage)

    for _ in range(num_transactions):
        sender = random.choice(normal_users)
        recipient = random.choice(normal_users)
        sender_address = sender.address
        recipient_address = recipient.address
        if sender_address == recipient_address:
            while True:
                recipient = random.choice(normal_users)
                recipient_address = recipient.address
                if sender_address != recipient_address:
                    break

        transaction_id = str(uuid.uuid4())
        timestamp = None
        gas = 1
        base_fee = BASE_FEE
        priority_fee = random.uniform(0.0, 1)
        fee = gas * (base_fee + priority_fee)

        if len(transactions) < num_valid:
            # Get the sender object
            sender_balance = sender.balance
            # Generate a valid transaction
            amount = random.uniform(0.1, 1)
            transaction = Transaction(
                transaction_id=transaction_id,
                timestamp=timestamp,
                sender=sender_address,
                recipient=recipient_address,
                gas=gas,
                amount=amount,
                base_fee=base_fee,
                priority_fee=priority_fee,
                fee = fee
            )
        else:
            # Generate an invalid transaction if the number of valid transactions
            # has reached the limit
            # sender_balance = sender.balance
            # Ensure the amount is greater than the sender's balance for an invalid
            # transaction
            # amount = sender_balance

            transaction = Transaction(
                transaction_id=transaction_id,
                timestamp=timestamp,
                sender=sender_address,
                recipient=recipient_address,
                gas=gas,
                amount=amount,
                base_fee=base_fee,
                priority_fee=priority_fee,
                fee = fee
            )

        transactions.append(transaction)

    return transactions


def generate_builders(num_builders):
    builders = []
    for i in range(num_builders):
        builder = Builder(address=f"Builder{i}", balance=initial_balance,
                          builder_strategy="mev")
        builders.append(builder)
    return builders

def generate_proposers(num_proposers):
    proposers = []
    for i in range(num_proposers):
        proposer_address = f"Proposer{i}"
        blockpool = Blockpool(address=proposer_address)
        proposer = Proposer(address=proposer_address, balance=initial_balance,
                            proposer_strategy="greedy", blockpool=blockpool)
        proposers.append(proposer)
    return proposers


def simulate(chain: Chain) -> tuple[Chain, list[float], list[float]]:
    counter = 0

    # Lists to store balances after each block publication
    total_proposer_balance: list[float] = []
    total_builder_balance: list[float]= []

    # generate a random number of transactions
    random_number = random.randint(1, 10)

    while True:
        new_transactions = generate_transactions(chain.normal_users, random_number, 1)

        # for each transaction broadcast to a random set of builders
        for transaction in new_transactions:
            create_timestamp = counter
            # set a random delay for the time recieving transaction
            mempool_timestamp = create_timestamp + random.uniform(0, 1)

            broadcasted_builders = random.sample(chain.builders, len(chain.builders) // 2)
            for builder in broadcasted_builders:
                builder.mempool.add_transaction(transaction, mempool_timestamp)


        # for each slot, a block should be built and added on chain
        if counter % 12 == 0:
            # for each builder, select transactions, append bid and add to blockpool
            # select proposer for the slot
            selected_proposer = chain.select_proposer()
            # list to store new blocks
            new_blocks = []
            for builder in chain.builders:
                # select transactions
                selected_transactions = builder.select_transactions()
                # add a bid for the selected list of transactions
                bid_transaction = builder.bid(selected_proposer.address)

                # update the selected transactions by adding the bid transaction into
                # the selected list of transactions (covered in Body class)
                selected_transactions.append(copy.deepcopy(bid_transaction))

                # record the time
                selecte_time = counter
                # get information (block_id) of previous block
                previous_block_id = chain.find_latest_block()

                total_fee = sum(transaction.fee for transaction in selected_transactions)

                # create a new block with the selected transactions
                new_block = Block(
                    block_id=uuid.uuid4(),
                    previous_block_id=previous_block_id,
                    timestamp=selecte_time,
                    proposer_address=selected_proposer.address,
                    transactions=selected_transactions,
                    builder_id=builder.address,
                    total_fee=total_fee,
                    bid=bid_transaction.amount
                )

                # add the new block to the list of new blocks
                new_blocks.append(new_block)

            selected_proposer.blockpool.add_block(new_block, selecte_time)

        # for proposer in proposers:
            # the selected proposer select a block from the blockpool
            selected_block = selected_proposer.select_block()

            # clear the blockpool for the next slot
            # selected_proposer.clear_blockpool()

            # add the selected block to the longest chain
            if selected_block is not None:
                confirm_time = counter
                chain.add_block(block=selected_block, confirm_time=confirm_time,
                                transaction=transaction, proposer=selected_proposer)
                selected_proposer.blockpool.remove_block(selected_block)
                for transaction in selected_block.transactions:
                    transaction.confirm(selected_proposer.address, confirm_time)
                    for builder in builders:
                        builder.mempool.remove_transaction(transaction)

            # balance change for each account after block put on chain
            # for each block, update the balance of proposer and builder e.g. proposer
            # get the trasnaction total fee - bid and builder get the bid
            # for each transaction in the block, update the balance of sender and recipient
            # use the withdraw and deposit method in account class

            # Create a mapping from builder_id to Builder object
            builder_mapping = {builder.address: builder for builder in chain.builders}

            for selected_block in chain.blocks:
                proposer = selected_proposer
                builder = selected_block.builder_id
                # using the mapping get the builder object from the builder_id
                builder = builder_mapping.get(builder)
                proposer.deposit(selected_block.total_fee - bid_transaction.amount)
                builder.deposit(bid_transaction.amount)

                # add mev profit to builder balance
                builder = builder_mapping.get(selected_block.builder_id)
                if builder.builder_strategy == "mev":
                    builder.balance += builder.mev_profits
                    print(f"Block ID: {selected_block.block_id}, MEV Profit: {builder.mev_profits}")

                # determine if the sender is proposer or normal user
                for transaction in selected_block.transactions:
                    sender = transaction.sender
                    sender_object = None

                    for user in (chain.normal_users + chain.proposers + chain.builders):
                        if user.address == sender:
                            sender_object = user
                            break

                    # determine if the recipient is builder or normal user
                    recipient = transaction.recipient
                    recipient_object = None
                    for user in (chain.normal_users + chain.proposers + chain.builders):
                        if user.address == recipient:
                            recipient_object = user
                            break

                    # update balance
                    sender_object.withdraw(transaction.amount)
                    recipient_object.deposit(transaction.amount-transaction.fee)

                    if builder.builder_strategy == "mev":
                        builder.mev_profits += transaction.fee

            total_proposer_balance.append(sum(proposer.balance for proposer in proposers))
            total_builder_balance.append(sum(builder.balance for builder in builders))

            # Calculate the total balance
            # total_balance = sum(user.balance for user in normal_users + proposers + builders)
            # print("Total Balance:", total_balance)
            # print("Normal User total balance:", sum(user.balance for user in normal_users))
            # print("Proposer total balance:", sum(proposer.balance for proposer in proposers))
            # print("Builder total balance:", sum(builder.balance for builder in builders))
            # print("==========")

        counter += 1
        if counter >= 2000:
            return chain, total_proposer_balance, total_builder_balance

def plot_distribution(total_proposer_balance: list[float], total_builder_balance: list[float],
                      initial_balance: float):
    block_numbers = np.arange(len(total_proposer_balance))  # Create an array of block numbers

    # Calculate the total profit (ignoring initial balances) for each block
    total_profit_proposer = np.array(total_proposer_balance) - len(total_proposer_balance) * [initial_balance]
    total_profit_builder = np.array(total_builder_balance) - len(total_builder_balance) * [initial_balance]

    # Calculate the total profit for each block
    total_profit = total_profit_proposer + total_profit_builder

    # Calculate the percentage of proposer and builder profit for each block
    proposer_percentage = (total_profit_proposer / total_profit) * 100
    builder_percentage = (total_profit_builder / total_profit) * 100

    plt.figure(figsize=(10, 6))
    plt.stackplot(block_numbers, proposer_percentage, builder_percentage,
                  labels=['Proposer Profit', 'Builder Profit'], alpha=0.7)
    plt.plot(block_numbers, np.ones_like(block_numbers) * 100, color='black',
             linestyle='--', label='Total (100%)')
    plt.xlabel('Block Number')
    plt.ylabel('Percentage')
    plt.legend(loc='upper left')
    plt.grid(False)
    plt.title('Percentage Distribution of Proposer and Builder Profits Over Blocks')
    plt.show()
    plt.savefig('./profit_distribution.pdf')

if __name__ == "__main__":

    num_users = 1000
    num_transactions = 200
    initial_balance = 100.0
    num_builders = 20
    num_proposers = 20

    chain = Chain()

    normal_users = generate_normal_users(num_users)
    builders = generate_builders(num_builders)
    proposers = generate_proposers(num_proposers)

    chain.proposers = proposers
    chain.builders = builders
    chain.normal_users = normal_users

    chain, total_proposer_balance, total_builder_balance = simulate(chain)

    # for user in chain.normal_users:
    #     print(user.address, user.balance)

    # for builder in chain.builders:
    #     print(builder.address, builder.balance)

    # for proposer in chain.proposers:
    #     print(proposer.address, proposer.balance)

    # for selected_block in chain.blocks:
    #     print(f"Block Header ID: {selected_block.block_id}")
    #     print(f"Previous Block Header ID: {selected_block.previous_block_id}")
    #     print(f"Total Fee: {selected_block.total_fee}")
    #     print(f"Number of Transactions: {len(selected_block.transactions)}")

    #     print(f"Proposer: {selected_block.proposer_address}")
    #     print(f"Builder ID: {selected_block.builder_id}")

        # for user in chain.normal_users:
        #     print(user.address, user.balance)

        # for builder in chain.builders:
        #     print(builder.address, builder.balance)

        # for proposer in chain.proposers:
        #     print(proposer.address, proposer.balance)

        # for transaction in selected_block.transactions:
            # print("Create Timestamp:", transaction.create_timestamp)
            # for builder_address, timestamp in transaction.dict_timestamp.items():
            #     print(f"  Mempool Timestamp ({builder_address}): {timestamp}")
            # print("Blockpool Timestamps:", transaction.select_timestamp)
            # print("Confirm Timestamps:", transaction.confirm_timestamp)

            # print(f"  Transaction ID: {transaction.transaction_id}")
            # print(f"  Sender: {transaction.sender}")
            # print(f"  Recipient: {transaction.recipient}")
            # print(f"  Gas: {transaction.gas}")
            # print(f"  Amount: {transaction.amount}")
            # print(f"  Base Fee: {transaction.base_fee}")
            # print(f"  Priority Fee: {transaction.priority_fee}")
            # print(f"  Fee: {transaction.fee}")
            # print()

        # print()

    data_path = FIGURE_PATH / "figures"
    plot_distribution(total_proposer_balance, total_builder_balance, initial_balance)

