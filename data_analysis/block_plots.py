import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Load the data
df = pd.read_csv('pbs_c/cmake-build-debug/blocks.csv')

# Analyze the data
print(df.describe())

fig, axs = plt.subplots(3, 2)

# Plot 1: cumulative total builder rewards vs total proposar rewards
df['Cumulative Reward'] = df['Reward'].cumsum()
df['Cumulative Winning Bid Value'] = df['Winning Bid Value'].cumsum()
axs[0, 0].plot(df['Block Number'], df['Cumulative Reward'], label='Cumulative Reward to Builders')
axs[0, 0].plot(df['Block Number'], df['Cumulative Winning Bid Value'], label='Cumulative Reward to Proposers')
axs[0, 0].set_title('Builders VS Proposers')
axs[0, 0].set_xlabel('Block Number')
axs[0, 0].set_ylabel('Units')
axs[0, 0].legend(loc='best',prop={'size': 7})

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
    axs[0, 1].plot(builder_df['Block Number'], cumulative_rewards, label=f'{get_builder_type(builder_id)} {adjust_builder_id(builder_id)}')
for proposer_id in proposer_ids:
    proposer_df = df[df['Proposer ID'] == proposer_id]
    cumulative_rewards = np.cumsum([reward for reward, id in zip(df['Winning Bid Value'], df['Proposer ID']) if id == proposer_id])
    axs[0, 1].plot(proposer_df['Block Number'], cumulative_rewards, label=f'Proposer {proposer_id-min_proposer_id+1}')
axs[0, 1].set_title('Cumulative Reward for Each Builder')
axs[0, 1].set_xlabel('Block Number')
axs[0, 1].set_ylabel('Cumulative Reward')
axs[0, 1].legend(loc='best',prop={'size': 7})

# Plot 3: Winning block values and maximum block values of all builders
max_builder_values = df.groupby('Block Number')[[f'Builder ID {builder_id} Block Value' for builder_id in builder_ids]].max().max(axis=1)
axs[1, 0].plot(df['Block Number'], df['Winning Block Value'], label='Winning Block Value')
axs[1, 0].plot(max_builder_values.index, max_builder_values.values, label='Max Builder Block Value', linestyle=':',color='red')
axs[1, 0].set_title('Block Values')
axs[1, 0].set_xlabel('Block Number')
axs[1, 0].set_ylabel('Block Value')
df['Max Builder Block Value'] = df[[f'Builder ID {builder_id} Block Value' for builder_id in builder_ids]].max(axis=1)
df['MaxEqualWinning'] = np.isclose(df['Winning Block Value'], df['Max Builder Block Value'], atol=1e-1)
percentage = (1.0 - df['MaxEqualWinning'].mean()) * 100
#axs[1, 0].fill_between(df['Block Number'], df['Winning Block Value'], max_builder_values, where=(df['MaxNotEqualWinning']), color='yellow', alpha=0.5)
axs[1, 0].legend(loc='best', prop={'size': 7})
text = f'{percentage:.2f}% of blocks are won by builders who do not have the highest block value'
wrapped_text = textwrap.fill(text, width=40)  # Adjust the width as needed
axs[1, 0].text(0.10, 0.95, wrapped_text, transform=axs[1, 0].transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.5),fontsize=7)

# Plot 4: Block Value Distribution
all_builder_bids = pd.concat([df[f'Builder ID {builder_id} Bid'] for builder_id in builder_ids])
ax2 = axs[1, 1].twinx()
ax2.hist(all_builder_bids, bins=30, alpha=0.5, label='All Builder Bids',color="green")
axs[1, 1].hist(df['Winning Block Value'], bins=30, alpha=0.5, label='Winning Block Value')
axs[1,1].hist(df['Winning Bid Value'], bins=30, alpha=0.5, label='Winning Bid Value')
ax2.set_ylabel('Frequency (All Builder Bids)')
axs[1, 1].set_title('Block Value Distribution')
axs[1, 1].set_xlabel('Value')
axs[1, 1].set_ylabel('Frequency')
lines, labels = axs[1, 1].get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc='best')

# Plot 5: Histogram of Proposer and Builder Rewards
axs[2, 0].hist(df['Winning Bid Value'], bins=30, alpha=0.5, label='Proposer Rewards', color='blue')
axs[2, 0].hist(df['Reward'], bins=30, alpha=0.5, label='Builder Rewards', color='green')
axs[2, 0].set_title('Histogram of Proposer and Builder Rewards')
axs[2, 0].set_xlabel('Reward')
axs[2, 0].set_ylabel('Frequency')
axs[2, 0].legend(loc='best')

# Plot 6: Scatter Plot
axs[2, 1].scatter(df['Winning Block Value'], df['Reward'], marker=".", s=3, label='Builder Rewards')
axs[2, 1].scatter(df['Winning Block Value'], df['Winning Bid Value'], marker=".", s=3, label='Proposer Rewards')
axs[2, 1].set_prop_cycle(None)
coefficients = np.polyfit(df['Winning Block Value'], df['Reward'], 2)
x_values = np.linspace(df['Winning Block Value'].min(), df['Winning Block Value'].max(), 100)
y_values = np.polyval(coefficients, x_values)
axs[2, 1].plot(x_values, y_values, label='Best Fit - Builder Rewards')
coefficients = np.polyfit(df['Winning Block Value'], df['Winning Bid Value'], 2)
x_values = np.linspace(df['Winning Block Value'].min(), df['Winning Block Value'].max(), 100)
y_values = np.polyval(coefficients, x_values)
axs[2, 1].plot(x_values, y_values, label='Best Fit - Proposer Rewards')
axs[2, 1].set_title('Scatter Plot')
axs[2, 1].set_xlabel('Block Value')
axs[2, 1].set_ylabel('Reward')
axs[2, 1].legend(loc='best',prop={'size': 7})

plt.tight_layout()
plt.show()