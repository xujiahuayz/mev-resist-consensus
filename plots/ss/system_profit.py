import os
import csv
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import ticker

def calculate_mev_from_transactions(file_path):
    """
    Calculate MEV distribution and total MEV profit from a transaction CSV file.
    """
    required_fields = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}
    total_mev = 0
    gas_fee = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not required_fields.issubset(reader.fieldnames):
            print(f"Skipping file {file_path} due to missing fields.")
            return 0, 0

        transactions = list(reader)

        for tx in transactions:
            try:
                mev_potential = int(tx['mev_potential'].strip())
                gas_fee += int(tx.get('gas_fee', 0))  # Include gas fee calculation
                if mev_potential > 0:
                    total_mev += mev_potential
            except (ValueError, KeyError):
                continue

    return total_mev, gas_fee

def load_total_profit_from_csv(data_folder, system_type):
    """
    Load total profits (MEV + gas fees) from all CSV files in the specified folder.
    Aggregate duplicates by summing values for each (Users, Builders/Validators) pair.
    """
    profit_data = []

    for filename in os.listdir(data_folder):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_folder, filename)
            try:
                parts = filename.split("_")
                if system_type == "pbs":
                    count_field = "builders"
                elif system_type == "pos":
                    count_field = "validators"
                else:
                    raise ValueError("Invalid system type specified: use 'pbs' or 'pos'.")

                user_count = int(parts[-1].split(".")[0].replace("users", ""))
                entity_count = int(parts[-2].replace(count_field, ""))

                # Calculate MEV and gas fees
                total_mev, gas_fee = calculate_mev_from_transactions(file_path)
                total_profit = total_mev + gas_fee
                profit_data.append((user_count, entity_count, total_profit))
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    # Convert profit data to a DataFrame
    df = pd.DataFrame(profit_data, columns=['Users', 'Entities', 'Total Profit'])

    # Aggregate duplicate (Users, Entities) entries by summing their Total Profit
    df = df.groupby(['Users', 'Entities'], as_index=False).sum()

    # Pivot the DataFrame
    return df.pivot(index='Users', columns='Entities', values='Total Profit')


def calculate_profit_difference(pbs_folder_path, pos_folder_path):
    """
    Calculate the profit difference (PBS - PoS) for all configurations.
    """
    pbs_profit_data = load_total_profit_from_csv(pbs_folder_path, system_type="pbs")
    pos_profit_data = load_total_profit_from_csv(pos_folder_path, system_type="pos")
    profit_difference_data = pbs_profit_data.subtract(pos_profit_data, fill_value=0)
    return pbs_profit_data, pos_profit_data, profit_difference_data

def plot_heatmap(results, title, vmin_val, vmax_val, output_folder_path, x_label):
    """
    Plot a heatmap of inversion counts for each user and builder/validator configuration with consistent formatting.
    """
    df = pd.DataFrame(results).T.sort_index(ascending=False).sort_index(axis=1)

    # Create the heatmap
    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(
        df,
        annot=False,
        fmt=".0f",
        cmap="YlGnBu",
        cbar_kws={'label': "Inversion Count"},
        vmin=vmin_val,
        vmax=vmax_val
    )

    # Axis labels
    ax.set_xlabel(x_label, fontsize=18, labelpad=15)
    ax.set_ylabel("Percentage of Attacking Users", fontsize=18, labelpad=15)

    # Set tick labels
    ax.set_xticks(range(len(df.columns)))
    ax.set_xticklabels([f"{x}%" for x in df.columns], fontsize=14)
    ax.set_yticks(range(len(df.index)))
    ax.set_yticklabels([f"{y}%" for y in df.index], fontsize=14)

    # Reverse the y-axis to start with the highest percentage at the top
    ax.invert_yaxis()

    # Customize the color bar
    cbar = ax.collections[0].colorbar
    cbar.set_label("Inversion Count", size=16, labelpad=10)
    cbar.ax.tick_params(labelsize=14)

    # Format the color bar tick labels for better readability
    cbar.formatter = ticker.FuncFormatter(lambda x, _: f'{int(x / 1e6):,}M')
    cbar.update_ticks()

    # Add the title
    plt.title(title, fontsize=20, pad=20)

    # Save the heatmap
    output_path = os.path.join(output_folder_path, f"{title.replace(' ', '_').lower()}.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to {output_path}")

if __name__ == "__main__":
    # Define input and output folders
    PBS_FOLDER = 'data/same_seed/pbs_visible80'
    POS_FOLDER = 'data/same_seed/pos_visible80'
    OUTPUT_FOLDER = 'figures/ss'
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Calculate profit differences
    pbs_profit_data, pos_profit_data, profit_difference_data = calculate_profit_difference(PBS_FOLDER, POS_FOLDER)

    # Save profit data for checking
    pbs_profit_data.to_csv(os.path.join(OUTPUT_FOLDER, "pbs_profit.csv"))
    pos_profit_data.to_csv(os.path.join(OUTPUT_FOLDER, "pos_profit.csv"))
    profit_difference_data.to_csv(os.path.join(OUTPUT_FOLDER, "profit_difference.csv"))

    # Determine vmin and vmax for heatmap color scale
    vmin_val = profit_difference_data.min().min()
    vmax_val = profit_difference_data.max().max()

    # Plot heatmap
    heatmap_path = os.path.join(OUTPUT_FOLDER, "profit_difference_heatmap.png")
    plot_heatmap(profit_difference_data, "PBS-PoS Profit Difference Heatmap", vmin_val, vmax_val, OUTPUT_FOLDER, "Percentage of Attacking Entities")
