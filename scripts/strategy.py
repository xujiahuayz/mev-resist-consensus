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

class Builder:
    def __init__(self, id, strategy, capability):
        self.id = id
        self.strategy = strategy
        self.capability = capability

    def bidding_strategy(self, block_value, block_bid_his, winning_bid, counter):
        '''Return the bid amount for the builder based on the strategy.'''
        if self.strategy == 'fraction_based':
            fraction = 0.5
            return block_value * fraction
        elif self.strategy == 'reactive':
            if block_bid_his:
                last_bid = max(block_bid_his[-1].values())
                increment = 0.1
                return last_bid * (1 + increment)
            else:
                return block_value * 0.5
        elif self.strategy == 'historical':
            return np.mean(winning_bid) if winning_bid else block_value * 0.5
        elif self.strategy == 'last_minute':
            if counter % 24 == 23:
                return block_value * 0.5
            return 0
        elif self.strategy == 'bluff':
            return block_value * (1.5 if counter < 23 else 0.5)

class Simulation:
    def __init__(self, num_builders, num_blocks):
        self.num_blocks = num_blocks
        self.winning_bid = []
        self.winning_strategy = []
        self.strategy_counts_per_block = []

        # Equally distribute strategies among builders
        strategies_per_builder = len(STRATEGIES)
        builders_strategies = STRATEGIES * (num_builders // strategies_per_builder) + STRATEGIES[:num_builders % strategies_per_builder]
        random.shuffle(builders_strategies)

        self.builders = [Builder(i, builders_strategies[i], np.random.uniform(1, 10)) for i in range(num_builders)]

    def simulate_block(self):
        '''Simulate a block'''
        for _ in range(self.num_blocks):
            block_value = np.random.normal(1, 0.1)  # Base value for the block
            auction_end = False
            block_bid_his = []
            counter = 0
            while not auction_end and counter < 24:
                counter_bids = {builder.id: builder.bidding_strategy(block_value, block_bid_his, self.winning_bid, counter) for builder in self.builders}
                block_bid_his.append(counter_bids)
                auction_end = random.choice([True, False])
                counter += 1

            # Determine winning bid and strategy
            highest_bid = max(counter_bids.values())
            winning_builder_id = max(counter_bids, key=counter_bids.get)
            winning_builder_strategy = [builder.strategy for builder in self.builders if builder.id == winning_builder_id][0]

            self.winning_bid.append(highest_bid)
            self.winning_strategy.append(winning_builder_strategy)
            self.update_strategies(winning_builder_strategy)

    def update_strategies(self, winning_strategy):
        '''Update the strategy of each builder with a probability of CHANGE_STRATEGY_RATE.'''
        for builder in self.builders:
            if random.random() < CHANGE_STRATEGY_RATE:
                builder.strategy = winning_strategy

    def track_strategies(self):
        """Track the number of builders for each strategy after each block."""
        count_per_strategy = {strategy: 0 for strategy in STRATEGIES}
        for builder in self.builders:
            count_per_strategy[builder.strategy] += 1
        self.strategy_counts_per_block.append(count_per_strategy)


    def run(self):
        '''run'''
        self.simulate_block()

    def plot_cumulative_win(self):
        '''Plot the cumulative win for each strategy'''
        plt.figure(figsize=(12, 6))
        strategies_count = {strategy: [0] * self.num_blocks for strategy in STRATEGIES}
        for i, strategy in enumerate(self.winning_strategy):
            strategies_count[strategy][i] += 1
        for strategy, counts in strategies_count.items():
            plt.plot(range(self.num_blocks), np.cumsum(counts), label=strategy)
        plt.xlabel('Block Number')
        plt.ylabel('Cumulative Wins')
        plt.title('Strategy Trends Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_strategy_num(self):
        """Plot the number of builders for each strategy over blocks."""
        plt.figure(figsize=(12, 6))

        # Prepare data for plotting
        block_numbers = list(range(len(self.strategy_counts_per_block)))
        for strategy in STRATEGIES:
            counts = [count[strategy] for count in self.strategy_counts_per_block]
            plt.plot(block_numbers, counts, label=strategy)

        # Plot settings
        plt.title('Number of Builders per Strategy Over Blocks')
        plt.xlabel('Block Number')
        plt.ylabel('Number of Builders')
        plt.legend()
        plt.grid(True)
        plt.show()

# Run the simulation
simulation = Simulation(NUM_BUILDERS, NUM_BLOCKS)
simulation.run()
simulation.plot_cumulative_win()
simulation.plot_strategy_num()
