import matplotlib.pyplot as plt
import numpy as np

def plot_distribution(total_proposer_balance: list[float], total_builder_balance: list[float],
                      initial_balance: float):
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
    plt.stackplot(block_numbers, proposer_percentage, builder_percentage,
                  labels=['Proposer Profit', 'Builder Profit'], alpha=0.7)
    plt.plot(block_numbers, np.ones_like(block_numbers) * 100, color='black',
             linestyle='--', label='Total (100%)')
    plt.xlabel('Block Number')
    plt.ylabel('Percentage')
    plt.legend(loc='upper left')
    plt.grid(False)
    plt.title('Percentage Distribution of Proposer and Builder Profits Over Blocks')
    plt.show()
    plt.savefig('./profit_distribution.pdf')
    pass

def plot_payoff():

    # Constants
    k = 0.1
    T_avg = 100
    T_values = [50, 100, 150]

    # Bid range
    b = np.linspace(0, 100, 400)

    plt.figure(figsize=(10, 6))

    # Plot for each T value
    for T in T_values:
        P_acceptance = np.minimum(1, np.exp(-k * b) * T / T_avg)
        plt.plot(b, P_acceptance, label=f'T={T}')

    plt.title('Probability of Acceptance vs Bid')
    plt.xlabel('Bid (b)')
    plt.ylabel('Probability of Acceptance')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    plot_payoff()
