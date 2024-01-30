import pandas as pd
import matplotlib.pyplot as plt

# Initialize empty list to store the data
data = []

# Open the CSV file and read it line by line
with open('pbs_c/cmake-build-debug/transactions.csv', 'r') as file:
    for line in file:
        transaction_data = []
        # Split the line into columns
        columns = line.strip().split(',')

        # Check if this is a block row or a transaction row
        if columns[0] is not "":  # This is a block row
            block_id = int(columns[0])
            block_bid = float(columns[1])
            builder_id = int(columns[2])
            if len(transaction_data) > 0:
                row = [block_id, block_bid, builder_id, transaction_data]
                data.append(row)
        else:  # This is a transaction row
            transaction_id = int(columns[3])
            transaction_gas = float(columns[4])
            transaction_mev = float(columns[5])
            transaction_row = [transaction_id, transaction_gas, transaction_mev]
            transaction_data.append(transaction_row)

# Convert the list of data into a DataFrame
df = pd.DataFrame(data, columns=['Block ID', 'Block Bid', 'Builder ID', 'Transaction ID', 'Transaction GAS', 'Transaction MEV'])

print(df.columns)

Labels = df.columns

fig, axes = plt.subplots(nrows=3, ncols=2)

df['Bid Value'].plot(ax=axes[0,0], label='Bid Value');
df['Bid Value'].rolling(window=10).mean().plot(ax=axes[0,0], label='Moving Average over 10 blocks')
axes[0,0].set_title('Winning Bids')
axes[0,0].legend()

df['Reward'].plot(ax=axes[1,0], label='Reward');
df['Reward'].rolling(window=10).mean().plot(ax=axes[1,0], label='Moving Average over 10 blocks')
axes[1,0].set_title('Reward')
axes[1,0].legend()

builder_freq = df['Builder ID'].value_counts()
builder_freq.plot(kind='bar', ax=axes[2,0]); axes[2,0].set_title('Builder Winning Frequency')

df['Bid Percentage'] = (df['Bid Value'] / df['Block Value']) * 100

# New plot: Bid value as a percentage of block value
df['Bid Percentage'].plot(ax=axes[0,1])
axes[0,1].set_title('Bid Value as a Percentage of Block Value')

# New plot: Cumulative reward of each builder
for builder_id in df['Builder ID'].unique():
    builder_rewards = df[df['Builder ID'] == builder_id]['Reward'].cumsum()
    builder_rewards.plot(ax=axes[1,1], label=f'Builder {builder_id}')

axes[1,1].set_title('Cumulative Reward of Each Builder')
axes[1,1].legend()

plt.tight_layout()
plt.show()
