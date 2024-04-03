import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Load the data
df = pd.read_csv('pbs_c/cmake-build-debug/posBlocks.csv')

# Analyze the data
print(df.describe())

fig, axs = plt.subplots(1, 1)


df['Cumulative Reward'] = df['Reward'].cumsum()
df['Cumulative Winning Bid Value'] = df['Winning Bid Value'].cumsum()

# Plot 2: Cumulative Reward for Each Node

builder_ids = df['Builder ID'].unique()
proposer_ids = df['Proposer ID'].unique()
min_proposer_id = min(proposer_ids)
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

for builder_id in builder_ids:
    builder_df = df[df['Builder ID'] == builder_id]
    cumulative_rewards = np.cumsum([reward for reward, id in zip(df['Reward'], df['Builder ID']) if id == builder_id])
    axs.plot(builder_df['Block Number'], cumulative_rewards, label=f'{get_builder_type(builder_id)} {adjust_builder_id(builder_id)}')
axs.set_title('Cumulative Reward for Each Builder')
axs.set_xlabel('Block Number')
axs.set_ylabel('Cumulative Reward')
axs.legend(loc='best',prop={'size': 7})

plt.tight_layout()
plt.show()