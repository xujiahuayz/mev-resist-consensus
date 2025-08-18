#!/usr/bin/env python3

import sys
sys.path.append('.')

from blockchain_env.restaking_pbs import update_stake, VALIDATOR_THRESHOLD

class TestParticipant:
    pass

def test_restaking():
    p = TestParticipant()
    p.capital = 160000000000  # 160 ETH
    p.reinvestment_factor = 0.5  # 50% restaking
    p.profit_history = []
    p.stake_history = [p.capital]
    
    print(f"Initial capital: {p.capital} gwei ({p.capital/1e9:.2f} ETH)")
    print(f"Initial active_stake: {p.capital} gwei ({p.capital/1e9:.2f} ETH)")
    print(f"Validator threshold: {VALIDATOR_THRESHOLD} gwei ({VALIDATOR_THRESHOLD/1e9:.2f} ETH)")
    
    # Test with a typical profit
    profit = 30000000  # 30 million gwei = 0.03 ETH
    print(f"\nProfit: {profit} gwei ({profit/1e9:.6f} ETH)")
    
    update_stake(p, profit)
    
    print(f"After profit - Capital: {p.capital} gwei ({p.capital/1e9:.2f} ETH)")
    print(f"After profit - Active stake: {p.active_stake} gwei ({p.active_stake/1e9:.2f} ETH)")
    print(f"Capital // Threshold: {p.capital // VALIDATOR_THRESHOLD}")
    
    # Calculate how much stake should increase
    stake_increase = (p.active_stake - p.capital + profit) / 1e9
    print(f"Stake increase: {stake_increase:.6f} ETH")
    
    # Test with larger profits
    print(f"\n--- Testing with larger profits ---")
    for i in range(1, 6):
        large_profit = 1000000000 * i  # 1-5 ETH
        print(f"\nLarge profit: {large_profit} gwei ({large_profit/1e9:.2f} ETH)")
        
        p2 = TestParticipant()
        p2.capital = 160000000000
        p2.reinvestment_factor = 0.5
        p2.profit_history = []
        p2.stake_history = [p2.capital]
        
        update_stake(p2, large_profit)
        stake_increase = (p2.active_stake - p2.capital + large_profit) / 1e9
        print(f"Stake increase: {stake_increase:.6f} ETH")

if __name__ == "__main__":
    test_restaking() 