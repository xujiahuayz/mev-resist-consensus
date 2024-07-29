import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

# Load the collected data
data_dir = 'data/fetch'
all_gas_fees = []

# Function to extract gas fees from transactions
def extract_gas_fees(transactions):
    fees = []
    for txn in transactions:
        if 'gas_fee_gwei' in txn:
            fees.append(float(txn['gas_fee_gwei']))
        elif 'gas_fee_wei' in txn:
            gas_fee_gwei = float(txn['gas_fee_wei']) / 1e9  # Convert Wei to Gwei
            fees.append(gas_fee_gwei)
    return fees

for file in os.listdir(data_dir):
    if file.endswith('.json'):
        with open(os.path.join(data_dir, file), 'r') as f:
            block_data = json.load(f)
            if 'transactions' in block_data:
                gas_fees = extract_gas_fees(block_data['transactions'])
                all_gas_fees.extend(gas_fees)
            else:
                print(f"Key 'transactions' not found in file: {file}")

# Check if all_gas_fees is not empty before proceeding
if not all_gas_fees:
    raise ValueError("No gas fees data found in the JSON files.")

# Convert to numpy array for analysis
gas_fees_np = np.array(all_gas_fees)

# Function to round to significant figures
def round_to_sig_figs(num, sig_figs):
    if num == 0:
        return 0
    return round(num, sig_figs - int(np.floor(np.log10(abs(num)))) - 1)

# Round the gas fees to 2 significant figures
rounded_gas_fees = np.array([round_to_sig_figs(fee, 2) for fee in gas_fees_np])

# Sample 100 gas fees (or fewer if less than 100 are available)
sample_size = min(100, len(rounded_gas_fees))
sample_gas_fees = np.random.choice(rounded_gas_fees, sample_size, replace=False)

print(f"Sample Gas Fees (rounded to 2 significant figures): {sample_gas_fees.tolist()}")

# Calculate potential MEV values based on the sample gas fees using a normal distribution
mean_percentage = 0.1  # Mean is 10% of the gas fee
std_dev_percentage = 0.07  # Standard deviation is 7% of the gas fee

# Generate MEV potentials
sample_mev_potentials = np.maximum(0, np.random.normal(sample_gas_fees * mean_percentage, sample_gas_fees * std_dev_percentage))

print(f"Sample MEV Potentials: {sample_mev_potentials.tolist()}")

# Plot the distribution of sample gas fees and MEV potentials
plt.figure(figsize=(14, 7))

# # Plot gas fees
# plt.subplot(1, 2, 1)
# sns.histplot(sample_gas_fees, bins=30, kde=True, color='blue', alpha=0.6)
# plt.title('Distribution of Sample Gas Fees')
# plt.xlabel('Gas Fee (Gwei)')
# plt.ylabel('Frequency')

# # Plot MEV potentials
# plt.subplot(1, 2, 2)
# sns.histplot(sample_mev_potentials, bins=30, kde=True, color='green', alpha=0.6)
# plt.title('Distribution of Sample MEV Potentials')
# plt.xlabel('MEV Potential (Gwei)')
# plt.ylabel('Frequency')

plt.tight_layout()
plt.show()
