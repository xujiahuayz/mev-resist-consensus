import csv
import matplotlib.pyplot as plt

def plot_validator_selection_from_csv(file_path):
    # Initialize a dictionary to store the count of validator selections
    validator_counts = {}

    # Read the CSV file
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            validator_id = row['validator_id']
            # Increment the count for the validator
            if validator_id in validator_counts:
                validator_counts[validator_id] += 1
            else:
                validator_counts[validator_id] = 1

    # Generate the plot
    plot_validator_selections(validator_counts)

def plot_validator_selections(validator_counts):
    # Extracting validator IDs and their selection counts
    validator_ids = list(validator_counts.keys())
    selection_counts = list(validator_counts.values())

    # Plotting the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(validator_ids, selection_counts, color='skyblue')
    plt.xlabel('Validator ID')
    plt.ylabel('Number of Times Selected')
    plt.title('Number of Times Each Validator Was Selected')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plt.savefig('figures/ss/validator_selection_plot.png')

    # Show the plot
    plt.show()
    
if __name__ == "__main__":
    # Define the file path of the CSV file
    csv_file_path = 'data/same_seed/pos_visible80/pos_block_data_validators0_users6.csv'

    # Call the function to read data from CSV and plot
    plot_validator_selection_from_csv(csv_file_path)