"""Builder module for blockchain environment."""

import random
from copy import deepcopy
from typing import List

from blockchain_env.transaction import Transaction
from blockchain_env.network import Node

BLOCK_CAP: int = 100

class Builder(Node):
    """Builder class with attack and bidding logic."""
    def __init__(self, builder_id: int, is_attacker: bool, initial_stake: int = 0, restaking_factor: float = None) -> None:
        """Initialize a Builder."""
        super().__init__(builder_id, restaking_factor)
        self.is_attacker: bool = is_attacker
        self.balance: int = 0
        self.selected_transactions: List[Transaction] = []
        self.strategy: str = "reactive"  # Default to reactive strategy
        self.bid_history: List[float] = []
        
        # Initialize stake for restaking
        if initial_stake > 0:
            self.capital = initial_stake
            self.active_stake = initial_stake

    def launch_attack(self, block_num: int, target_transaction: Transaction, attack_type: str) -> Transaction:
        """Launch an attack transaction targeting a specific transaction."""
        if attack_type == 'front':
            gas_fee: int = target_transaction.gas_fee + 1
        else:
            gas_fee: int = target_transaction.gas_fee - 1
        mev_potential: int = 0
        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Transaction = target_transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction: Transaction) -> None:
        """Receive a transaction and add to mempool if not duplicate."""
        if transaction not in self.mempool:
            self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num: int) -> List[Transaction]:
        """Select transactions for block proposal."""
        selected_transactions: List[Transaction] = []
        if self.is_attacker:
            self.mempool.sort(key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) >= BLOCK_CAP:
                    break
                if transaction.mev_potential > 0:
                    attack_type: str = random.choice(['front', 'back'])
                    attack_transaction: Transaction = self.launch_attack(block_num, transaction, attack_type)
                    if attack_type == 'front':
                        selected_transactions.append(attack_transaction)
                        if len(selected_transactions) < BLOCK_CAP:
                            selected_transactions.append(transaction)
                    elif attack_type == 'back':
                        selected_transactions.append(transaction)
                        if len(selected_transactions) < BLOCK_CAP:
                            selected_transactions.append(attack_transaction)
                else:
                    selected_transactions.append(transaction)
        else:
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) >= BLOCK_CAP:
                    break
                selected_transactions.append(transaction)
        
        self.selected_transactions = selected_transactions[:BLOCK_CAP]
        return self.selected_transactions

    def bid(self, selected_transactions: List[Transaction]) -> float:
        """Calculate the builder's bid for the block using reactive strategy."""
        total_gas_fee: float = sum(tx.gas_fee for tx in selected_transactions)
        block_value: float = total_gas_fee
        if self.is_attacker:
            mev_gain: float = sum(tx.target_tx.mev_potential for tx in selected_transactions if hasattr(tx, 'target_tx') and tx.target_tx)
            block_value += mev_gain
        
        # Reactive bidding strategy
        if not self.bid_history:
            # First bid: start with 50% of block value
            bid: float = block_value * 0.5
        else:
            my_last_bid: float = self.bid_history[-1]
            # Reactive adjustment based on previous bid
            if my_last_bid < block_value * 0.8:
                # Increase bid if too low
                bid = min(block_value * 0.9, my_last_bid * 1.1)
            else:
                # Maintain competitive bid
                bid = max(block_value * 0.7, my_last_bid * 0.95)
        
        # Add small random variation
        bid = bid * random.uniform(0.98, 1.02)
        self.bid_history.append(bid)
        return bid

    def get_mempool(self) -> List[Transaction]:
        """Get the builder's mempool."""
        return self.mempool

    def clear_mempool(self, block_num: int) -> None:
        """Clear transactions included onchain or too old from the mempool."""
        timer: int = block_num - 5
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at < timer]
    
    def receive_block_reward(self, block_reward: int) -> None:
        """Receive block reward and update stake."""
        self.update_stake(block_reward)
    
    def get_selected_transactions(self) -> List[Transaction]:
        """Get the selected transactions for this block."""
        return self.selected_transactions.copy()
    
    def calculate_block_value(self) -> float:
        """Calculate the value of the block exactly like in bidding.py."""
        if not self.selected_transactions:
            return 0.0
        
        gas_fee = sum(tx.gas_fee for tx in self.selected_transactions)
        mev_value = 0.0
        
        if self.is_attacker:
            # MEV value from attack transactions (like in bidding.py)
            for tx in self.selected_transactions:
                if hasattr(tx, 'target_tx') and tx.target_tx:
                    mev_value += getattr(tx.target_tx, 'mev_potential', 0)
        
        return gas_fee + mev_value
