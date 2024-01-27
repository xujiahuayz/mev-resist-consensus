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
                row = [block_id, block_bid, builder_id, transaction_ids, transaction_gas_values, transaction_mev_values]
                data.append(row)
            # Start a new block
            block_id = int(columns[0])
            block_bid = float(columns[1])
            builder_id = int(columns[2])
            # Reset the transaction data lists
            transaction_ids = []
            transaction_gas_values = []
            transaction_mev_values = []
        else:  # This is a transaction row
            transaction_id = int(columns[3])
            transaction_gas = float(columns[4])
            transaction_mev = float(columns[5])
            # Add the transaction data to the lists
            transaction_ids.append(transaction_id)
            transaction_gas_values.append(transaction_gas)
            transaction_mev_values.append(transaction_mev)

    # Store the transaction data for the last block
    row = [block_id, block_bid, builder_id, transaction_ids, transaction_gas_values, transaction_mev_values]
    data.append(row)

# Convert the list of data into a DataFrame
df = pd.DataFrame(data, columns=['Block ID', 'Block Bid', 'Builder ID', 'Transaction IDs', 'Transaction GAS', 'Transaction MEV'])

# Now you can proceed with your analysis and plotting code
print(df)

fig, axs = plt.subplots(3, 2)

# Plot 1: Total Block Bid for Each Block
block_bids = df['Block Bid'].tolist()
axs[0, 0].plot(df['Block ID'], block_bids)
axs[0, 0].set_title('Total Block Bid for Each Block')
axs[0, 0].set_xlabel('Block ID')
axs[0, 0].set_ylabel('Total Block Bid')

# Plot 2: Total Transaction GAS for Each Block
total_gas = [sum(gas) for gas in df['Transaction GAS']]
axs[0, 1].plot(df['Block ID'], total_gas)
axs[0, 1].set_title('Total Transaction GAS for Each Block')
axs[0, 1].set_xlabel('Block ID')
axs[0, 1].set_ylabel('Total Transaction GAS')

# Plot 3: Reward for Each Block
rewards = [gas - bid for gas, bid in zip(total_gas, block_bids)]
axs[1, 0].plot(df['Block ID'], rewards)
axs[1, 0].set_title('Reward for Each Block')
axs[1, 0].set_xlabel('Block ID')
axs[1, 0].set_ylabel('Reward')

# Plot 4: Cumulative Reward for Each Builder
builder_ids = df['Builder ID'].unique()
for builder_id in builder_ids:
    builder_df = df[df['Builder ID'] == builder_id]
    cumulative_rewards = np.cumsum([reward for reward, id in zip(rewards, df['Builder ID']) if id == builder_id])
    axs[1, 1].plot(builder_df['Block ID'], cumulative_rewards, label=f'Builder {builder_id}')
axs[1, 1].set_title('Cumulative Reward for Each Builder')
axs[1, 1].set_xlabel('Block ID')
axs[1, 1].set_ylabel('Cumulative Reward')
axs[1, 1].legend()

# Plot 5: Percentage of Blocks Built by Each Builder
block_counts = [len(df[df['Builder ID'] == builder_id]) for builder_id in builder_ids]
block_percentages = [count / len(df) * 100 for count in block_counts]
axs[2, 0].bar(builder_ids, block_percentages)
axs[2, 0].set_title('Percentage of Blocks Built by Each Builder')
axs[2, 0].set_xlabel('Builder ID')
axs[2, 0].set_ylabel('Percentage of Blocks Built')

def is_attacker_transaction(transaction_id):
    return abs(transaction_id) < 1000

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
    successful_attack_transactions = 2* successful_attacks
    successful_attacks_count.append(successful_attack_transactions)

# Plot 6: Attacker's Cumulative Reward
axs[2, 1].plot(block_ids, attacker_rewards, label='Cumulative Reward')
axs[2, 1].set_title("Attacker's Cumulative Reward and Attack Statistics")
axs[2, 1].set_xlabel('Block Number')
axs[2, 1].set_ylabel('Cumulative Reward')

# Add bars for the number of attacker's transactions and successful attacks
ax2 = axs[2, 1].twinx()
ax2.bar(df['Block ID'], attacker_transactions_count, color='r', alpha=0.3, label='Attacker Transactions')
ax2.bar(df['Block ID'], successful_attacks_count, color='g', alpha=1, label='Successful Attacks')
ax2.set_ylabel('Count')
ax2.legend()

plt.tight_layout()
plt.show()