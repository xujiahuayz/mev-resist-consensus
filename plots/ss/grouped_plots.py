import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Set seaborn theme for modern styling
sns.set_theme(style="whitegrid")

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

    ax.stackplot(validator_percentages, *stack_data, colors=colors, alpha=0.9)

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
    """Create a 2x2 subplot grid for POS plots."""
    data_folder = '/Users/tammy/pbs/figures/ss'
    output_folder = '/Users/tammy/pbs/figures/ss'
    os.makedirs(output_folder, exist_ok=True)
    
    # Create figure with 2x2 subplots - make them square
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    
    # User attack counts to plot
    user_attack_counts = [0, 12, 24, 50]
    
    # Plot data
    for i, user_count in enumerate(user_attack_counts):
        row = i // 2
        col = i % 2
        ax = axes[row, col]
        
        # Load POS data
        file_name = f"pos_data_user_attack_{user_count}.json"
        file_path = os.path.join(data_folder, file_name)
        
        if os.path.exists(file_path):
            data = load_data(file_path)
            plot_mev_distribution_subplot(ax, data, user_count, "pos")
        else:
            ax.text(0.5, 0.5, f"Data not found:\n{file_name}", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title(f"Missing Data: POS", fontsize=20)
    
    # Set axis tickers as requested:
    # Top-left plot (0% MEV users) - Y-axis tickers only (remove x-axis)
    axes[0, 0].set_xticks([])
    
    # Top-right plot (33% MEV users) - No tickers at all
    axes[0, 1].set_xticks([])
    axes[0, 1].set_yticks([])
    
    # Bottom-left plot (67% MEV users) - Both X and Y-axis tickers (keep all)
    # (already set in subplot function)
    
    # Bottom-right plot (100% MEV users) - X-axis tickers only (remove y-axis)
    axes[1, 1].set_yticks([])
    
    # Add centered axis labels for the entire figure with proper spacing
    fig.text(0.5, -0.01, r'Percentage of $\mathtt{attack}$ Validators (%)', ha='center', fontsize=36)
    fig.text(0.01, 0.35, 'MEV Profit Captured (%)', ha='center', rotation=90, fontsize=36)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(output_folder, "pos_grouped_mev_distribution.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    
    print(f"POS grouped plot saved to {save_path}")

def create_pbs_grouped_plot():
    """Create a 2x2 subplot grid for PBS plots."""
    data_folder = '/Users/tammy/pbs/figures/ss'
    output_folder = '/Users/tammy/pbs/figures/ss'
    os.makedirs(output_folder, exist_ok=True)
    
    # Create figure with 2x2 subplots - make them square
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    
    # User attack counts to plot
    user_attack_counts = [0, 12, 24, 50]
    
    # Plot data
    for i, user_count in enumerate(user_attack_counts):
        row = i // 2
        col = i % 2
        ax = axes[row, col]
        
        # Load PBS data
        file_name = f"pbs_data_user_attack_{user_count}.json"
        file_path = os.path.join(data_folder, file_name)
        
        if os.path.exists(file_path):
            data = load_data(file_path)
            plot_mev_distribution_subplot(ax, data, user_count, "pbs")
        else:
            ax.text(0.5, 0.5, f"Data not found:\n{file_name}", 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.set_title(f"Missing Data: PBS", fontsize=20)
    
    # Set axis tickers as requested:
    # Top-left plot (0% MEV users) - Y-axis tickers only (remove x-axis)
    axes[0, 0].set_xticks([])
    
    # Top-right plot (33% MEV users) - No tickers at all
    axes[0, 1].set_xticks([])
    axes[0, 1].set_yticks([])
    
    # Bottom-left plot (67% MEV users) - Both X and Y-axis tickers (keep all)
    # (already set in subplot function)
    
    # Bottom-right plot (100% MEV users) - X-axis tickers only (remove y-axis)
    axes[1, 1].set_yticks([])
    
    # Add centered axis labels for the entire figure with proper spacing
    fig.text(0.5, -0.01, r'Percentage of $\mathtt{attack}$ Builders (%)', ha='center', fontsize=36)
    fig.text(0.01, 0.35, 'MEV Profit Captured (%)', ha='center', rotation=90, fontsize=36)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(output_folder, "pbs_grouped_mev_distribution.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    
    print(f"PBS grouped plot saved to {save_path}")

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