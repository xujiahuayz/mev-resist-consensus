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

fig, axs = plt.subplots(1, 1)

# Plot 1: Total Block Bid for Each Block
block_bids = df['Block Bid'].tolist()
axs.plot(df['Block ID'], block_bids)
axs.set_title('Total Block Bid for Each Block')
axs.set_xlabel('Block ID')
axs.set_ylabel('Total Block Bid')

plt.tight_layout()
plt.show()