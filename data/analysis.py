import pandas as pd


df1 = pd.read_csv('/data/pbsBlocks.csv')
df2 = pd.read_csv('posBlocks.csv')

print(df1.head())
print(df2.head())
