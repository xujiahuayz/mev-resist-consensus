import pandas as pd
from os import path
# import matplotlib as plt
import seaborn as sns

sns.set_theme(style="ticks", palette="pastel")

df1 = pd.read_csv('/Users/tammy/Downloads/posBlocks.csv')
df2 = pd.read_csv('/Users/tammy/Downloads/pbsBlocks.csv')

print(df1.head())
print(df2.head())



