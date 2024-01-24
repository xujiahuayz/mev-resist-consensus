'''For this file we focus on yeilding the builder's best strategy for time zero.'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random

# Constants
NUM_BUILDERS = 50
NUM_BLOCKS = 100
STRATEGIES = ['fraction_based', 'reactive', 'historical', 'last_minute', 'bluff']
CHANGE_STRATEGY_RATE = 0.2

def simulate_transaction_fee():
    base_fee = np.random.normal(loc=1.0, scale=0.1)
    # Each builder's fee will be a variation of the base fee
    return lambda builder: np.random.normal(loc=base_fee, scale=builder['capability'])

# Initialize builders
builders = [
    {
        'id': i, 
        'strategy': random.choice(STRATEGIES),
        'capability': np.random.uniform(0.05, 0.2)  
    } 
    for i in range(NUM_BUILDERS)
]


def simulate_block(builders, get_fee_for_builder):
    bids = {builder['id']: get_fee_for_builder(builder) for builder in builders}
    winning_bid = max(bids.values())
    winning_builders = [builder for builder in builders if bids[builder['id']] == winning_bid]
    winning_strategy = winning_builders[0]['strategy'] if winning_builders else None
    return winning_strategy, bids


def update_strategies(builders, winning_strategy):
    for builder in builders:
        if random.random() < CHANGE_STRATEGY_RATE:
            builder['strategy'] = winning_strategy

# Run the simulation
results = []
last_winning_strategy = None
for block in range(NUM_BLOCKS):
    get_fee_for_builder = simulate_transaction_fee()
    winning_strategy, bids = simulate_block(builders, get_fee_for_builder)
    update_strategies(builders, winning_strategy)
    results.append({
        'block': block,
        'winning_strategy': winning_strategy,
        'bids': bids
    })
    last_winning_strategy = winning_strategy if winning_strategy else last_winning_strategy

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Plot the trends
plt.figure(figsize=(14, 7))
for strategy in STRATEGIES:
    counts = results_df['winning_strategy'].eq(strategy).cumsum()
    plt.plot(counts, label=strategy)

plt.title('Strategy Trends Over Blocks')
plt.xlabel('Block Number')
plt.ylabel('Cumulative Wins')
plt.legend()
plt.grid(True)
plt.show()
