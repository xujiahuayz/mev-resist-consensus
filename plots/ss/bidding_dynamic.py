import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# random.seed(16)

ATTACK_BUILDERS = {f"builder_{i}" for i in range(3)} | {f"builder_{i+5}" for i in range(10)}
NON_ATTACK_BUILDERS = {f"builder_{i+3}" for i in range(2)} | {f"builder_{i+15}" for i in range(5)}

def plot_bid_dynamics(file_path_input, block_number_input):
    output_figure_path = 'figures/ss/bid_dynamics_selected_block.png'
    data = pd.read_csv(file_path_input)
    block_data = data[(data['block_num'] == block_number_input) & (data['bid'] > 0)]
    if block_data.empty:
        print(f"No valid bid data for Block {block_number_input}.")
        return
    block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
    block_data['round_num'] = pd.to_numeric(block_data['round_num'], errors='coerce')
    last_round = block_data['round_num'].max()
    last_round_data = block_data[block_data['round_num'] == last_round]
    winning_builder = last_round_data.loc[last_round_data['bid'].idxmax()]['builder_id']
    is_winning_attacker = winning_builder in ATTACK_BUILDERS
    def get_color(builder_id):
        if builder_id == winning_builder:
            return 'red'
        if builder_id in ATTACK_BUILDERS:
            return 'lightblue'
        return 'orange'
    unique_builders = block_data['builder_id'].unique()
    if len(unique_builders) > 15:
        selected_builders = np.random.choice([b for b in unique_builders if b != winning_builder], size=7, replace=False)
        selected_builders = np.append(selected_builders, winning_builder)
    else:
        selected_builders = unique_builders
    plt.figure(figsize=(12, 8))
    for builder_id in selected_builders:
        builder_data = block_data[block_data['builder_id'] == builder_id]
        color = get_color(builder_id)
        sns.lineplot(
            data=builder_data,
            x='round_num',
            y='bid',
            marker='o',
            linewidth=1.5,
            color=color,
            markersize=4,
            label=f"{builder_id} ({'Winning Attacker' if is_winning_attacker else 'Winning Non-Attacker'})" if builder_id == winning_builder else ""
        )
    legend_labels = {
        r"$\tau_{B_i} = \mathtt{attack},\ B_w$": "red" if not is_winning_attacker else None,
        r"$\tau_{B_i} = \mathtt{benign},\ B_w$": "red" if is_winning_attacker else None,
        r"$\tau_{B_i} = \mathtt{attack}$": "orange",
        r"$\tau_{B_i} = \mathtt{benign}$": "lightblue"
    }
    legend_handles = [plt.Line2D([0], [0], color=color, lw=4, label=label) for label, color in legend_labels.items()]
    plt.legend(handles=legend_handles, loc="lower right", fontsize=24)
    plt.xlabel(r"Round $t$", fontsize=26)
    plt.ylabel('Bid Value $b_{i,t}$ (gwei)', fontsize=26)
    plt.tick_params(axis='both', which='major', labelsize=24)
    plt.gca().yaxis.get_offset_text().set_fontsize(24)
    plt.tight_layout()
    plt.savefig(output_figure_path)
    plt.show()

def analyze_data(file_path_input):
    data = pd.read_csv(file_path_input)
    total_blocks = data['block_num'].nunique()
    match_count = 0
    bid_block_value_ratios = []
    bid_second_highest_block_value_ratios = []
    for block_number in data['block_num'].unique():
        block_data = data[data['block_num'] == block_number]
        block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
        block_data['block_value'] = pd.to_numeric(block_data['block_value'], errors='coerce')
        highest_bid_row = block_data.loc[block_data['bid'].idxmax()]
        highest_bid_id = highest_bid_row['builder_id']
        highest_bid = highest_bid_row['bid']
        sorted_block_values = block_data.sort_values(by='block_value', ascending=False)
        highest_block_value = sorted_block_values.iloc[0]['block_value']
        second_highest_block_value = sorted_block_values.iloc[1]['block_value'] if len(sorted_block_values) > 1 else 0
        highest_block_value_id = sorted_block_values.iloc[0]['builder_id']
        if highest_bid_id == highest_block_value_id:
            match_count += 1
        if highest_block_value > 0:
            bid_block_value_ratio = (highest_bid / highest_block_value) * 100
            bid_block_value_ratios.append(bid_block_value_ratio)
        if second_highest_block_value > 0:
            bid_second_highest_block_value_ratio = (highest_bid / second_highest_block_value) * 100
            bid_second_highest_block_value_ratios.append(bid_second_highest_block_value_ratio)
    match_percentage = (match_count / total_blocks) * 100
    avg_bid_block_value_ratio = np.mean(bid_block_value_ratios) if bid_block_value_ratios else 0
    avg_bid_second_highest_block_value_ratio = np.mean(bid_second_highest_block_value_ratios) if bid_second_highest_block_value_ratios else 0
    return match_percentage, avg_bid_block_value_ratio, avg_bid_second_highest_block_value_ratio

def plot_block_value_dynamics(file_path_input, block_number_input):
    output_figure_path = 'figures/ss/block_value_dynamics_selected_block.png'
    data = pd.read_csv(file_path_input)
    block_data = data[data['block_num'] == block_number_input]
    if block_data.empty:
        print(f"No valid block value data for Block {block_number_input}.")
        return
    block_data['block_value'] = pd.to_numeric(block_data['block_value'], errors='coerce')
    block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
    block_data['round_num'] = pd.to_numeric(block_data['round_num'], errors='coerce')
    winning_builder = block_data.loc[block_data['bid'].idxmax()]['builder_id']
    is_winning_attacker = winning_builder in ATTACK_BUILDERS
    def get_color(builder_id):
        if builder_id == winning_builder:
            return 'red'
        if builder_id in ATTACK_BUILDERS:
            return 'lightblue'
        return 'orange'
    unique_builders = block_data['builder_id'].unique()
    if len(unique_builders) > 15:
        selected_builders = np.random.choice([b for b in unique_builders if b != winning_builder], size=7, replace=False)
        selected_builders = np.append(selected_builders, winning_builder)
    else:
        selected_builders = unique_builders
    plt.figure(figsize=(12, 8))
    for builder_id in selected_builders:
        builder_data = block_data[block_data['builder_id'] == builder_id]
        color = get_color(builder_id)
        sns.lineplot(
            data=builder_data,
            x='round_num',
            y='block_value',
            marker='o',
            linewidth=1.5,
            color=color,
            markersize=4,
            label=f"{builder_id} ({'Winning Attacker' if is_winning_attacker else 'Winning Non-Attacker'})" if builder_id == winning_builder else ""
        )
    legend_labels = {
        r"$\tau_{B_i} = \mathtt{attack},\ B_w$": "red" if not is_winning_attacker else None,
        r"$\tau_{B_i} = \mathtt{attack}$": "orange",
        r"$\tau_{B_i} = \mathtt{benign}$": "lightblue"
    }
    legend_handles = [plt.Line2D([0], [0], color=color, lw=4, label=label) for label, color in legend_labels.items()]
    plt.legend(handles=legend_handles, loc="lower right", fontsize=24)
    plt.xlabel(r"Round $t$", fontsize=26)
    plt.ylabel('Block Value $v_{i,t}$ (gwei)', fontsize=26)
    plt.tick_params(axis='both', which='major', labelsize=24)
    plt.gca().yaxis.get_offset_text().set_fontsize(24)
    plt.tight_layout()
    plt.savefig(output_figure_path)
    plt.show()

if __name__ == "__main__":
    FILE_PATH = 'data/same_seed/bid_builder10.csv'
    BLOCK_NUMBER = 1

    plot_bid_dynamics(FILE_PATH, BLOCK_NUMBER)
    plot_block_value_dynamics(FILE_PATH, BLOCK_NUMBER)

    match_percentage, avg_bid_block_value_ratio, avg_bid_second_highest_block_value_ratio = analyze_data(FILE_PATH)
    print(f"The winning bid has the highest block value {match_percentage:.2f}% of the time.")
    print(f"On average, the winning bid is {avg_bid_block_value_ratio:.2f}% of the highest block value.")
    print(f"On average, the winning bid is {avg_bid_second_highest_block_value_ratio:.2f}% of the second-highest block value.")
