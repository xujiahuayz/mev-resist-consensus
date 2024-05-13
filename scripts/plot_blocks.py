'''Place holder for plotting blocks data'''

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="ticks", palette="pastel")

pos_blocks = pd.read_csv('/Users/tammy/Downloads/posBlocks.csv')
pbs_blocks = pd.read_csv('/Users/tammy/Downloads/pbsBlocks.csv')

pos_tx = pd.read_csv
pbs_tx = pd.read_csv


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
    pbs_blocks['Reward Type'] = pbs_blocks.apply(lambda row: 'Proposer' if row['Builder ID'] == row['Proposer ID'] else ('MEV' if row['Builder ID'] in mev_builders else 'Non-MEV'), axis=1)
    pbs_blocks['Reward Type'] = pbs_blocks['Reward Type'].astype('category')
    pbs_blocks['Calculated Reward'] = pbs_blocks.apply(lambda row: row['Winning Bid Value'] if row['Reward Type'] == 'Proposer' else row['Reward'], axis=1)

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

def plot_win_rate():
    pass

if __name__ == '__main__':
    # plot_box_mev()
    plot_reward_time()