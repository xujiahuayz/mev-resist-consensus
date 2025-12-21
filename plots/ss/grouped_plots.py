import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

# Set seaborn theme for modern styling
sns.set_theme(style="whitegrid")

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

def load_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def plot_mev_distribution_subplot(ax, aggregated_data, user_attack_count, plot_type, total_validators=20):
    """Generate a subplot of MEV distribution."""
    validator_counts = sorted(int(key) for key in aggregated_data.keys())
    validator_percentages = [100 * count / total_validators for count in validator_counts]
    
    if plot_type == "pos":
        validator_mev = [aggregated_data[str(count)]["validators_mev"] for count in validator_counts]
        user_mev = [aggregated_data[str(count)]["users_mev"] for count in validator_counts]
        total_mev = [aggregated_data[str(count)]["total_mev"] for count in validator_counts]
        
        validator_mev_percent = [100 * v / t if t > 0 else 0 for v, t in zip(validator_mev, total_mev)]
        user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
        uncaptured_mev_percent = [100 - v - u for v, u in zip(validator_mev_percent, user_mev_percent)]
        
        # Stack order: validator, user, uncaptured
        stack_data = [validator_mev_percent, user_mev_percent, uncaptured_mev_percent]
    else:  # pbs
        builder_mev = [aggregated_data[str(count)]["builders_mev"] for count in validator_counts]
        user_mev = [aggregated_data[str(count)]["users_mev"] for count in validator_counts]
        total_mev = [aggregated_data[str(count)]["total_mev"] for count in validator_counts]
        
        builder_mev_percent = [100 * b / t if t else 0 for b, t in zip(builder_mev, total_mev)]
        user_mev_percent = [100 * u / t if t else 0 for u, t in zip(user_mev, total_mev)]
        uncaptured_mev_percent = [100 - b - u for b, u in zip(builder_mev_percent, user_mev_percent)]
        
        # Stack order: builder, user, uncaptured
        stack_data = [builder_mev_percent, user_mev_percent, uncaptured_mev_percent]

    # Use sophisticated color palette
    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", 3)
    colors = [palette[2], palette[1], palette[0]]  # Darkest to lightest

    ax.stackplot(validator_percentages, *stack_data, colors=colors, alpha=0.8)

    # User attack percentage mapping
    user_attack_percentage_map = {'0': '0', '12': '33', '24': '67', '50': '100'}
    user_attack_percentage = user_attack_percentage_map.get(str(user_attack_count), 'Check Data')
    
    # Set title with percentage
    ax.set_title(rf"${user_attack_percentage}\%$ of $\mathtt{{attack}}$ Users", fontsize=32)
    
    # Remove individual subplot axis labels - we'll use global ones
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(['0', '25', '50', '75', '100'], fontsize=28)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0', '25', '50', '75', '100'], fontsize=28)
    
    ax.margins(0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

def create_pos_grouped_plot():
    """Create a 1x4 subplot grid for PoS plots."""
    data_folder = PROJECT_ROOT / 'figures' / 'ss'
    output_folder = PROJECT_ROOT / 'figures' / 'ss'
    os.makedirs(output_folder, exist_ok=True)
    
    # Create figure with 1 row and 4 columns
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    
    # User attack counts to plot
    user_attack_counts = [0, 12, 24, 50]
    
    # Plot PoS data
    for col, user_count in enumerate(user_attack_counts):
        ax = axes[col]
        
        # Load PoS data
        file_name = f"pos_data_user_attack_{user_count}.json"
        file_path = data_folder / file_name
        
        if file_path.exists():
            data = load_data(file_path)
            plot_mev_distribution_subplot(ax, data, user_count, "pos")
        else:
            ax.text(0.5, 0.5, f"Data not found:\n{file_name}", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title("Missing Data: PoS", fontsize=20)
    
    # Set axis tickers: Only leftmost plot has y-axis, all have x-axis (same row)
    axes[1].set_yticks([])  # 2nd: no y-axis
    axes[2].set_yticks([])  # 3rd: no y-axis
    axes[3].set_yticks([])  # Rightmost: no y-axis
    
    # Add centered axis labels for the entire figure
    fig.text(0.5, -0.05, r'Percentage of $\mathtt{attack}$ Validators (%)', ha='center', fontsize=36)
    fig.text(-0.015, 0, 'MEV Profit Captured (%)', ha='center', rotation=90, fontsize=36)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    save_path = output_folder / "pos_grouped_mev_distribution.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    
    print(f"PoS grouped plot saved to {save_path}")

def create_pbs_grouped_plot():
    """Create a 1x4 subplot grid for ePBS plots."""
    data_folder = PROJECT_ROOT / 'figures' / 'ss'
    output_folder = PROJECT_ROOT / 'figures' / 'ss'
    os.makedirs(output_folder, exist_ok=True)
    
    # Create figure with 1 row and 4 columns
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    
    # User attack counts to plot
    user_attack_counts = [0, 12, 24, 50]
    
    # Plot ePBS data
    for col, user_count in enumerate(user_attack_counts):
        ax = axes[col]
        
        # Load ePBS data
        file_name = f"pbs_data_user_attack_{user_count}.json"
        file_path = data_folder / file_name
        
        if file_path.exists():
            data = load_data(file_path)
            plot_mev_distribution_subplot(ax, data, user_count, "pbs")
        else:
            ax.text(0.5, 0.5, f"Data not found:\n{file_name}", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title("Missing Data: ePBS", fontsize=20)
    
    # Set axis tickers: Only leftmost plot has y-axis, all have x-axis
    axes[1].set_yticks([])  # 2nd: no y-axis
    axes[2].set_yticks([])  # 3rd: no y-axis
    axes[3].set_yticks([])  # Rightmost: no y-axis
    
    # Add centered axis labels for the entire figure
    fig.text(0.5, -0.05, r'Percentage of $\mathtt{attack}$ Builders (%)', ha='center', fontsize=36)
    fig.text(-0.015, 0, 'MEV Profit Captured (%)', ha='center', rotation=90, fontsize=36)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    save_path = output_folder / "pbs_grouped_mev_distribution.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    
    print(f"ePBS grouped plot saved to {save_path}")

def create_pos_legend_figure(save_path):
    """Generate and save a separate figure containing only the POS legend."""
    plt.figure(figsize=(12, 2))
    # Use the same sophisticated color palette
    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", 3)
    colors = [palette[0], palette[1], palette[2]]

    labels = ["Uncaptured", "Users'", "Validators'"]
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]

    plt.legend(handles, labels, loc='center', fontsize=32, frameon=False)
    plt.axis('off')

    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

def create_pbs_legend_figure(save_path):
    """Generate and save a separate figure containing only the PBS legend."""
    plt.figure(figsize=(12, 2))
    # Use the same sophisticated color palette
    palette = sns.color_palette("ch:rot=-.25,hue=1,light=.75", 3)
    colors = [palette[0], palette[1], palette[2]]

    labels = ["Uncaptured", "Users'", "Builders'"]
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]

    plt.legend(handles, labels, loc='center', fontsize=32, frameon=False)
    plt.axis('off')

    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

if __name__ == "__main__":
    create_pos_grouped_plot()
    create_pbs_grouped_plot()
