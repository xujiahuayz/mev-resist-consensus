import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the data from the CSV file
data = pd.read_csv('/Users/aaryangulia/DSF/PBS/pbs/pbs_c/cmake-build-debug/num_builder_sim.csv', header=None)

# Calculate the number of builders
data['num_builders'] = data.index + 2

# Calculate bid/(blockValue-bid)
data['ratio'] = data[2] / (data[1] - data[2])

# Calculate the coefficients of the line of best fit
coefficients = np.polyfit(data['num_builders'], data['ratio'], 1)

# Create a function that represents the line of best fit
line_of_best_fit = np.poly1d(coefficients)

# Plot the data
plt.plot(data['num_builders'], data['ratio'], label='Data')

# Plot the line of best fit
plt.plot(data['num_builders'], line_of_best_fit(data['num_builders']), label='Line of Best Fit', color='red')

plt.xlabel('Number of Builders')
plt.ylabel('Net Proposer Reward / Net Builder Reward')
plt.title('Net Proposer Reward / Net Builder Reward vs Number of Builders')
plt.legend()
plt.show()