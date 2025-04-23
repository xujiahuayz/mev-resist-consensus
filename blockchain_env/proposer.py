from typing import List, Dict, Optional, Tuple
from blockchain_env.node import Node
from blockchain_env.builder import Builder
from blockchain_env.transaction import Transaction
import random

class Proposer(Node):
    def __init__(self, proposer_id: int) -> None:
        super().__init__(proposer_id)
        self.id: int = proposer_id
        self.current_block: int = 0
        self.current_round: int = 0
        self.max_rounds: int = 24  # Maximum number of rounds per block
        self.bids: Dict[int, Dict[int, float]] = {}  # {block: {builder_id: bid_amount}}
        self.winning_bids: Dict[int, Tuple[int, float]] = {}  # {block: (round, bid_amount)}
        self.end_rounds: Dict[int, int] = {}  # {block: end_round}
        self.all_observed_bids: Dict[int, Dict[int, float]] = {}  # {block: {round: bid_amount}}
        
    def start_new_block(self) -> None:
        """Start a new block and initialize the auction."""
        self.current_block += 1
        self.current_round = 0
        self.bids[self.current_block] = {}
        self.all_observed_bids[self.current_block] = {}
        
    def receive_bid(self, builder_id: int, bid_amount: float) -> None:
        """Receive a bid from a builder for the current round."""
        if self.current_block not in self.bids:
            self.bids[self.current_block] = {}
        self.bids[self.current_block][builder_id] = bid_amount
        # Track all observed bids for this round
        self.all_observed_bids[self.current_block][self.current_round] = bid_amount
        
    def end_round(self) -> None:
        """End the current round and determine if the auction should continue."""
        self.current_round += 1
        self.end_rounds[self.current_block] = self.current_round
        
    def select_winner(self) -> Optional[Tuple[int, float]]:
        """Select the winning bid for the current block."""
        if self.current_block not in self.bids or not self.bids[self.current_block]:
            return None
            
        # Find the highest bid in the current block
        highest_bid: float = 0.0
        winning_builder: int = -1
        winning_round: int = -1
        
        for round_num, bids in self.all_observed_bids[self.current_block].items():
            if bids > highest_bid:
                highest_bid = bids
                winning_builder = next((b_id for b_id, bid in self.bids[self.current_block].items() if bid == bids), -1)
                winning_round = round_num
                    
        if winning_builder != -1:
            self.winning_bids[self.current_block] = (winning_round, highest_bid)
            return (winning_builder, highest_bid)
        return None
        
    def adjust_auction_duration(self) -> None:
        """Adjust the auction duration based on the adaptive termination strategy."""
        if self.current_block <= 1:
            return  # Need at least one previous block to adjust
            
        prev_block = self.current_block - 1
        if prev_block not in self.winning_bids or prev_block not in self.end_rounds:
            return
            
        prev_winning_round, prev_winning_bid = self.winning_bids[prev_block]
        prev_end_round = self.end_rounds[prev_block]
        
        # Check all observed bids in the previous block
        higher_bid_after = False
        higher_bid_before = False
        
        for round_num, bid_amount in self.all_observed_bids[prev_block].items():
            if bid_amount > prev_winning_bid:
                if round_num > prev_end_round:
                    higher_bid_after = True
                elif round_num < prev_end_round:
                    higher_bid_before = True
                        
        # Adjust the maximum number of rounds based on the strategy
        if higher_bid_after:
            self.max_rounds = min(24, self.max_rounds + 1)
        elif higher_bid_before:
            self.max_rounds = max(1, self.max_rounds - 1)
            
    def get_block(self, builders: List[Builder]) -> Optional[List[Transaction]]:
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
