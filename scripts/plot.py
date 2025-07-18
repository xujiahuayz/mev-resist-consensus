# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,too-many-instance-attributes, too-many-arguments

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

class Plotting:
    def __init__(self, simulation):
        self.simulation = simulation

    def plot_cumulative_win(self, STRATEGIES):
        '''Plot the cumulative win for each strategy'''
        plt.figure(figsize=(12, 6))
        strategies_count = {strategy: [0] * self.simulation.num_blocks for strategy in STRATEGIES}
        for i, strategy in enumerate(self.simulation.winning_strategy):
            strategies_count[strategy][i] += 1
        for strategy, counts in strategies_count.items():
            plt.plot(range(self.simulation.num_blocks), np.cumsum(counts), label=strategy)
        plt.xlabel('Block Number')
        plt.ylabel('Cumulative Wins')
        plt.title('Strategy Trends Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_strategy_num(self, STRATEGIES):
        """Plot the number of builders for each strategy over blocks."""
        plt.figure(figsize=(12, 6))

        block_numbers = list(range(len(self.simulation.strategy_counts_per_block)))
        for strategy in STRATEGIES:
            counts = [count[strategy] for count in self.simulation.strategy_counts_per_block]
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
        block_bid_his = self.simulation.block_bid_his[block_number]

        # Determine the winning bid and the ID of the winning builder for this block
        winning_bid = max(bid for counter_bids in block_bid_his for bid in counter_bids.values())
        winning_builder_id = [builder_id for counter_bids in block_bid_his for
                              builder_id, bid in counter_bids.items() if bid == winning_bid][0]

        # Retrieve the strategies used in this specific block
        strategies_this_block = self.simulation.builder_strategies_per_block[block_number]

        # Generate unique colors for each builder
        colors = cm.rainbow(np.linspace(0, 1, len(self.simulation.builders)))

        for builder, color in zip(self.simulation.builders, colors):
            builder_bids = [block_bid_his[counter].get(builder.id, None)
                            if counter < len(block_bid_his) else None for counter in range(24)]
            builder_strategy = strategies_this_block[builder.id]

            # Make the winning builder's line bolder
            linewidth = 2.5 if builder.id == winning_builder_id else 1.0
            linestyle = '-' if builder.id == winning_builder_id else '--'
            label = f"Builder {builder.id} ({builder_strategy})"
            if builder.id == winning_builder_id:
                label += " - Winner"

            plt.plot(range(24), builder_bids, label=label, color=color, alpha=0.7,
                     linewidth=linewidth, linestyle=linestyle)

        plt.xlabel('Counter')
        plt.ylabel('Bid Value')
        plt.title(f'Bids for Block {block_number}')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_bid_value(self):
        plt.figure(figsize=(12, 6))

        block_numbers = list(range(len(self.simulation.winning_bid)))

        plt.plot(block_numbers, self.simulation.winning_bid, label='Winning Bid', color='green')
        plt.plot(block_numbers, self.simulation.winning_block_values, label='Block Value',
                 color='blue')

        plt.xlabel('Block Number')
        plt.ylabel('Value')
        plt.title('Winning Bids and Block Values Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()


    def plot_intra_rankings(self):
        plt.figure(figsize=(12, 6))

        # Calculate intra-block rankings
        rankings = self.simulation.intra_rankings()

        # Plot the rankings
        plt.plot(range(len(rankings)), rankings, marker='o', linestyle='-')

        plt.xlabel('Block Number')
        plt.ylabel('Rank of Winning Bid Within Block')
        plt.title('Intra-Block Ranking of Winning Bids')
        plt.gca().invert_yaxis()  # Invert y-axis so that rank 1 appears at the top
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_cumulate_reward_strategy(self, STRATEGIES):
        plt.figure(figsize=(12, 6))

        #plot the cumulative reward for each strategy over blocks
        for strategy in STRATEGIES:
            cumulate_reward = np.cumsum([self.simulation.winning_block_values[i]
                                         - self.simulation.winning_bid[i]
                                         for i in range(len(self.simulation.winning_bid))
                                         if self.simulation.winning_strategy[i] == strategy])
            plt.plot(range(len(cumulate_reward)), cumulate_reward, label=strategy)

        plt.xlabel('Block Number')
        plt.ylabel('Cumulative Reward')
        plt.title('Cumulative Reward Over Blocks')
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_proposers_cumulative_rewards(self):
        proposer_rewards = [proposer.cumulative_reward for proposer in self.simulation.proposers]

        plt.figure(figsize=(8, 6))
        plt.bar(range(len(self.simulation.proposers)), proposer_rewards, color='orange')
        plt.title('Proposers\' Cumulative Rewards')
        plt.xlabel('Proposer ID')
        plt.ylabel('Cumulative Reward')
        plt.xticks(range(len(self.simulation.proposers)))
        plt.show()

    def plot_builders_cumulative_rewards(self):
        builder_rewards = [builder.cumulative_reward for builder in self.simulation.builders]

        plt.figure(figsize=(8, 6))
        plt.bar(range(len(self.simulation.proposers)), builder_rewards, color='orange')
        plt.title('Builder\' Cumulative Rewards')
        plt.xlabel('Builder ID')
        plt.ylabel('Cumulative Reward')
        plt.xticks(range(len(self.simulation.builder)))
        plt.show()

    def plot_builders_profit_distribution(self):
        builder_profits = [builder.cumulative_reward for builder in self.simulation.builders]

        plt.figure(figsize=(8, 6))
        plt.hist(builder_profits, bins=10, color='skyblue', edgecolor='black')
        plt.title('Builders\' Profit Distribution')
        plt.xlabel('Profit')
        plt.ylabel('Number of Builders')
        plt.show()

    def plot_cumulative_reward_distribution(self):
        builders_cumulative_rewards = []
        proposers_cumulative_rewards = []
        time_steps = list(range(len(self.simulation.block_bid_his)))

        current_builders_reward = 0
        current_proposers_reward = 0
        for i in time_steps:
            current_builders_reward += sum(builder.cumulative_reward for builder in self.simulation.builders)
            current_proposers_reward += sum(proposer.cumulative_reward for proposer in self.simulation.proposers)
            builders_cumulative_rewards.append(current_builders_reward)
            proposers_cumulative_rewards.append(current_proposers_reward)

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(time_steps, builders_cumulative_rewards, label='Builders\' Total Cumulative Reward', color='blue')
        plt.plot(time_steps, proposers_cumulative_rewards, label='Proposers\' Total Cumulative Reward', color='orange')
        plt.title('Total Cumulative Reward Over Time')
        plt.xlabel('Block Number')
        plt.ylabel('Cumulative Reward')
        plt.legend()
        plt.show()

if __name__ == '__main__':
    print("plot.py loaded")
