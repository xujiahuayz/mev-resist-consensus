import matplotlib.pyplot as plt
import numpy as np

from scripts.generate import total_proposer_balance, total_builder_balance


def plot_distribution(total_proposer_balance: list[float], total_builder_balance: list[float], initial_balance: float):
    block_numbers = np.arange(len(total_proposer_balance))  # Create an array of block numbers

    # Calculate the total profit (ignoring initial balances) for each block
    total_profit_proposer = np.array(total_proposer_balance) - len(total_proposer_balance) * [initial_balance]
    total_profit_builder = np.array(total_builder_balance) - len(total_builder_balance) * [initial_balance]

    # Calculate the total profit for each block
    total_profit = total_profit_proposer + total_profit_builder

    # Calculate the percentage of proposer and builder profit for each block
    proposer_percentage = (total_profit_proposer / total_profit) * 100
    builder_percentage = (total_profit_builder / total_profit) * 100

    plt.figure(figsize=(10, 6))
    plt.stackplot(block_numbers, proposer_percentage, builder_percentage, labels=['Proposer Profit', 'Builder Profit'], alpha=0.7)
    plt.plot(block_numbers, np.ones_like(block_numbers) * 100, color='black', linestyle='--', label='Total (100%)')
    plt.xlabel('Block Number')
    plt.ylabel('Percentage')
    plt.legend(loc='upper left')
    plt.grid(False)
    plt.title('Percentage Distribution of Proposer and Builder Profits Over Blocks (Ignoring Initial Balances)')
    plt.show()
    plt.savefig('figures/profit_distribution.pdf')

if __name__ == "__main__":
    plot_distribution(total_proposer_balance, total_builder_balance, 1000.0)
