import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def process_file(file):
    try:
        df = pd.read_csv(file)
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))
        
        df['mev_builders'] = mev_builders
        df['characteristic'] = characteristic
        df['total_block_value'] = df['gas_captured'] + df['mev_captured']
        df['reward'] = df['gas_captured'] + df['mev_captured'] - df['block_bid']
        
        return df, mev_builders, characteristic
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame(), None, None

def plot_reward_distribution(ax, data, mev_builders, characteristic):
    data['log_reward'] = np.log1p(data['reward'])
    
    reward_data = pd.DataFrame({
        'Log Reward': data['log_reward'],
        'Builder Type': np.where(data['builder_type'] == 1, 'MEV', 'Non-MEV')
    })
    
    sns.set(style="whitegrid")
    sns.violinplot(ax=ax, y='Builder Type', x='Log Reward', data=reward_data, palette='pastel', order=['Non-MEV', 'MEV'])
    
    medians = reward_data.groupby('Builder Type')['Log Reward'].median().reindex(['Non-MEV', 'MEV'])
    for i, median in enumerate(medians):
        ax.plot([median, median], [i - 0.05, i + 0.05], color='white', linewidth=2.5)
    
    title = f'MEV builders number = {mev_builders},\nLatency characteristics = {characteristic}'
    ax.set_title(title, fontsize=20)
    ax.set_ylabel('Builder Type', fontsize=18)
    ax.set_xlabel('Log Reward', fontsize=18)
    ax.tick_params(axis='both', which='major', labelsize=16)

if __name__ == '__main__':
    csv_path = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    representative_files = [
        "mev_builders=1characteristic=0.2.csv",
        "mev_builders=1characteristic=1.csv",
        "mev_builders=25characteristic=0.2.csv",
        "mev_builders=25characteristic=1.csv",
        "mev_builders=49characteristic=0.2.csv",
        "mev_builders=49characteristic=1.csv"
    ]
    
    fig, axes = plt.subplots(3, 2, figsize=(15, 22))
    axes = axes.flatten()
    
    sns.set(style="whitegrid")
    
    for i, file_name in enumerate(representative_files):
        file_path = os.path.join(csv_path, file_name)
        df, mev_builders, characteristic = process_file(file_path)
        if not df.empty:
            plot_reward_distribution(axes[i], df, mev_builders, characteristic)
        else:
            print(f"No data to plot for {file_name}.")
    
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.05)
    plt.savefig(os.path.join(save_dir, 'reward_distribution_3x3_horizontal.png'), bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.show()
    plt.close()
