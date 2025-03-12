import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

def load_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def plot_mev_distribution(aggregated_data, user_attack_count, save_path, total_users=50, total_validators=20):
    """Generate and save a plot of MEV distribution."""
    # Extracting data
    validator_counts = sorted(int(key) for key in aggregated_data.keys())
    validator_percentages = [100 * count / total_validators for count in validator_counts]
    validator_mev = [aggregated_data[str(count)]["validators_mev"] for count in validator_counts]
    user_mev = [aggregated_data[str(count)]["users_mev"] for count in validator_counts]
    total_mev = [aggregated_data[str(count)]["total_mev"] for count in validator_counts]

    # Calculating percentages
    validator_mev_percent = [100 * v / t if t > 0 else 0 for v, t in zip(validator_mev, total_mev)]
    user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 - v - u for v, u in zip(validator_mev_percent, user_mev_percent)]

    # Set large font sizes
    axis_font_size = 32
    title_font_size = 36
    tick_font_size = 28

    plt.figure(figsize=(10, 9))
    palette = sns.color_palette("Blues", 3)
    colors = [palette[2], palette[1], palette[0]]

    # Stackplot to visualize MEV distribution with adjusted data
    plt.stackplot(validator_percentages, user_mev_percent, validator_mev_percent, uncaptured_mev_percent,
                  labels=["Users' MEV", "Validators' MEV", "Uncaptured MEV"], colors=colors, alpha=0.9)
    
    plt.xlabel("Percentage of Attacking Validators", fontsize=axis_font_size)
    plt.ylabel("MEV Profit Distribution (%)", fontsize=axis_font_size)
    # user_attack_percentage = round(100 * int(user_attack_count) / total_users)
    user_attack_percentage_map = {
        '0': '0',
        '12': '33',
        '24': '67',
        '50': '100'
    }
    user_attack_percentage = user_attack_percentage_map.get(str(user_attack_count), 'Check Data')


    plt.title(f"User Attacker Percentage: {user_attack_percentage}%", fontsize=title_font_size)
    plt.legend(loc="upper right", fontsize=tick_font_size)
    plt.xticks(ticks=[0, 25, 50, 75, 100], labels=['0', '25', '50', '75', '100'], fontsize=tick_font_size)
    plt.yticks(fontsize=tick_font_size)
    plt.margins(0)
    plt.tight_layout(pad=0)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

def main():
    data_folder = '/Users/tammy/mev-resist-consensus/figures/ss'
    output_folder = '/Users/tammy/mev-resist-consensus/figures/ss'
    os.makedirs(output_folder, exist_ok=True)  # Ensure the output directory exists

    # Iterate through the JSON files in the data folder
    for file_name in os.listdir(data_folder):
        if file_name.endswith('.json') and file_name.startswith('pos_aggregated_data_user_attack'):
            file_path = os.path.join(data_folder, file_name)
            data = load_data(file_path)
            user_attack_count = file_name.split('_')[-1].split('.')[0]  # Extract user attack count from filename
            save_path = os.path.join(output_folder, f"pos_mev_distribution_user_attack_{user_attack_count}.png")
            plot_mev_distribution(data, user_attack_count, save_path, total_users=50)

if __name__ == "__main__":
    main()
