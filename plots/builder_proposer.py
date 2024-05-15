import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    array = array.flatten().astype(float) 
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 0.0000001
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def process_file(file, is_pos=True):
    try:
        df = pd.read_csv(file)
        
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_entity = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))
        
        df['mev_entity'] = mev_entity
        df['characteristic'] = characteristic
        df['reward'] = df['gas_captured'] + df['mev_captured']
        return df, mev_entity, characteristic
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame(), None, None
    
def plot_heatmap(data, title, save_path):
    pivot = data.pivot("MEV Entity", "Characteristic", "Gini Coefficient")

    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, cmap="YlGnBu", cbar_kws={'label': 'Gini Coefficient'}, annot=False)
    plt.title(title)
    plt.xlabel('Characteristic')
    plt.ylabel('MEV Entity')

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.show()
    plt.close()

if __name__ == '__main__':
    pos_csv_path = "/Users/Tammy/Downloads/pos_vary_mev_and_characteristic"
    pbs_csv_path = "/Users/Tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"  
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    pos_files = os.listdir(pos_csv_path)
    pbs_files = os.listdir(pbs_csv_path)
    
    pos_gini_data = []
    for file_name in pos_files:
        file_path = os.path.join(pos_csv_path, file_name)
        df, mev_validators, characteristic = process_file(file_path, is_pos=True)
        if df is not None and not df.empty:
            gini_coeff = gini(df['reward'].values)
            pos_gini_data.append((mev_validators, characteristic, gini_coeff))
        else:
            print(f"No data to plot for {file_name}.")

    pbs_gini_data = []
    for file_name in pbs_files:
        file_path = os.path.join(pbs_csv_path, file_name)
        df, mev_builders, characteristic = process_file(file_path, is_pos=False)
        if df is not None and not df.empty:
            gini_coeff = gini(df['reward'].values)
            pbs_gini_data.append((mev_builders, characteristic, gini_coeff))
        else:
            print(f"No data to plot for {file_name}.")

    pos_gini_df = pd.DataFrame(pos_gini_data, columns=['MEV Entity', 'Characteristic', 'Gini Coefficient'])
    pbs_gini_df = pd.DataFrame(pbs_gini_data, columns=['MEV Entity', 'Characteristic', 'Gini Coefficient'])

    plot_heatmap(pos_gini_df, 'Gini Coefficient for PoS', os.path.join(save_dir, 'gini_coefficient_heatmap_pos.png'))
    plot_heatmap(pbs_gini_df, 'Gini Coefficient for PBS', os.path.join(save_dir, 'gini_coefficient_heatmap_pbs.png'))
