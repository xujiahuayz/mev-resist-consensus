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
    def get_reward_type(row):
        if row['Builder ID'] in mev_builders:
            return 'MEV'
        elif row['Builder ID'] in non_mev_builders:
            return 'Non-MEV'
        return 'Other'
    
    pbs_blocks['Reward Type'] = pbs_blocks.apply(get_reward_type, axis=1)

    # Calculate rewards, separate proposer's reward using 'Winning Bid Value'
    pbs_blocks['Calculated Reward'] = pbs_blocks.apply(lambda x: x['Winning Bid Value'] if x['Builder ID'] == x['Proposer ID'] else x['Reward'], axis=1)

    # Group and sum rewards by block number and reward type
    reward_totals = pbs_blocks.groupby(['Block Number', 'Reward Type'])['Calculated Reward'].sum().unstack(fill_value=0)

    reward_totals.reset_index(inplace=True)

    # Plot the cumulative rewards over block number for each category
    plt.figure(figsize=(14, 8))
    for column in reward_totals.columns[1:]:  # Skip the first column which is 'Block Number'
        plt.plot(reward_totals['Block Number'], reward_totals[column], label=column, marker='o', linestyle='-')

    plt.title('Cumulative Rewards Over Block Number for MEV Builders, Non-MEV Builders, and Proposers')
    plt.xlabel('Block Number')
    plt.ylabel('Cumulative Reward')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    # plot_box_mev()
    plot_reward_time()