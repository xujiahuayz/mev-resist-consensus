from typing import List, Dict, Tuple
from blockchain_env.node import Node
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
import random

class Proposer(Node):
    def __init__(self, proposer_id: int) -> None:
        super().__init__(proposer_id)
        self.current_round: int = 0
        self.max_rounds: int = 24  # Maximum number of rounds per block
        self.bids: Dict[int, float] = {}  # {builder_id: bid_amount}
        self.all_observed_bids: Dict[int, float] = {}  # {round: bid_amount}
        self.winning_bid: Tuple[int, float] | None = None  # (round, bid_amount)
        self.end_round: int | None = None
        
    def receive_bid(self, builder_id: int, bid_amount: float) -> None:
        """Receive a bid from a builder for the current round."""
        self.bids[builder_id] = bid_amount
        # Track all observed bids for this round
        self.all_observed_bids[self.current_round] = bid_amount
        
    def end_round(self) -> None:
        """End the current round and determine if the auction should continue."""
        self.current_round += 1
        self.end_round = self.current_round
        
    def select_winner(self) -> Tuple[int, float] | None:
        """Select the winning bid for the current block.
        """
        if not self.bids:
            return None
            
        # Find the highest bid across all rounds
        highest_bid: float = 0.0
        winning_round: int = -1
        
        # First find the highest bid amount and its round
        for round_num, bid_amount in self.all_observed_bids.items():
            if bid_amount > highest_bid:
                highest_bid = bid_amount
                winning_round = round_num
                
        if winning_round == -1:
            return None  # No valid bids found
            
        # Now find the builder who made this bid
        winning_builder = None
        for builder_id, bid_amount in self.bids.items():
            if bid_amount == highest_bid:
                winning_builder = builder_id
                break
                
        if winning_builder is None:
            # This should never happen in normal operation as we track bids in both structures
            raise ValueError("Found highest bid but no matching builder. Data inconsistency detected.")
            
        self.winning_bid = (winning_round, highest_bid)
        return (winning_builder, highest_bid)
        
    def adjust_auction_duration(self, prev_winning_bid: Tuple[int, float] | None, prev_end_round: int | None) -> None:
        """Adjust the auction duration based on the adaptive termination strategy."""
        if prev_winning_bid is None or prev_end_round is None:
            return
            
        prev_winning_round, prev_winning_amount = prev_winning_bid
        
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
        self.end_round = None
