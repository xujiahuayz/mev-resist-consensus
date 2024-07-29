import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

# Load block data from the provided CSV format
block_data = pd.read_csv("data/block_data.csv")

# Calculate the total gas fee for each block and the MEV potentials
block_data["total_gas_gwei"] = block_data["total_gas"]
block_data["mev_potential_gwei"] = block_data["total_gas_gwei"] * 0.15  # 15% of total gas as MEV potential

# Sample some realistic data for MEV potentials
num_samples = 1000
mev_potentials = np.random.choice(block_data["mev_potential_gwei"], num_samples, replace=True)

# Plot the distribution of MEV potentials
plt.figure(figsize=(10, 6))
sns.histplot(mev_potentials, bins=50, kde=True, color='blue', alpha=0.6)
plt.axvline(x=np.mean(mev_potentials), color='red', linestyle='--', label=f'Mean: {np.mean(mev_potentials):.2f} Gwei')
plt.title('Distribution of MEV Potentials')
plt.xlabel('MEV Potential (Gwei)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True)
plt.show()

# Print the calculated parameters
print(f"Mean of MEV Potentials: {np.mean(mev_potentials):.2f} Gwei")
print(f"Standard Deviation of MEV Potentials: {np.std(mev_potentials):.2f} Gwei")
