'''For this file we focus on yeilding the builder's best strategy for time zero.'''

import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

random.seed(42)

# Constants
NUM_BUILDERS = 20
NUM_BLOCKS = 100
STRATEGIES = ['fraction_based', 'reactive', 'historical', 'last_minute', 'bluff']
CHANGE_STRATEGY_RATE = 0.2

class Builder:
    def __init__(self, id, strategy, capability: float, reactivity: float):
        self.id = id
        self.strategy = strategy
        self.capability = capability
        self.reactivity = reactivity

    def block_value(self):
        '''Return the value of the block.'''
        return max(0, random.uniform(self.capability-5, self.capability+5))
        # return self.capability
    
    def bidding_strategy(self, block_value, block_bid_his, winning_bid, counter):
        '''Return the bid amount for the builder based on the strategy.'''
        if self.strategy == 'fraction_based':
            return block_value * 0.5
        elif self.strategy == 'reactive':
            if block_bid_his:
                last_bid = max(block_bid_his[-1].values())
                new_bid = np.random.normal(last_bid, last_bid * self.reactivity)
                return min(new_bid, block_value)
            else:
                return block_value * 0.1
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
        self.winning_block_values = []
        self.builder_strategies_per_block = []

        builders_per_strategy = NUM_BUILDERS // len(STRATEGIES)

        # Initialize a list to store the strategy assigned to each builder
        builders_strategies = []

        # Assign each strategy to the correct number of builders
        for strategy in STRATEGIES:
            builders_strategies.extend([strategy] * builders_per_strategy)

        self.builders = [Builder(i, builders_strategies[i], random.uniform(5, 10), random.uniform(0,1)) for i in range(num_builders)]

    def simulate_block(self):
        '''Simulate a block'''
        for _ in range(self.num_blocks):
            block_values_per_builder = {}
            auction_end = False
            block_bid_his = []
            counter = 0

            current_strategies = {builder.id: builder.strategy for builder in self.builders}
            self.builder_strategies_per_block.append(current_strategies)

            while not auction_end and counter < 24:
                counter_bids = {}
                for builder in self.builders:
                    increment_factor = 1 + (random.uniform(0,1) * counter/24)
                    perceived_block_value = builder.block_value() * increment_factor
                    block_values_per_builder[builder.id] = perceived_block_value
                    bid = builder.bidding_strategy(perceived_block_value, block_bid_his, self.winning_bid, counter)
                    counter_bids[builder.id] = bid

                block_bid_his.append(counter_bids)
                if counter >= 18:
                    auction_end_probability = (counter - 12) / (24 - 12)
                    auction_end = random.random() < auction_end_probability
                counter += 1
                

            # Determine winning bid, strategy, and block value
            highest_bid = max(counter_bids.values())
            winning_builder_id = max(counter_bids, key=counter_bids.get)
            winning_builder_strategy = [builder.strategy for builder in self.builders if builder.id == winning_builder_id][0]
            winning_block_value =  block_values_per_builder[winning_builder_id]

            self.winning_bid.append(highest_bid)
            self.winning_strategy.append(winning_builder_strategy)
            self.update_strategies(winning_builder_strategy, winning_builder_id)
            self.update_strategy_counts()
            self.block_bid_his.append(block_bid_his)
            self.winning_block_values.append(winning_block_value)
            # print(block_bid_his)

    def update_strategies(self, winning_strategy, winning_builder_id):
        last_winning_strategy = self.winning_strategy[-1] if self.winning_strategy else None

        for builder in self.builders:
            # Check if the winning builder used bluff strategy and won
            # if builder.id == winning_builder_id and builder.strategy == 'bluff' :
            #     # Assign a new strategy randomly, excluding 'bluff'
            #     non_bluff_strategies = [s for s in STRATEGIES if s != 'bluff']
            #     builder.strategy = random.choice(non_bluff_strategies)
            # elif random.random() < CHANGE_STRATEGY_RATE/5:
            #     # a percentage of builders change to some random strategy
            #     builder.strategy = random.choice(STRATEGIES)
            if random.random() < CHANGE_STRATEGY_RATE:
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
        block_bid_his = self.block_bid_his[block_number]

        # Determine the winning bid and the ID of the winning builder for this block
        winning_bid = max(bid for counter_bids in block_bid_his for bid in counter_bids.values())
        winning_builder_id = [builder_id for counter_bids in block_bid_his for builder_id, bid in counter_bids.items() if bid == winning_bid][0]

        # Retrieve the strategies used in this specific block
        strategies_this_block = self.builder_strategies_per_block[block_number]

        # Generate unique colors for each builder
        colors = cm.rainbow(np.linspace(0, 1, len(self.builders)))

        for builder, color in zip(self.builders, colors):
            builder_bids = [block_bid_his[counter].get(builder.id, None) if counter < len(block_bid_his) else None for counter in range(24)]
            builder_strategy = strategies_this_block[builder.id]

            # Make the winning builder's line bolder
            linewidth = 2.5 if builder.id == winning_builder_id else 1.0
            linestyle = '-' if builder.id == winning_builder_id else '--'
            label = f"Builder {builder.id} ({builder_strategy})"
            if builder.id == winning_builder_id:
                label += " - Winner"

            plt.plot(range(24), builder_bids, label=label, color=color, alpha=0.7, linewidth=linewidth, linestyle=linestyle)

        plt.xlabel('Counter')
        plt.ylabel('Bid Value')
        plt.title(f'Bids for Block {block_number}')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_bid_value(self):
        plt.figure(figsize=(12, 6))

        block_numbers = list(range(len(self.winning_bid)))

        plt.plot(block_numbers, self.winning_bid, label='Winning Bid', color='green')
        plt.plot(block_numbers, self.winning_block_values, label='Block Value', color='blue')

        plt.xlabel('Block Number')
        plt.ylabel('Value')
        plt.title('Winning Bids and Block Values Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()

    def intra_rankings(self):
        intra_block_rankings = []

        for block_bid_his in self.block_bid_his:
            all_bids = [bid for counter_bids in block_bid_his for bid in counter_bids.values()]

            sorted_bids = sorted(all_bids, reverse=True)
            winning_bid = max(all_bids)

            rank = sorted_bids.index(winning_bid) + 1
            intra_block_rankings.append(rank)

        return intra_block_rankings

    def plot_intra_rankings(self):
        plt.figure(figsize=(12, 6))

        # Calculate intra-block rankings
        rankings = self.intra_rankings()

        # Plot the rankings
        plt.plot(range(len(rankings)), rankings, marker='o', linestyle='-')

        plt.xlabel('Block Number')
        plt.ylabel('Rank of Winning Bid Within Block')
        plt.title('Intra-Block Ranking of Winning Bids')
        plt.gca().invert_yaxis()  # Invert y-axis so that rank 1 appears at the top
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_cumulate_reward_strategy(self):
        plt.figure(figsize=(12, 6))

        #plot the cumulative reward for each strategy over blocks
        for strategy in STRATEGIES:
            cumulate_reward = np.cumsum([self.winning_block_values[i] - self.winning_bid[i] for i in range(len(self.winning_bid)) if self.winning_strategy[i] == strategy])
            plt.plot(range(len(cumulate_reward)), cumulate_reward, label=strategy)

        plt.xlabel('Block Number')
        plt.ylabel('Cumulative Reward')
        plt.title('Cumulative Reward Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()


# Run the simulation
simulation = Simulation(NUM_BUILDERS, NUM_BLOCKS)
simulation.run()
# simulation.plot_cumulative_win()
# simulation.plot_strategy_num()
# simulation.plot_bids_for_block(10)
simulation.plot_bid_value()
simulation.plot_intra_rankings()
# simulation.plot_cumulate_reward_strategy()