import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Initialize empty list to store the data
data = []

# Initialize empty lists to store the transaction data for each block
transaction_ids = []
transaction_gas_values = []
transaction_mev_values = []

# Open the CSV file and read it line by line
with open('pbs_c/cmake-build-debug/transactions.csv', 'r') as file:
    for line in file:
        # Split the line into columns
        columns = line.strip().split(',')
        if columns[0] == "Block ID": continue
        # Check if this is a block row or a transaction row
        if columns[0]:  # This is a block row
            # If this is not the first block, store the transaction data for the previous block
            if transaction_ids:
                row = [block_id, block_bid, builder_id,block_value, transaction_ids, transaction_gas_values, transaction_mev_values]
                data.append(row)
            # Start a new block
            block_id = int(columns[0])
            block_bid = float(columns[1])
            builder_id = int(columns[2])
            block_value = float(columns[3])
            # Reset the transaction data lists
            transaction_ids = []
            transaction_gas_values = []
            transaction_mev_values = []
        else:  # This is a transaction row
            transaction_id = int(columns[4])
            transaction_gas = float(columns[5])
            transaction_mev = float(columns[6])
            # Add the transaction data to the lists
            transaction_ids.append(transaction_id)
            transaction_gas_values.append(transaction_gas)
            transaction_mev_values.append(transaction_mev)

    # Store the transaction data for the last block
    row = [block_id, block_bid, builder_id,block_value, transaction_ids, transaction_gas_values, transaction_mev_values]
    data.append(row)

# Convert the list of data into a DataFrame
df = pd.DataFrame(data, columns=['Block ID', 'Block Bid', 'Builder ID','Block Value', 'Transaction IDs', 'Transaction GAS', 'Transaction MEV'])

# Now you can proceed with your analysis and plotting code
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(df)

fig, axs = plt.subplots(3, 2)

# Plot 1: Total Block Bid for Each Block
block_bids = df['Block Bid'].tolist()
total_value = df['Block Value'].tolist()
total_gas = [sum(gas) for gas in df['Transaction GAS']]
axs[0, 0].plot(df['Block ID'], block_bids, label='Block Bid')
axs[0, 0].plot(df['Block ID'], total_value, label='Block Value')
axs[0, 0].plot(df['Block ID'], total_gas, label='Block GAS Fees')
axs[0, 0].set_title('Block Stats')
axs[0, 0].set_xlabel('Block ID')
axs[0, 0].set_ylabel('Units')
axs[0, 0].legend(loc='best',prop={'size': 7})

# Plot 2: Reward for Each Block
rewards = [value - bid for value, bid in zip(total_value, block_bids)]
axs[0, 1].plot(df['Block ID'], rewards)
axs[0, 1].set_title('Reward for Each Block')
axs[0, 1].set_xlabel('Block ID')
axs[0, 1].set_ylabel('Reward')

# Plot 3: % stats
reward_val_percentage = [reward / value * 100 for reward, value in zip(rewards, total_value)]
bid_val_percentage = [bid / value * 100 for bid, value in zip(block_bids, total_value)]
reward_gas_percentage = [reward / gas * 100 for reward, gas in zip(rewards, total_gas)]
bid_gas_percentage = [bid / gas * 100 for bid, gas in zip(block_bids, total_gas)]
gas_val_percentage = [gas / value * 100 for gas, value in zip(total_gas, total_value)]
reward_bid_percentage = [reward / (bid if bid != 0 else 0.001) * 100 for reward, bid in zip(rewards, block_bids)]
reward_val_percentage_moving_avg = pd.Series(reward_val_percentage).rolling(window=20).mean()
bid_val_percentage_moving_avg = pd.Series(bid_val_percentage).rolling(window=20).mean()
bid_gas_percentage_moving_avg = pd.Series(bid_gas_percentage).rolling(window=20).mean()
axs[1, 0].plot(df['Block ID'], bid_val_percentage_moving_avg, label='20 Block avg Bid Percentage of Block Value')
axs[1, 0].plot(df['Block ID'], bid_gas_percentage_moving_avg, label='20 Block avg Bid Percentage of Block Gas')
axs[1, 0].set_title('Block % Stats')
axs[1, 0].set_xlabel('Block ID')
axs[1, 0].set_ylabel('%')
#axs[1,0].set_ylim(0, 100)
axs[1, 0].legend(loc='best',prop={'size': 7})

# Plot 4: Cumulative Reward for Each Builder
builder_ids = df['Builder ID'].unique()
def get_builder_type(id):
    if 1 <= id <= 9:
        return 'Normal Builder'
    elif 10 <= id <= 99:
        return 'MEV Builder'
    else:
        return 'Unknown Builder'

def adjust_builder_id(id):
    if(get_builder_type(id) == 'MEV Builder'):
        return int(int(id) / 20 + 1)
    else:
        return id

# Plot 4: Cumulative Reward for Each Builder
for builder_id in builder_ids:
    builder_df = df[df['Builder ID'] == builder_id]
    cumulative_rewards = np.cumsum([reward for reward, id in zip(rewards, df['Builder ID']) if id == builder_id])
    axs[1, 1].plot(builder_df['Block ID'], cumulative_rewards, label=f'{get_builder_type(builder_id)} {adjust_builder_id(builder_id)}')
axs[1, 1].set_title('Cumulative Reward for Each Builder')
axs[1, 1].set_xlabel('Block ID')
axs[1, 1].set_ylabel('Cumulative Reward')
axs[1, 1].legend(loc='best',prop={'size': 7})

# Create a list of labels for the x-axis
builder_labels = [f'{get_builder_type(id)} {adjust_builder_id(id)}' for id in builder_ids]

# Plot 5: Percentage of Blocks Built by Each Builder
block_counts = [len(df[df['Builder ID'] == builder_id]) for builder_id in builder_ids]
block_percentages = [count / len(df) * 100 for count in block_counts]
axs[2, 0].bar(builder_labels, block_percentages)
axs[2, 0].set_title('Percentage of Blocks Built by Each Builder')
axs[2, 0].set_xlabel('Builder Type and ID')
axs[2, 0].set_ylabel('Percentage of Blocks Built')
# Rotate the x-axis labels
labels = axs[2, 0].get_xticklabels()
plt.setp(labels, rotation=45, horizontalalignment='right')

def is_attacker_transaction(transaction_id):
    return abs(transaction_id) < 100000

def is_successful_attack(transactions, index):
    if index < len(transactions) - 2:
        return (is_attacker_transaction(transactions[index][0]) and
                transactions[index][0] > 0 and
                not is_attacker_transaction(transactions[index + 1][0]) and
                is_attacker_transaction(transactions[index + 2][0]) and
                transactions[index + 2][0] < 0)
    return False

attacker_transactions_count = []
successful_attacks_count = []
attacker_reward = 0
attacker_rewards = []
block_ids = []

for _, row in df.iterrows():
    transactions = list(zip(row['Transaction IDs'], row['Transaction GAS'], row['Transaction MEV']))
    attacker_transactions = 0
    successful_attacks = 0
    for i in range(len(transactions)):
        transaction_id, transaction_gas, transaction_mev = transactions[i]
        if is_attacker_transaction(transaction_id):
            attacker_reward -= transaction_gas
            attacker_transactions += 1
        if is_successful_attack(transactions, i):
            attacker_reward += transactions[i + 1][2]
            successful_attacks += 1
    attacker_rewards.append(attacker_reward)
    block_ids.append(row['Block ID'])
    attacker_transactions_count.append(attacker_transactions)
    successful_attack_transactions = 2 * successful_attacks
    successful_attacks_count.append(successful_attack_transactions)

# Plot 6: Attacker's Cumulative Reward
axs[2, 1].plot(block_ids, attacker_rewards, label='Cumulative Reward')
axs[2, 1].set_title("Attacker's Cumulative Reward and Attack Statistics")
axs[2, 1].set_xlabel('Block ID')
axs[2, 1].set_ylabel('Cumulative Reward')

# Add bars for the number of attacker's transactions and successful attacks
ax2 = axs[2, 1].twinx()
ax2.bar(df['Block ID'], attacker_transactions_count, color='r', alpha=0.3, label='Attacker Transactions')
ax2.bar(df['Block ID'], successful_attacks_count, color='g', alpha=1, label='Successful Attacks')
ax2.set_ylabel('Count')
ax2.legend(loc='best',prop={'size': 7})

plt.tight_layout()
plt.show()