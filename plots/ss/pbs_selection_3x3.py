import csv
import os
import matplotlib.pyplot as plt
import numpy as np

# Change these to match the actual total number of builders and users
TOTAL_BUILDERS = 20
TOTAL_USERS = 50

def get_final_builder_counts(file_path, builder_attack_count):
    """Extract final builder selection counts from a CSV file."""
    attacking_total = 0
    non_attacking_total = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            builder_id = row['builder_id']
            builder_index = int(builder_id.split('_')[-1])

            # Count attacker vs. non-attacker
            if builder_index < builder_attack_count:
                attacking_total += 1
            else:
                non_attacking_total += 1

    return attacking_total, non_attacking_total

def plot_final_build_counts(data_folder_path, configs_list):
    """
    - 3×3 subplots with bar charts
    - Columns = percentage of attacking builders
    - Rows = percentage of attacking users
    - Each subplot shows final build counts for attack vs non-attack builders
    """
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Gather unique builder/user counts from the configs
    builder_counts = sorted({c[0] for c in configs_list})
    user_counts = sorted({c[1] for c in configs_list})

    fig, axes = plt.subplots(
        nrows=len(user_counts),
        ncols=len(builder_counts),
        figsize=(12, 10),
        squeeze=False
    )

    # Font sizes
    label_font_size = 12
    tick_label_font_size = 10
    outer_label_font_size = 16

    # Plot each subplot
    for b_attack, u_attack in configs_list:
        row_idx = user_counts.index(u_attack)
        col_idx = builder_counts.index(b_attack)
        ax = axes[row_idx, col_idx]

        filename = f"pbs_block_data_builders{b_attack}_users{u_attack}.csv"
        file_path = os.path.join(data_folder_path, filename)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            ax.text(0.5, 0.5, "File Not Found",
                    ha='center', va='center',
                    fontsize=label_font_size)
            ax.set_axis_off()
            continue

        att_total, nonatt_total = get_final_builder_counts(file_path, b_attack)
        
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

        # Hide x-axis labels except bottom row
        if row_idx != len(user_counts) - 1:
            ax.tick_params(axis='x', labelbottom=False)
        # Hide y-axis labels except first column
        if col_idx != 0:
            ax.tick_params(axis='y', labelleft=False)

        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    # Convert numeric builder counts to percentages and label columns
    for ax, bcount in zip(axes[0], builder_counts):
        pct_builders = (bcount / TOTAL_BUILDERS) * 100
        ax.set_title(f"{pct_builders:.0f}%", fontsize=outer_label_font_size, pad=10)

    # Convert numeric user counts to percentages and label rows on the right
    for ax, ucount in zip(axes[:, -1], user_counts):
        pct_users = (ucount / TOTAL_USERS) * 100
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

    # Tight layout for subplots (ensures subplots themselves aren't overlapping)
    plt.tight_layout()

    # Adjust margins to make room for outer text, tweak as needed
    plt.subplots_adjust(left=0.12, right=0.88, top=0.83, bottom=0.12)

    # Single text labels
    # Top: "Percentage of Attacking Builders"
    fig.text(
        0.5, 0.91,  # Move down from 0.95 if needed
        r"Percentage of MEV-Seeking Builders $\tau_{B_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )
    # Right: "Percentage of Attacking Users"
    fig.text(
        0.95, 0.5,  # Move left from 0.92 if needed
        r"Percentage MEV-Seeking Users $\tau_{U_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        rotation=-90,
        fontsize=outer_label_font_size
    )
    # Left: "Final Build Counts"
    fig.text(
        0.03, 0.5,
        "Final Build Counts",
        ha='center', va='center',
        rotation='vertical',
        fontsize=outer_label_font_size
    )
    # Bottom: "Builder Type"
    fig.text(
        0.5, 0.06,
        "Builder Type",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )

    out_path = os.path.join(output_dir, "pbs_final_build_counts_3x3_grid.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"3×3 grid bar chart saved to {out_path}")

if __name__ == "__main__":
    DATA_FOLDER = "data/same_seed/pbs_visible80"
    # Example: (attacking_builders_count, attacking_users_count).
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_final_build_counts(DATA_FOLDER, configs)
