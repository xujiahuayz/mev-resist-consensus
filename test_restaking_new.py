#!/usr/bin/env python3

import sys
sys.path.append('.')

from blockchain_env.restaking_pbs import update_stake, VALIDATOR_THRESHOLD

class TestParticipant:
    pass

def test_restaking_new():
    print(f"Testing with new validator threshold: {VALIDATOR_THRESHOLD} gwei ({VALIDATOR_THRESHOLD/1e9:.3f} ETH)")
    
    p = TestParticipant()
    p.capital = 64000000000  # 64 ETH
    p.reinvestment_factor = 0.5  # 50% restaking
    p.profit_history = []
    p.stake_history = [p.capital]
    
    print(f"\nInitial state:")
    print(f"  Capital: {p.capital} gwei ({p.capital/1e9:.2f} ETH)")
    print(f"  Active stake: {p.capital} gwei ({p.capital/1e9:.2f} ETH)")
    print(f"  Capital // Threshold: {p.capital // VALIDATOR_THRESHOLD}")
    
    # Test with typical profits from the simulation
    profits = [30000000, 50000000, 70000000]  # 0.03, 0.05, 0.07 ETH
    
    for i, profit in enumerate(profits):
        print(f"\n--- Profit {i+1}: {profit} gwei ({profit/1e9:.6f} ETH) ---")
        
        # Reset participant
        p.capital = 64000000000
        p.active_stake = 64000000000
        p.profit_history = []
        p.stake_history = [p.capital]
        
        update_stake(p, profit)
        
        print(f"  After profit:")
        print(f"    Capital: {p.capital} gwei ({p.capital/1e9:.6f} ETH)")
        print(f"    Active stake: {p.active_stake} gwei ({p.active_stake/1e9:.6f} ETH)")
        print(f"    Capital // Threshold: {p.capital // VALIDATOR_THRESHOLD}")
        print(f"    Stake increase: {(p.active_stake - 64000000000) / 1e9:.6f} ETH")
    
    # Test with larger profits that should definitely cause stake increases
    print(f"\n--- Testing with larger profits ---")
    large_profits = [1000000000, 2000000000, 5000000000]  # 1, 2, 5 ETH
    
    for profit in large_profits:
        print(f"\nLarge profit: {profit} gwei ({profit/1e9:.2f} ETH)")
        
        p2 = TestParticipant()
        p2.capital = 64000000000
        p2.reinvestment_factor = 0.5
        p2.profit_history = []
        p2.stake_history = [p2.capital]
        
        update_stake(p2, profit)
        stake_increase = (p2.active_stake - 64000000000) / 1e9
        print(f"  Stake increase: {stake_increase:.6f} ETH")

if __name__ == "__main__":
    test_restaking_new() 