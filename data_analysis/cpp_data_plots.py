import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('pbs_c/cmake-build-debug/blockchain_data.csv')

print(df.columns)

Labels = df.columns

fig, axes = plt.subplots(nrows=3, ncols=2)

df['Bid Value'].plot(ax=axes[0,0], label='Bid Value');
df['Bid Value'].rolling(window=10).mean().plot(ax=axes[0,0], label='Moving Average over 10 blocks')
axes[0,0].set_title('Winning Bids')
axes[0,0].legend()

df['Reward'].plot(ax=axes[1,0], label='Reward');
df['Reward'].rolling(window=10).mean().plot(ax=axes[1,0], label='Moving Average over 10 blocks')
axes[1,0].set_title('Reward')
axes[1,0].legend()

builder_freq = df['Builder ID'].value_counts()
builder_freq.plot(kind='bar', ax=axes[2,0]); axes[2,0].set_title('Builder Winning Frequency')

df['Bid Percentage'] = (df['Bid Value'] / df['Block Value']) * 100

# New plot: Bid value as a percentage of block value
df['Bid Percentage'].plot(ax=axes[0,1])
axes[0,1].set_title('Bid Value as a Percentage of Block Value')

# New plot: Cumulative reward of each builder
for builder_id in df['Builder ID'].unique():
    builder_rewards = df[df['Builder ID'] == builder_id]['Reward'].cumsum()
    builder_rewards.plot(ax=axes[1,1], label=f'Builder {builder_id}')

axes[1,1].set_title('Cumulative Reward of Each Builder')
axes[1,1].legend()

plt.tight_layout()
plt.show()
