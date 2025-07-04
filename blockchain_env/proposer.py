"""Proposer module for blockchain environment."""

import random
from typing import List, Dict, Tuple, Any

from blockchain_env.network import Node
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction

random.seed(16)

class Proposer(Node):
    def __init__(self, proposer_id: int) -> None:
        super().__init__(proposer_id)
        self.current_round: int = 0
        self.max_rounds: int = 24  # Maximum number of rounds per block
        self.bids: Dict[int, float] = {}  # {builder_id: bid_amount}
        self.all_observed_bids: Dict[int, float] = {}  # {round: bid_amount}
        self.winning_bid: Tuple[int, float] | None = None  # (round, bid_amount)
        self.end_round_num: int | None = None

    def receive_bid(self, builder_id: int, bid_amount: Any) -> None:
        """Receive a bid from a builder for the current round."""
        # Convert bid_amount to float if it's not already
        if isinstance(bid_amount, (int, float)):
            bid_amount_float: float = float(bid_amount)
            self.bids[builder_id] = bid_amount_float
            # Track all observed bids for this round
            self.all_observed_bids[self.current_round] = bid_amount_float

    def end_round(self) -> None:
        """End the current round and determine if the auction should continue."""
        self.current_round += 1
        self.end_round_num = self.current_round

    def select_winner(self) -> Tuple[int, float] | None:
        """Select the winning bid for the current block."""
        if not self.bids:
            return None

        # Find the highest bid and its builder
        highest_bid: float = 0.0
        winning_builder: int = -1

        for builder_id, bid_amount in self.bids.items():
            if bid_amount > highest_bid:
                highest_bid = bid_amount
                winning_builder = builder_id

        if winning_builder == -1:
            return None  # No valid bids found

        return (winning_builder, highest_bid)

    def adjust_auction_duration(self, prev_winning_bid: Tuple[int, float] | None, prev_end_round: int | None) -> None:
        """Adjust the auction duration based on the adaptive termination strategy."""
        if prev_winning_bid is None or prev_end_round is None:
            return

        _, prev_winning_amount = prev_winning_bid

        # Check all observed bids in the previous block
        higher_bid_after = False
        higher_bid_before = False

        for round_num, bid_amount in self.all_observed_bids.items():
            if bid_amount > prev_winning_amount:
                if round_num > prev_end_round:
                    higher_bid_after = True
                elif round_num < prev_end_round:
                    higher_bid_before = True

        # Adjust the maximum number of rounds based on the strategy
        if higher_bid_after:
            self.max_rounds = min(24, self.max_rounds + 1)
        elif higher_bid_before:
            self.max_rounds = max(1, self.max_rounds - 1)

    def get_block(self, builders: List[Builder]) -> List[Transaction] | None:
        """Get the block from the winning builder."""
        winner = self.select_winner()
        if winner is None:
            return None

        winning_builder_id, _ = winner
        winning_builder = next((b for b in builders if b.id == winning_builder_id), None)

        if winning_builder:
            return winning_builder.get_selected_transactions()
        return None

    def is_auction_complete(self) -> bool:
        """Check if the current auction has reached its maximum rounds."""
        return self.current_round >= self.max_rounds

    def reset_for_new_block(self) -> None:
        """Reset the proposer's state for a new block."""
        self.current_round = 0
        self.bids.clear()
        self.all_observed_bids.clear()
        self.winning_bid = None
        self.end_round_num = None
