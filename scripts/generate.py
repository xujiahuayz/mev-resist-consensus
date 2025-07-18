# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
import random
import uuid
import copy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from blockchain_env.account import Account
from blockchain_env.chain import Chain
from blockchain_env.builder import Builder
from blockchain_env.constants import BASE_FEE
from blockchain_env.proposer import Proposer, Blockpool
from blockchain_env.transaction import Transaction
from blockchain_env.block import Block

random.seed(1)

NUM_USERS = 5000
NUM_TXS = 500
INIT_BALANCE = 100.0
NUM_BUILDERS = 200
NUM_PROPOSERS = 20

def generate_normal_users(num_users):
    normal_users_list = []
    for i in range(num_users):
        address = f"Address{i}"
        # balance = random.uniform(1000.0, 10000.0)
        balance = 100.0
        user = Account(address, balance)
        normal_users_list.append(user)
    return normal_users_list

# add percentage of invalid transactions
def generate_transactions(normal_users_list, num_transactions, valid_percentage):
    transactions = []
    num_valid = int(num_transactions * valid_percentage)
    for transaction in range(num_transactions):
        sender = random.choice(normal_users_list)
        recipient = random.choice(normal_users_list)
        sender_address = sender.address
        recipient_address = recipient.address
        if sender_address == recipient_address:
            while True:
                recipient = random.choice(normal_users_list)
                recipient_address = recipient.address
                if sender_address != recipient_address:
                    break

        transaction_id = str(uuid.uuid4())
        timestamp = None
        gas = 1
        base_fee = BASE_FEE
        priority_fee = random.uniform(0.0, 1)
        fee = gas * (base_fee + priority_fee)
        is_private = random.choice([True, False])

        if len(transactions) < num_valid:
            # Generate a valid transaction
            amount = random.uniform(0.1, 1)
            transaction = Transaction(
                gas_fee=fee,
                mev_potential=0,
                creator_id=sender_address,
                created_at=timestamp
            )
        else:
            # Generate an invalid transaction if the number of valid transactions
            # has reached the limit
            amount = random.uniform(0.1, 1)

            transaction = Transaction(
                gas_fee=fee,
                mev_potential=0,
                creator_id=sender_address,
                created_at=timestamp
            )

        transactions.append(transaction)

    return transactions


def generate_builders(num_builders):
    builders_list = []
    build_strategies = ['greedy', 'mev', 'random']
    bid_strategies = ['fraction_based', 'reactive', 'historical', 'last_minute', 'bluff']
    discount_factor_range = (0.0, 1.0)
    credit_range = (0.0, 1.0)
    inclusion_rate_range = (0.0, 1.0)

    for i in range(num_builders):
        builder_strategy = random.choice(build_strategies)
        bid_strategy = random.choice(bid_strategies)
        discount_factor = random.uniform(*discount_factor_range)
        credit = random.uniform(*credit_range)
        inclusion_rate = random.uniform(*inclusion_rate_range)
        private = random.choice([True, False])

        builder = Builder(
            builder_id=f"Builder{i}",
            is_attacker=False
        )
        builders_list.append(builder)
    return builders_list

def generate_proposers(num_proposers):
    proposers_list = []
    for i in range(num_proposers):
        proposer_address = f"Proposer{i}"
        blockpool = Blockpool(address=proposer_address)
        proposer = Proposer(
            proposer_id=f"Proposer{i}",
            is_attacker=False
        )
        proposers_list.append(proposer)
    return proposers_list

def simulate(chain: Chain) -> tuple[Chain, list[float], list[float], list, list]:
    counter = 0

    # Lists to store balances after each block publication
    total_proposer_balance: list[float] = []
    total_builder_balance: list[float]= []

    # generate a random number of transactions
    random_number = random.randint(1, 10)

    builder_data = []
    block_data = pd.DataFrame(columns=['Discount Factor', 'Bid Amount', 'Total Transaction Fee',
                                       'Inclusion Rate', 'Credit', 'Bid Strategy', 'Builder Strategy', 'Block Number'])
    block_data_rows = []

    while True:
        new_transactions = generate_transactions(chain.normal_users, random_number, 1)

        # for each transaction broadcast to a random set of builders
        for transaction in new_transactions:
            create_timestamp = counter
            # set a random delay for the time recieving transaction
            mempool_timestamp = create_timestamp + random.uniform(0, 1)

            if transaction.is_private:
                # For private transactions, broadcast to builders with private order flow
                private_builders = [builder for builder in chain.builders if builder.private]
                for builder in private_builders:
                    builder.mempool.add_transaction(transaction, mempool_timestamp)
            else:
                # For public transactions, broadcast to a random set of builders
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

            selected_block = selected_proposer.select_block()

            for builder in chain.builders:
                # select transactions
                selected_transactions = builder.select_transactions()
                # add a bid for the selected list of transactions
                bid_transaction = builder.bid(selected_proposer.address, block_data)

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

            # print(f"Iteration {counter}: Blockpool Contents")
            # for block in selected_proposer.blockpool.blocks:
            #     print(f"Block ID: {block.block_id}, Builder ID: {block.builder_id}, Bid: {block.bid}")

            selected_block = selected_proposer.select_block()

            # clear the blockpool for the next slot
            selected_proposer.clear_blockpool()

            # add the selected block to the longest chain
            if selected_block is not None:
                confirm_time = counter
                chain.add_block(block=selected_block, confirm_time=confirm_time,
                                transaction=transaction, proposer=selected_proposer)
                selected_proposer.blockpool.remove_block(selected_block)
                for transaction in selected_block.transactions:
                    transaction.confirm(selected_proposer.address, confirm_time)
                    for builder in chain.builders:
                        builder.mempool.remove_transaction(transaction)

            # Create a mapping from builder_id to Builder object
            builder_mapping = {builder.address: builder for builder in chain.builders}

            for selected_block in chain.blocks:
                proposer = selected_proposer
                builder = selected_block.builder_id
                # using the mapping get the builder object from the builder_id
                builder = builder_mapping.get(builder)
                proposer.deposit(selected_block.total_fee - bid_transaction.amount)
                builder.deposit(bid_transaction.amount)

                # add inclusion count for builder
                builder.inclusion_count()

                new_row = {
                    'Discount Factor': builder.discount,
                    'Bid Amount': selected_block.bid,
                    'Total Transaction Fee': sum(tx.fee for tx in selected_block.transactions),
                    'Inclusion Rate': builder.inclusion_rate,
                    'Credit': builder.credit,
                    'Builder Strategy': builder.builder_strategy,
                    'Bid Strategy': builder.bid_strategy,
                    'Block Number': counter // 12,
                }
                block_data = pd.concat([block_data, pd.DataFrame([new_row])], ignore_index=True)

                # add mev profit to builder balance
                builder = builder_mapping.get(selected_block.builder_id)
                if builder.builder_strategy == "mev":
                    builder.balance += builder.mev_profits

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

            for builder in chain.builders:
                builder.alter_strategy(block_data)

            total_proposer_balance.append(sum(proposer.balance for proposer in proposers))
            total_builder_balance.append(sum(builder.balance for builder in builders))

            block_data = pd.concat([block_data, pd.DataFrame(block_data_rows)], ignore_index=True)

        counter += 1
        if counter >= 100:
            return chain, total_proposer_balance, total_builder_balance, builder_data, block_data

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

def plot_credit():
    plt.figure(figsize=(10, 6))
    sc = plt.scatter(discount_factors, credits, alpha=0.7, c=inclusion_numbers, cmap='viridis')
    plt.colorbar(sc, label='Inclusion Number')
    plt.title('Relationship Between Discount Factor, Credit, and Inclusion Number of Builders')
    plt.xlabel('Discount Factor (Future Importance)')
    plt.ylabel('Credit Score')
    plt.grid(True)
    plt.show()

def plot_bid():
    x = block_data_df['Discount Factor']
    y = block_data_df['Bid Amount']
    sizes = block_data_df['Total Transaction Fee']
    colors = sizes

    sizes = (sizes - sizes.min()) / (sizes.max() - sizes.min()) * 100 + 20 #normalize

    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(x, y, c=colors, s=sizes, alpha=0.7, cmap='viridis', marker='x', edgecolor='black')

    # Creating a color bar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Total Transaction Fee')

    # Adding title and labels
    plt.title('Discount Factor vs Bid Amount (Color: Total Transaction Fee)')
    plt.xlabel('Discount Factor')
    plt.ylabel('Bid Amount')
    plt.grid(True)

    plt.show()

def plot_inclusion():

    plt.figure(figsize=(10, 6))
    plt.scatter(discount_factors, inclusion_times, alpha=0.7)
    plt.title('Relationship Between Discount Factor and Inclusion Time')
    plt.xlabel('Discount Factor')
    plt.ylabel('Inclusion Time (in blocks)')
    plt.grid(True)
    plt.show()

def plot_bid_time(block_data_df):
    plt.figure(figsize=(10, 6))

    # Define color mapping for each strategy
    strategy_colors = {'strategy1': 'blue', 'strategy2': 'green', 'strategy3': 'red'}

    for strategy in block_data_df['Bidding Strategy'].unique():
        # Filter data by strategy
        strategy_data = block_data_df[block_data_df['Bidding Strategy'] == strategy]
        plt.scatter(strategy_data['Slot'], strategy_data['Bid Amount'], color=strategy_colors[strategy], label=strategy)

    plt.xlabel('Slot')
    plt.ylabel('Bid Amount')
    plt.title('Selected Bids for Each Slot by Bidding Strategy')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_strategy(block_data_df):
    plt.figure(figsize=(12, 6))

    # Get the total number of blocks for x-axis
    max_block_number = block_data_df['Block Number'].max() + 1
    block_numbers = list(range(max_block_number))

    # Initialize a dictionary to store strategy counts per block
    strategy_counts = {strategy: [0] * max_block_number for strategy in block_data_df['Bid Strategy'].unique()}

    # Populate the strategy counts for each block
    for index, row in block_data_df.iterrows():
        strategy_counts[row['Bid Strategy']][row['Block Number']] += 1

    # Prepare data for stacked plot
    data_for_plot = np.array([strategy_counts[strategy] for strategy in strategy_counts])

    # Plotting a stacked graph
    plt.stackplot(block_numbers, data_for_plot, labels=strategy_counts.keys())

    plt.xlabel('Block Number')
    plt.ylabel('Number of Builders')
    plt.title('Number of Builders per Strategy Over Blocks (Stacked)')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.show()


if __name__ == "__main__":

    chain = Chain()

    normal_users = generate_normal_users(NUM_USERS)
    builders = generate_builders(NUM_BUILDERS)
    proposers = generate_proposers(NUM_PROPOSERS)

    chain.proposers = proposers
    chain.builders = builders
    chain.normal_users = normal_users

    chain, total_proposer_balance, total_builder_balance, builder_data, block_data = simulate(chain)

    block_data_df = pd.DataFrame(block_data)

    discount_factors = block_data_df['Discount Factor'].tolist()
    credits = block_data['Credit'].tolist()
    inclusion_numbers = block_data['Inclusion Rate'].tolist()
    bid_amounts = block_data['Bid Amount'].tolist()

    print(block_data_df)

    # plot_strategy(block_data_df)
