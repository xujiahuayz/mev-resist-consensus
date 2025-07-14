import csv
import os
import matplotlib.pyplot as plt
import numpy as np

# Change these to match your actual total counts
TOTAL_VALIDATORS = 20
TOTAL_USERS = 50

def get_final_validator_counts(file_path, validator_attack_count):
    """Extract final validator selection counts from a CSV file."""
    attacking_total = 0
    non_attacking_total = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            validator_id = row['validator_id']
            # Extract numeric part of validator ID
            validator_index = int(validator_id.split('_')[-1])

            # Increment attacking or non-attacking count
            if validator_index < validator_attack_count:
                attacking_total += 1
            else:
                non_attacking_total += 1

    return attacking_total, non_attacking_total

def plot_final_build_counts(data_folder_path, configs_list):
    """
    - 3×3 subplots with bar charts
    - Columns = percentage of attacking validators
    - Rows = percentage of attacking users
    - Each subplot shows final build counts for attack vs non-attack validators
    """
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Gather unique validator/user counts
    validator_counts = sorted({cfg[0] for cfg in configs_list})
    user_counts = sorted({cfg[1] for cfg in configs_list})

    # Create subplots: rows=users, cols=validators
    fig, axes = plt.subplots(
        nrows=len(user_counts),
        ncols=len(validator_counts),
        figsize=(12, 10),
        squeeze=False
    )

    # Font sizes
    label_font_size = 12
    tick_label_font_size = 10
    outer_label_font_size = 16

    for validator_attack_count, user_attack_count in configs_list:
        row = user_counts.index(user_attack_count)
        col = validator_counts.index(validator_attack_count)
        ax = axes[row, col]

        filename = f"pos_block_data_validators{validator_attack_count}_users{user_attack_count}.csv"
        file_path = os.path.join(data_folder_path, filename)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            ax.text(0.5, 0.5, "File Not Found",
                    ha='center', va='center',
                    fontsize=label_font_size)
            ax.set_axis_off()
            continue

        att_total, nonatt_total = get_final_validator_counts(file_path, validator_attack_count)
        
        # Create bar chart
        categories = ['Attack', 'Non-Attack']
        values = [att_total, nonatt_total]
        colors = ['red', 'blue']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:,}', ha='center', va='bottom', fontsize=8)

        # Hide x labels except bottom row
        if row != len(user_counts) - 1:
            ax.tick_params(axis='x', labelbottom=False)
        # Hide y labels except first column
        if col != 0:
            ax.tick_params(axis='y', labelleft=False)

        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    # Convert numeric validator counts → percentage columns
    for ax, val_count in zip(axes[0], validator_counts):
        pct_validators = (val_count / TOTAL_VALIDATORS) * 100
        ax.set_title(f"{pct_validators:.0f}%", fontsize=outer_label_font_size, pad=10)

    # Convert numeric user counts → percentage rows, on the right
    for ax, usr_count in zip(axes[:, -1], user_counts):
        pct_users = (usr_count / TOTAL_USERS) * 100
        ax.annotate(
            f"{pct_users:.0f}%",
            xy=(1.06, 0.5),
            xytext=(1.06, 0.5),
            textcoords='axes fraction',
            ha='center',
            va='center',
            rotation=-90,
            fontsize=outer_label_font_size,
            annotation_clip=False
        )

    # Make subplots fit nicely
    plt.tight_layout()
    plt.subplots_adjust(left=0.12, right=0.88, top=0.83, bottom=0.12)

    # Single text labels
    fig.text(
        0.5, 0.91,  # top
        r"Percentage of MEV-Seeking Validators $\tau_{V_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )
    fig.text(
        0.95, 0.5,  # right
        r"Percentage of MEV-Seeking Users $\tau_{U_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        rotation=-90,
        fontsize=outer_label_font_size
    )
    fig.text(
        0.03, 0.5,  # left
        "Final Build Counts",
        ha='center', va='center',
        rotation='vertical',
        fontsize=outer_label_font_size
    )
    fig.text(
        0.5, 0.06,  # bottom
        "Validator Type",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )

    out_path = os.path.join(output_dir, 'pos_final_build_counts_3x3_grid.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"3×3 grid bar chart saved to {out_path}")

if __name__ == "__main__":
    DATA_FOLDER = 'data/same_seed/pos_visible80'
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_final_build_counts(DATA_FOLDER, configs)
