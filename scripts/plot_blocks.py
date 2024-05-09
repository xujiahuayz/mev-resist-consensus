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

# Plotting the box plot for rewards of Non-MEV vs MEV builders
plt.figure(figsize=(10, 6))
sns.boxplot(data=pbs_blocks, x='Builder Type', y='Reward')
plt.title('Distribution of Rewards for Non-MEV and MEV Builders')
plt.ylabel('Reward')
plt.xlabel('Builder Type')
plt.show()

