import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

def load_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def plot_mev_distribution(aggregated_data, user_attack_count, save_path, total_users=50, total_validators=20):
    """Generate and save a plot of MEV distribution without a legend."""
    validator_counts = sorted(int(key) for key in aggregated_data.keys())
    validator_percentages = [100 * count / total_validators for count in validator_counts]
    validator_mev = [aggregated_data[str(count)]["validators_mev"] for count in validator_counts]
    user_mev = [aggregated_data[str(count)]["users_mev"] for count in validator_counts]
    total_mev = [aggregated_data[str(count)]["total_mev"] for count in validator_counts]

    validator_mev_percent = [100 * v / t if t > 0 else 0 for v, t in zip(validator_mev, total_mev)]
    user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 - v - u for v, u in zip(validator_mev_percent, user_mev_percent)]

    plt.figure(figsize=(10, 9))
    palette = sns.color_palette("Blues", 3)
    colors = [palette[2], palette[1], palette[0]]

    plt.stackplot(validator_percentages, user_mev_percent, validator_mev_percent, uncaptured_mev_percent,
                  colors=colors, alpha=0.9)
    

    user_attack_percentage_map = {'0': '0', '12': '33', '24': '67', '50': '100'}
    user_attack_percentage = user_attack_percentage_map.get(str(user_attack_count), 'Check Data')
    plt.xlabel(r"Validators: $\tau_{V_i} = \mathtt{attack}$ (%)", fontsize=36)
    plt.ylabel(r"MEV Profit Captured (%)", fontsize=36)
    plt.title(rf"${user_attack_percentage}\%$ of Users: $\tau_{{U_i}} = \mathtt{{attack}}$", fontsize=36)
    
    plt.xticks(ticks=[0, 25, 50, 75, 100], labels=['0', '25', '50', '75', '100'], fontsize=36)
    plt.yticks(fontsize=36)
    plt.margins(0)
    plt.tight_layout(pad=0)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

def create_legend_figure(save_path):
    """Generate and save a separate figure containing only the legend."""
    plt.figure(figsize=(10, 2))
    palette = sns.color_palette("Blues", 3)
    colors = [palette[2], palette[1], palette[0]]
    
    labels = ["Users'", "Validators'", "Uncaptured"]
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    
    legend = plt.legend(handles, labels, loc='center', fontsize=36, frameon=False)
    plt.axis('off')
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

def main():
    data_folder = '/Users/tammy/pbs/figures/ss'
    output_folder = '/Users/tammy/pbs/figures/ss'
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(data_folder):
        if file_name.endswith('.json') and file_name.startswith('pos_aggregated_data_user_attack'):
            file_path = os.path.join(data_folder, file_name)
            data = load_data(file_path)
            user_attack_count = file_name.split('_')[-1].split('.')[0]
            save_path = os.path.join(output_folder, f"pos_mev_distribution_user_attack_{user_attack_count}.png")
            plot_mev_distribution(data, user_attack_count, save_path, total_users=50)
    
    legend_path = os.path.join(output_folder, "pos_mev_dis_legend.png")
    create_legend_figure(legend_path)

if __name__ == "__main__":
    main()
