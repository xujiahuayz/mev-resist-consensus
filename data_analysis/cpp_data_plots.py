import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('pbs_c/cmake-build-debug/blockchain_data.csv')

print(df.columns)

Labels = df.columns

fig, axes = plt.subplots(nrows=3, ncols=1)

df['Bid Value'].plot(ax=axes[0], label='Bid Value'); 
df['Bid Value'].rolling(window=10).mean().plot(ax=axes[0], label='Moving Average over 10 blocks')
axes[1].set_title('Winning Bids')
axes[1].legend()

df['Reward'].plot(ax=axes[1], label='Reward'); 
df['Reward'].rolling(window=10).mean().plot(ax=axes[1], label='Moving Average over 10 blocks')
axes[1].set_title('Reward')
axes[1].legend()

builder_freq = df['Builder ID'].value_counts()
builder_freq.plot(kind='bar', ax=axes[2]); axes[2].set_title('Builder Winning Frequency')

plt.tight_layout()
plt.show()
