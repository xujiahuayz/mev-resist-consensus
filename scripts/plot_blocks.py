'''Place holder for plotting blocks data'''

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style="ticks", palette="pastel")
# sns.set_theme(style="whitegrid")

pos_blocks = pd.read_csv('/Users/tammy/Downloads/posBlocks.csv')
pbs_blocks = pd.read_csv('/Users/tammy/Downloads/pbsBlocks.csv')

non_mev_builders = [1, 2, 3, 4, 5]
mev_builders = [10, 30, 50, 70, 90]

pbs_blocks['Builder Type'] = pbs_blocks['Builder ID'].apply(lambda x: 'MEV' if x in mev_builders else 'Non-MEV')
pbs_blocks['Reward Type'] = pbs_blocks.apply(lambda row: 'Proposer' if row['Builder ID'] == row['Proposer ID'] else ('MEV' if row['Builder ID'] in mev_builders else 'Non-MEV'), axis=1)
pbs_blocks['Reward Type'] = pbs_blocks['Reward Type'].astype('category')
pbs_blocks['Calculated Reward'] = pbs_blocks.apply(lambda row: row['Winning Bid Value'] if row['Reward Type'] == 'Proposer' else row['Reward'], axis=1)



def plot_box_mev():
    # Plotting the box plot for rewards of Non-MEV vs MEV builders
    plt.figure(figsize=(6, 6))
    sns.boxplot(data=pbs_blocks, x='Builder Type', y='Reward')
    plt.title('Distribution of Rewards for Non-MEV and MEV Builders')
    plt.ylabel('Reward')
    plt.xlabel('Builder Type')
    plt.show()

def plot_reward_time():
  # Group and calculate cumulative rewards by block number and reward type
    reward_totals = pbs_blocks.groupby(['Block Number', 'Reward Type'])['Calculated Reward'].sum().unstack().fillna(0).cumsum()

    # Reset index to convert back to a DataFrame
    reward_totals.reset_index(inplace=True)

    # Plotting the cumulative rewards
    plt.figure(figsize=(14, 8))
    for column in reward_totals.columns[1:]:  # Skip 'Block Number' which is index 0
        sns.lineplot(x=reward_totals['Block Number'], y=reward_totals[column], label=column)
    plt.title('Cumulative Rewards Over Block Number for MEV Builders, Non-MEV Builders, and Proposers')
    plt.xlabel('Block Number')
    plt.ylabel('Cumulative Reward')
    plt.legend(title='Builder Type')
    plt.grid(True)
    plt.show()

def plot_reward_time_stacked():
    # Plot the normalized data as a 100% stacked area plot
    reward_totals = pbs_blocks.groupby(['Block Number', 'Reward Type'])['Calculated Reward'].sum().unstack(fill_value=0).cumsum()
    reward_totals_percent = reward_totals.div(reward_totals.sum(axis=1), axis=0)

    plt.figure(figsize=(14, 8))
    reward_totals_percent.plot(kind='area', stacked=True)
    plt.title('100% Cumulative Rewards Over Block Number by Builder Type')
    plt.xlabel('Block Number')
    plt.ylabel('Percentage of Total Cumulative Reward')
    plt.legend(title='Builder Type')
    plt.ylim(0, 1)
    plt.grid(True)
    plt.show()

def plot_inclusion_time():
    # the time it takes for a mev transaction to be included in a block (also do it for non mev)
    pass

def plot_inclusion_rate():
    # plot what percentage of mev attackable transaction are included and attacked
    pass

def plot_bid_reward():
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=pbs_blocks, x='Winning Bid Value', y='Reward', hue='Builder Type', style='Builder Type',
                palette=['#FF6347', '#4682B4'], s=60, alpha=0.5, edgecolor='none')
    plt.title('Scatter Plot of Bid vs Reward by Builder Type')
    plt.xlabel('Winning Bid Value')
    plt.ylabel('Reward')
    plt.legend(title='Builder Type')
    plt.grid(True)
    plt.show()

def plot_bid_block():
    # plot the winning bid value vs the block value
    pbs_blocks['Winning Bid Percentage'] = (pbs_blocks['Winning Bid Value'] / pbs_blocks['Winning Block Value']) * 100

    plt.figure(figsize=(14, 8))

    # Plotting the histogram of the Winning Bid Percentage
    sns.histplot(pbs_blocks['Winning Bid Percentage'], bins=30, kde=False)

    plt.title('Distribution of Winning Bid Percentage of Block Value')
    plt.xlabel('Winning Bid Percentage (%)')
    plt.ylabel('Number of Blocks')
    plt.grid(True)
    plt.show()

def plot_3d_rewards():
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')



    X, Y = np.meshgrid(np.unique(x), np.unique(y))
    Z = np.array([z[(x == xval) & (y == yval)].mean() for xval, yval in zip(np.ravel(X), np.ravel(Y))]).reshape(X.shape)

    # Plot the surface
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')

    # Add labels and title
    ax.set_xlabel('Number of Miners')
    ax.set_ylabel('Block Propagation Delay')
    ax.set_zlabel('Calculated Reward')
    ax.set_title('3D Surface Plot of Rewards vs Miners and Block Propagation Delay')

    # Add a color bar which maps values to colors
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

    plt.show()


if __name__ == '__main__':
    # plot_box_mev()
    # plot_reward_time()
    # plot_reward_time_stacked()
    # plot_bid_reward()
    # plot_bid_block()
    # plot_inclusion_time()
    # plot_inclusion_rate()
    plot_3d_rewards()
