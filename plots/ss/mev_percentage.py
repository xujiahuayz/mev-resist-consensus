"""This is a file to compare the MEV transaction percentage between PBS and PoS systems."""

import os
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Define paths
pbs_folder = 'data/same_seed/pbs_visible80'
pos_folder = 'data/same_seed/pos_visible80'
output_folder = 'figures/ss'

# Function to load and preprocess data
def load_data(folder, role='builders'):
    """
    Load CSV files from a folder and extract the number of builders/validators and users.

    Parameters:
    folder (str): Path to the folder containing the CSV files.
    role (str): 'builders' for PBS or 'validators' for PoS.

    Returns:
    pd.DataFrame: Combined DataFrame with added 'builders/validators' and 'users' columns.
    """
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.csv')]
    all_data = []
    for file in files:
        # Extract builders/validators and users from the filename using regex
        filename = os.path.basename(file)
        regex = rf'{role}(\d+)_users(\d+)'  # Dynamically handle 'builders' or 'validators'
        match = pd.Series(filename).str.extract(regex)
        role_count = int(match[0][0])  # Extract the count of builders/validators
        users = int(match[1][0])  # Extract the count of users

        # Load CSV file and add columns for role and users
        df = pd.read_csv(file)
        df[role] = role_count
        df['users'] = users
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

# Function to calculate MEV statistics for grouped data
def calculate_mev_stats(df, role='builders'):
    """
    Calculate total transactions, MEV transactions, and MEV percentage grouped by role and users.

    Parameters:
    df (pd.DataFrame): Input data with role and users columns.
    role (str): 'builders' for PBS or 'validators' for PoS.

    Returns:
    pd.DataFrame: Aggregated statistics with MEV percentages.
    """
    # A transaction is MEV if `target_tx` is not null
    df['is_mev'] = df['target_tx'].notnull()

    # Group by role (builders/validators) and users
    grouped = df.groupby([role, 'users']).agg(
        total_transactions=('id', 'count'),
        mev_transactions=('is_mev', 'sum')
    ).reset_index()

    # Add MEV percentage column
    grouped['mev_percentage'] = (grouped['mev_transactions'] / grouped['total_transactions']) * 100
    return grouped

# Load PBS and PoS data
pbs_data = load_data(pbs_folder, role='builders')  # For PBS: builders
pos_data = load_data(pos_folder, role='validators')  # For PoS: validators

# Calculate statistics for PBS and PoS
pbs_stats = calculate_mev_stats(pbs_data, role='builders')
pos_stats = calculate_mev_stats(pos_data, role='validators')

# Prepare data for dual surface plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# PBS Surface
pbs_X, pbs_Y, pbs_Z = (
    pbs_stats['users'],
    pbs_stats['builders'],
    pbs_stats['mev_percentage']
)
ax.plot_trisurf(pbs_X, pbs_Y, pbs_Z, color='blue', alpha=0.7, label='PBS')

# PoS Surface
pos_X, pos_Y, pos_Z = (
    pos_stats['users'],
    pos_stats['validators'],
    pos_stats['mev_percentage']
)
ax.plot_trisurf(pos_X, pos_Y, pos_Z, color='red', alpha=0.7, label='PoS')

# Labels and title
ax.set_xlabel('Number of Users')
ax.set_ylabel('Number of Builders/Validators')
ax.set_zlabel('MEV Transaction Percentage')
plt.title('Comparison of MEV Transaction Percentage: PBS vs PoS')

# Add a legend manually
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='blue', lw=4, alpha=1, label='PBS'),
    Line2D([0], [0], color='red', lw=4, alpha=1, label='PoS'),
]
ax.legend(handles=legend_elements, loc='best')

# Save the figure
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, 'mev_3d_surface_plot.png')
plt.savefig(output_path)
plt.show()

print(f"Surface plot saved at {output_path}")
