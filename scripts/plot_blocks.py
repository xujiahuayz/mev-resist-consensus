'''Place holder for plotting blocks data'''

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks", palette="pastel")

pos_blocks = pd.read_csv('/Users/tammy/Downloads/posBlocks.csv')
pbs_blocks = pd.read_csv('/Users/tammy/Downloads/pbsBlocks.csv')


non_mev_builders = [1, 2, 3, 4, 5]
mev_builders = [10, 30, 50, 70, 90]

pbs_blocks['Builder Type'] = pbs_blocks['Builder ID'].apply(lambda x: 'MEV' if x in mev_builders else 'Non-MEV')


def plot_box_mev():
    # Plotting the box plot for rewards of Non-MEV vs MEV builders
    plt.figure(figsize=(6, 6))
    sns.boxplot(data=pbs_blocks, x='Builder Type', y='Reward')
    plt.title('Distribution of Rewards for Non-MEV and MEV Builders')
    plt.ylabel('Reward')
    plt.xlabel('Builder Type')
    plt.show()

def plot_reward_time():
    pbs_blocks['Reward Type'] = pbs_blocks['Builder ID'].apply(lambda x: 'MEV' if x in mev_builders else ('Non-MEV' if x in non_mev_builders else 'Other'))

    # Separating proposer's reward calculation
    pbs_blocks['Proposer Reward'] = pbs_blocks.apply(lambda row: row['Winning Bid Value'] if row['Builder ID'] == row['Proposer ID'] else 0, axis=1)

    # Calculating rewards for builders separately from proposers
    pbs_blocks['Builder Reward'] = pbs_blocks.apply(lambda row: row['Reward'] if row['Builder ID'] != row['Proposer ID'] else 0, axis=1)

    # Group and calculate cumulative rewards for proposers
    proposer_rewards = pbs_blocks.groupby('Block Number')['Proposer Reward'].sum().cumsum()

    # Group and calculate cumulative rewards by builder type
    builder_rewards = pbs_blocks.groupby(['Block Number', 'Reward Type'])['Builder Reward'].sum().groupby('Reward Type').cumsum().reset_index()

    # Merging proposer rewards back for plotting
    builder_rewards = builder_rewards.append({'Block Number': proposer_rewards.index, 'Reward Type': 'Proposer', 'Builder Reward': proposer_rewards.values}, ignore_index=True)

    # Plotting
    plt.figure(figsize=(14, 8))
    sns.lineplot(data=builder_rewards, x='Block Number', y='Builder Reward', hue='Reward Type', marker='o', linestyle='-')
    plt.title('Cumulative Rewards Over Block Number for MEV Builders, Non-MEV Builders, and Proposers')
    plt.xlabel('Block Number')
    plt.ylabel('Cumulative Reward')
    plt.legend(title='Builder Type')
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    # plot_box_mev()
    plot_reward_time()