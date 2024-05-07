import pandas as pd
from os import path
import matplotlib as plt
import seaborn as sns

sns.set_theme(style="ticks", palette="pastel")

pos_blocks = pd.read_csv('/Users/tammy/Downloads/posBlocks.csv')
pbs_blocks = pd.read_csv('/Users/tammy/Downloads/pbsBlocks.csv')

print(pos_blocks.head())
print(pbs_blocks.head())


# mev and non mev builder comparison
sns.boxplot(x='Builder Type', y='Profit', data=pbs_blocks)
plt.title('Profit Distribution for MEV vs. Non-MEV Builders')
plt.show()

