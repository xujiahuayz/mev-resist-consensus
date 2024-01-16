import random

class Builder:
    def __init__(self, id):
        self.id = id
        self.block = []
        self.bid = 0

    def create_block(self, transactions):
        self.block = transactions
        self.bid = random.uniform(0, sum(transaction[1] for transaction in transactions))

    def update_bid(self, new_bid):
        self.bid = min(new_bid, sum(transaction[1] for transaction in self.block))

class Proposer:
    def __init__(self):
        self.builder_bids = []

    def start_auction(self, builders):
        self.builder_bids = [(builder.id, builder.bid) for builder in builders]

    def end_auction(self):
        if self.builder_bids:
            winner_id, winning_bid = max(self.builder_bids, key=lambda x: x[1])
            return winner_id, winning_bid
        else:
            return None, 0

def simulate_game(num_builders, num_transactions, num_blocks):
    builders = [Builder(i) for i in range(num_builders)]
    proposer = Proposer()

    for _ in range(num_blocks):
        # Generate random transactions
        transactions = [(f"Transaction{i}", random.uniform(1, 10)) for i in range(num_transactions)]

        # Builders create blocks and submit bids
        for builder in builders:
            builder.create_block(transactions)

        # Proposer starts auction
        proposer.start_auction(builders)

        # Builders compete in the auction
        for _ in range(random.randint(1, 10)):  # Simulate auction rounds
            for builder in builders:
                builder.update_bid(builder.bid + random.uniform(-5, 5))

        # Proposer ends the auction and selects the winner
        winner_id, winning_bid = proposer.end_auction()

        if winner_id is not None:
            winner = next(builder for builder in builders if builder.id == winner_id)
            print(f"Block { _ + 1 }: Winner - Builder {winner.id}, Winning Bid - {winning_bid}")
            # Reward the winner and proposer
            winner_reward = sum(transaction[1] for transaction in winner.block) - winning_bid
            proposer_reward = winning_bid
            print(f"Builder {winner.id} Reward: {winner_reward}, Proposer Reward: {proposer_reward}")
        else:
            print(f"No winner for Block { _ + 1 }")

# Example simulation
simulate_game(num_builders=5, num_transactions=10, num_blocks=3)
