'''For this file we focus on yeilding the builder's best strategy for time zero.'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random

random.seed(42)

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

    def block_value(self):
        '''Return the value of the block.'''
        return np.random.normal(scale=self.capability)
    
    def bidding_strategy(self, block_value, block_bid_his, winning_bid, counter):
        '''Return the bid amount for the builder based on the strategy.'''
        if self.strategy == 'fraction_based':
            fraction = 0.7
            return block_value * fraction
        elif self.strategy == 'reactive':
            if block_bid_his:
                last_bid = max(block_bid_his[-1].values())
                reactivity = 0.05
                new_bid = np.random.normal(last_bid, last_bid * reactivity)
                return min(new_bid, block_value)
            else:
                return block_value * 0.5
        elif self.strategy == 'historical':
            last_10_bids = winning_bid[-10:]
            return min(np.mean(last_10_bids), block_value) if last_10_bids else block_value * 0.5
        elif self.strategy == 'last_minute':
            if counter % 24 == 22:
                return block_value * 0.5
            return 0
        elif self.strategy == 'bluff':
            return block_value * (1 if counter < 22 else 0.5)

class Simulation:
    def __init__(self, num_builders, num_blocks):
        self.num_blocks = num_blocks
        self.winning_bid = []
        self.winning_strategy = []
        self.strategy_counts_per_block = []
        self.block_bid_his = []
        self.block_values = []

        # Equally distribute strategies among builders
        strategies_per_builder = len(STRATEGIES)
        builders_strategies = STRATEGIES * (num_builders // strategies_per_builder) + STRATEGIES[:num_builders % strategies_per_builder]
        random.shuffle(builders_strategies)

        self.builders = [Builder(i, builders_strategies[i], np.random.uniform(1, 10)) for i in range(num_builders)]

    def simulate_block(self):
        '''Simulate a block'''
        for _ in range(self.num_blocks):
            block_value = np.random.normal(10, 3)
            self.block_values.append(block_value)
            auction_end = False
            block_bid_his = []
            counter = 0
            while not auction_end and counter < 24:
                counter_bids = {builder.id: builder.bidding_strategy(block_value, block_bid_his, self.winning_bid, counter) for builder in self.builders}
                block_bid_his.append(counter_bids)
                if counter >= 12:
                    auction_end_probability = (counter - 12) / (24 - 12)
                    auction_end = random.random() < auction_end_probability
                counter += 1

            # Determine winning bid and strategy
            highest_bid = max(counter_bids.values())
            winning_builder_id = max(counter_bids, key=counter_bids.get)
            winning_builder_strategy = [builder.strategy for builder in self.builders if builder.id == winning_builder_id][0]

            self.winning_bid.append(highest_bid)
            self.winning_strategy.append(winning_builder_strategy)
            self.update_strategies(winning_builder_strategy, winning_builder_id)
            self.update_strategy_counts()
            self.block_bid_his.append(block_bid_his)
            # print(block_bid_his)

    def update_strategies(self, winning_strategy, winning_builder_id):
        last_winning_strategy = self.winning_strategy[-1] if self.winning_strategy else None

        for builder in self.builders:
            # Check if the winning builder used bluff strategy and won
            if builder.id == winning_builder_id and builder.strategy == 'bluff' :
                # Assign a new strategy randomly, excluding 'bluff'
                non_bluff_strategies = [s for s in STRATEGIES if s != 'bluff']
                builder.strategy = random.choice(non_bluff_strategies)
            # elif random.random() < CHANGE_STRATEGY_RATE/5:
            #     # a percentage of builders change to some random strategy
            #     builder.strategy = random.choice(STRATEGIES)
            elif random.random() < CHANGE_STRATEGY_RATE:
                # Change strategy to the last winning strategy for a percentage of builders
                if last_winning_strategy and builder.strategy != last_winning_strategy:
                    builder.strategy = last_winning_strategy

    def update_strategy_counts(self):
        # Count the number of builders using each strategy in the current block
        current_strategy_count = {strategy: 0 for strategy in STRATEGIES}
        for builder in self.builders:
            current_strategy_count[builder.strategy] += 1
        self.strategy_counts_per_block.append(current_strategy_count)

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

        block_numbers = list(range(len(self.strategy_counts_per_block)))
        for strategy in STRATEGIES:
            counts = [count[strategy] for count in self.strategy_counts_per_block]
            # print(simulation.strategy_counts_per_block)
            plt.plot(block_numbers, counts, label=strategy)

        plt.title('Number of Builders per Strategy Over Blocks')
        plt.xlabel('Block Number')
        plt.ylabel('Number of Builders')
        plt.legend()
        plt.grid(True)
        plt.show()


    def plot_bids_for_block(self, block_number):
        plt.figure(figsize=(12, 6))
        strategy_colors = {
            'fraction_based': 'blue',
            'reactive': 'green',
            'historical': 'red',
            'last_minute': 'cyan',
            'bluff': 'magenta'
        }

        block_bid_his = self.block_bid_his[block_number]

        for builder in self.builders:
            builder_bids = [None] * 24  # Initialize with None for 24 counters

            for counter in range(24):
                if counter < len(block_bid_his):
                    builder_bids[counter] = block_bid_his[counter].get(builder.id, None)

            plt.plot(range(24), builder_bids, label=f"Builder {builder.id} ({builder.strategy})", color=strategy_colors[builder.strategy], alpha=0.7)

        plt.xlabel('Counter')
        plt.ylabel('Bid Value')
        plt.title(f'Bids for Block {block_number}')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1)) 
        plt.grid(True)
        plt.tight_layout() 
        plt.show()

    def plot_bid_value(self):
        plt.figure(figsize=(12, 6))

        # Assuming self.winning_bids and self.block_values are populated correctly
        block_numbers = list(range(len(self.winning_bid)))

        plt.plot(block_numbers, self.winning_bid, label='Winning Bid', color='green')
        plt.plot(block_numbers, self.block_values, label='Block Value', color='blue')

        plt.xlabel('Block Number')
        plt.ylabel('Value')
        plt.title('Winning Bids and Block Values Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()

# Run the simulation
simulation = Simulation(NUM_BUILDERS, NUM_BLOCKS)
simulation.run()
simulation.plot_cumulative_win()
simulation.plot_strategy_num()
simulation.plot_bids_for_block(10)
simulation.plot_bid_value()
