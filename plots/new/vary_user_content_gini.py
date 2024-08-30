import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import os

sns.set_theme(style="whitegrid")

# Define constants
NUM_BUILDERS = 50  # Number of builders in the system
NUM_VALIDATORS = 50  # Number of validators in the system

def compute_gini(array):
    """Compute the Gini coefficient of a numpy array."""
    array = array.astype(float).flatten()
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 0.0000001
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def load_block_data(data_dir, mev_counts):
    builder_selection = {'pbs': {}, 'pos': {}}
    for mev_count in mev_counts:
        for system in ['pbs', 'pos']:
            selection_counts = []
            for run_id in range(1, 51):
                file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', system, f'block_data_{system}.csv')
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    # Count the number of blocks built by each builder/validator
                    if system == 'pbs':
                        builder_counts = df['builder_id'].value_counts().reindex(range(1, NUM_BUILDERS + 1), fill_value=0).values
                        selection_counts.append(builder_counts)
                    elif system == 'pos':
                        validator_counts = df['validator_id'].value_counts().reindex(range(1, NUM_VALIDATORS + 1), fill_value=0).values
                        selection_counts.append(validator_counts)

            if len(selection_counts) > 0:
                builder_selection[system][mev_count] = selection_counts
            else:
                builder_selection[system][mev_count] = np.array([])

    return builder_selection

def calculate_gini_selection_statistics(selection_counts):
    gini_selection_stats = {'pbs': {}, 'pos': {}}
    for system in ['pbs', 'pos']:
        for mev_count, runs in selection_counts[system].items():
            gini_values = [compute_gini(run) for run in runs if len(run) > 0]
            if gini_values:
                mean_gini = np.mean(gini_values)
                lower_ci = np.percentile(gini_values, 2.5)
                upper_ci = np.percentile(gini_values, 97.5)
                gini_selection_stats[system][mev_count] = (mean_gini, lower_ci, upper_ci)
            else:
                gini_selection_stats[system][mev_count] = (np.nan, np.nan, np.nan)
    return gini_selection_stats

def interpolate_and_smooth(x, y, num_points=49, window_length=5, polyorder=2):
    interp_func = interp1d(x, y, kind='linear', fill_value="extrapolate")
    x_new = np.linspace(min(x), max(x), num_points)
    y_new = interp_func(x_new)
    y_smooth = savgol_filter(y_new, window_length, polyorder)
    return x_new, y_smooth

def get_y_axis_limits(data_dirs, mev_counts):
    all_gini_values = []

    for data_dir in data_dirs:
        selection_counts = load_block_data(data_dir, mev_counts)
        gini_selection_stats = calculate_gini_selection_statistics(selection_counts)

        for system in ['pbs', 'pos']:
            all_gini_values.extend([gini_selection_stats[system].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts])

    min_y = min(all_gini_values)
    max_y = max(all_gini_values)
    return min_y, max_y

def plot_gini_selection_with_confidence(data_dir, mev_counts, output_file, ylim=None):
    selection_counts = load_block_data(data_dir, mev_counts)
    gini_selection_stats = calculate_gini_selection_statistics(selection_counts)

    # Extract Gini coefficient data and confidence intervals
    gini_pbs = [gini_selection_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts]
    gini_pos = [gini_selection_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts]
    lower_ci_pbs = [gini_selection_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[1] for mc in mev_counts]
    upper_ci_pbs = [gini_selection_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[2] for mc in mev_counts]
    lower_ci_pos = [gini_selection_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[1] for mc in mev_counts]
    upper_ci_pos = [gini_selection_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[2] for mc in mev_counts]

    # Filter out the valid indices for plotting
    valid_indices_pbs = [i for i, val in enumerate(gini_pbs) if not np.isnan(val)]
    valid_indices_pos = [i for i, val in enumerate(gini_pos) if not np.isnan(val)]

    # Interpolate and smooth data for plotting
    x_pbs, y_pbs = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pbs], np.array(gini_pbs)[valid_indices_pbs])
    x_pos, y_pos = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pos], np.array(gini_pos)[valid_indices_pos])
    _, lower_ci_pbs_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pbs], np.array(lower_ci_pbs)[valid_indices_pbs])
    _, upper_ci_pbs_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pbs], np.array(upper_ci_pbs)[valid_indices_pbs])
    _, lower_ci_pos_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pos], np.array(lower_ci_pos)[valid_indices_pos])
    _, upper_ci_pos_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pos], np.array(upper_ci_pos)[valid_indices_pos])

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the lines for PBS and POS
    sns.lineplot(x=x_pbs, y=y_pbs, label='PBS', ax=ax, color='blue')
    sns.lineplot(x=x_pos, y=y_pos, label='POS', ax=ax, color='orange')

    # Plot the confidence intervals as shaded areas
    ax.fill_between(x_pbs, lower_ci_pbs_smooth, upper_ci_pbs_smooth, color='blue', alpha=0.2)
    ax.fill_between(x_pos, lower_ci_pos_smooth, upper_ci_pos_smooth, color='orange', alpha=0.2)

    # Set plot labels, legend, and grid
    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=20)
    ax.set_ylabel('Gini Coefficient of Builder/Validator Selection', fontsize=20)
    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.legend(fontsize=18, loc='lower right')
    ax.grid(True)
    ax.xaxis.grid(True)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, which='both', linestyle='--', linewidth=0.7)

    if ylim:
        ax.set_ylim(ylim)

    # Save the plot
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    mev_counts = list(range(1, 51))
    data_dir_default = 'data/100_runs'
    data_dir_attackall = 'data/100run_attackall'
    data_dir_attacknon = 'data/100run_attacknon'

    ylim = get_y_axis_limits([data_dir_default, data_dir_attackall, data_dir_attacknon], mev_counts)

    plot_gini_selection_with_confidence(data_dir_default, mev_counts, 'figures/new/gini_selection.png', ylim)
    plot_gini_selection_with_confidence(data_dir_attackall, mev_counts, 'figures/new/gini_selection_attackall.png', ylim)
    plot_gini_selection_with_confidence(data_dir_attacknon, mev_counts, 'figures/new/gini_selection_attacknon.png', ylim)
