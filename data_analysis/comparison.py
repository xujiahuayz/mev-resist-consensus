import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the data
df = pd.read_csv('/Users/aaryangulia/DSF/PBS/pbs/pbs_c/cmake-build-debug/comparison.csv')

# Calculate total rewards for each builder in PBS and POS
pbs_block_values = df.groupby('PBS Builder ID')['PBS Block Value'].sum()
pbs_bids = df.groupby('PBS Builder ID')['PBS Bid Value'].sum()
pbs_rewards = pbs_block_values - pbs_bids
pbs_proposer_rewards = df.groupby('Proposer ID')['PBS Bid Value'].sum()
combined_pbs_rewards = pbs_rewards.append(pbs_proposer_rewards)

pos_rewards = df.groupby('POS Builder ID')['POS Block Value'].sum()

def gini(x):
    # (Warning: This is a concise implementation, but it is O(n**2)
    # in time and memory, where n = len(x).  *Don't* pass in huge
    # samples!)
    x = x.to_numpy()

    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    # Relative mean absolute difference
    rmad = mad/np.mean(x)
    # Gini coefficient
    g = 0.5 * rmad
    return g

# Calculate Gini coefficient for PBS and POS rewards
gini_pbs_builder = gini(pbs_rewards)
gini_pbs_proposer = gini(pbs_proposer_rewards)
gini_pbs_combined = gini(combined_pbs_rewards)
gini_pos = gini(pos_rewards)

print(f'Gini coefficient for PBS combined rewards: {gini_pbs_combined}')
print(f'Gini coefficient for PBS builder rewards: {gini_pbs_builder}')
print(f'Gini coefficient for PBS proposer rewards: {gini_pbs_proposer}')
print(f'Gini coefficient for POS rewards: {gini_pos}')

def get_participant_type(id):
    if 1 <= id <= 9:
        return 'Normal Builder'
    elif 10 <= id <= 99:
        return 'MEV Builder'
    elif 100 <= id <= 199:  # Assuming proposer IDs are in the range 100-199
        return 'Proposer'
    else:
        return 'Unknown Participant'

def adjust_participant_id(id):
    if get_participant_type(id) == 'MEV Builder':
        return int(int(id) / 20 + 1)
    elif get_participant_type(id) == 'Proposer':
        return id - 100 + 1  # Assuming proposer IDs start from 100
    else:
        return id


# Filter the unique IDs based on the expected ranges for builder and proposer IDs
pbs_builder_ids = [id for id in df['PBS Builder ID'].unique() if 1 <= id <= 99]
pbs_proposer_ids = [id for id in df['Proposer ID'].unique() if 1 <= id <= 99]
pos_builder_ids = [id for id in df['POS Builder ID'].unique() if 1 <= id <= 99]

# Create a list of labels for the x-axis
pbs_builder_labels = [f'{get_participant_type(id)} {adjust_participant_id(id)}' for id in pbs_builder_ids]
pbs_proposer_labels = [f'Proposer {(id-100+1)}' for id in pbs_proposer_ids]
pos_builder_labels = [f'{get_participant_type(id)} {adjust_participant_id(id)}' for id in pos_builder_ids]

# Create a list of labels for the x-axis
combined_pbs_labels = pbs_builder_labels + pbs_proposer_labels

# Create a new figure
plt.figure(figsize=(10, 5))

# Create a subplot for PBS
plt.subplot(1, 2, 1)
combined_pbs_rewards.plot(kind='bar')
plt.title('PBS Mechanism')
plt.xlabel('Participant ID')
plt.xticks(ticks=range(len(combined_pbs_labels)), labels=combined_pbs_labels, rotation=90)  # Set the x-axis labels
plt.ylabel('Total Reward')

# Create a subplot for POS
plt.subplot(1, 2, 2)
pos_rewards.plot(kind='bar')
plt.title('POS Mechanism')
plt.xlabel('Builder ID')
plt.xticks(ticks=range(len(pos_builder_labels)), labels=pos_builder_labels, rotation=90)  # Set the x-axis labels
plt.ylabel('Total Reward')

# Show the plot
plt.tight_layout()
plt.show()