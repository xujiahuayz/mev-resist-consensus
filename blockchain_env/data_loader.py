"""Data loader for real Ethereum blockchain data fetched from different periods."""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import numpy as np

class EthereumDataLoader:
    """Loads and samples real Ethereum data from fetched periods."""
    
    def __init__(self, data_path: str = "data/fetch"):
        self.data_path = Path(data_path)
        self.periods_data = {}
        self.load_all_periods()
    
    def load_all_periods(self):
        """Load data from all available periods."""
        if not self.data_path.exists():
            print(f"Warning: Data path {self.data_path} does not exist. Run fetch scripts first.")
            return
        
        for period_dir in self.data_path.iterdir():
            if period_dir.is_dir() and not period_dir.name.startswith('.'):
                self.load_period_data(period_dir.name)
    
    def load_period_data(self, period_name: str):
        """Load data from a specific period."""
        period_path = self.data_path / period_name
        if not period_path.exists():
            return
        
        gas_fees = []
        transaction_data = []
        
        # Load all block files in the period
        for block_file in period_path.glob("block_*.json"):
            try:
                with open(block_file, 'r', encoding='utf-8') as f:
                    block_data = json.load(f)
                
                # Extract gas fees and transaction data
                if 'gas_fees_gwei' in block_data:
                    gas_fees.extend(block_data['gas_fees_gwei'])
                
                if 'transactions' in block_data:
                    transaction_data.extend(block_data['transactions'])
                    
            except Exception as e:
                print(f"Error loading {block_file}: {e}")
        
        self.periods_data[period_name] = {
            'gas_fees': gas_fees,
            'transactions': transaction_data,
            'total_transactions': len(transaction_data)
        }
        
        print(f"Loaded {period_name}: {len(gas_fees)} gas fees, {len(transaction_data)} transactions")
    
    def get_period_names(self) -> List[str]:
        """Get list of available period names."""
        return list(self.periods_data.keys())
    
    def get_period_info(self) -> Dict:
        """Get information about all loaded periods."""
        info = {}
        for period_name, data in self.periods_data.items():
            info[period_name] = {
                'total_transactions': data['total_transactions'],
                'gas_fee_stats': {
                    'mean': np.mean(data['gas_fees']) if data['gas_fees'] else 0,
                    'median': np.median(data['gas_fees']) if data['gas_fees'] else 0,
                    'std': np.std(data['gas_fees']) if data['gas_fees'] else 0,
                    'min': np.min(data['gas_fees']) if data['gas_fees'] else 0,
                    'max': np.max(data['gas_fees']) if data['gas_fees'] else 0
                }
            }
        return info
    
    def get_periods_by_type(self, period_type: str) -> List[str]:
        """Get period names by type (high_volatility, stable)."""
        return [name for name in self.periods_data if period_type.upper() in name]
    
    def get_periods_by_era(self, era: str) -> List[str]:
        """Get period names by era (pre_merge, post_merge)."""
        return [name for name in self.periods_data if era.upper() in name]
    
    def sample_gas_fees(self, 
                       period_name: Optional[str] = None, 
                       n_samples: int = 100,
                       strategy: str = "random") -> List[float]:
        """
        Sample gas fees from a specific period or all periods.
        
        Args:
            period_name: Specific period to sample from, or None for all periods
            n_samples: Number of samples to return
            strategy: Sampling strategy ("random", "stratified")
        
        Returns:
            List of gas fees in Gwei
        """
        if not self.periods_data:
            print("Warning: No data loaded. Returning empty list.")
            return []
        
        if period_name and period_name not in self.periods_data:
            print(f"Warning: Period {period_name} not found. Sampling from all periods.")
            period_name = None
        
        if period_name:
            # Sample from specific period
            gas_fees = self.periods_data[period_name]['gas_fees']
            if strategy == "stratified":
                return self._stratified_sample(gas_fees, n_samples)
            else:
                return random.sample(gas_fees, min(n_samples, len(gas_fees)))
        else:
            # Sample from all periods
            all_gas_fees = []
            for period_data in self.periods_data.values():
                all_gas_fees.extend(period_data['gas_fees'])
            
            if strategy == "stratified":
                return self._stratified_sample(all_gas_fees, n_samples)
            else:
                return random.sample(all_gas_fees, min(n_samples, len(all_gas_fees)))
    
    def sample_transactions(self, 
                          period_name: Optional[str] = None,
                          n_samples: int = 100) -> List[Dict]:
        """
        Sample transaction data from a specific period or all periods.
        
        Args:
            period_name: Specific period to sample from, or None for all periods
            n_samples: Number of samples to return
        
        Returns:
            List of transaction dictionaries
        """
        if not self.periods_data:
            return []
        
        if period_name and period_name not in self.periods_data:
            print(f"Warning: Period {period_name} not found. Sampling from all periods.")
            period_name = None
        
        if period_name:
            transactions = self.periods_data[period_name]['transactions']
        else:
            all_transactions = []
            for period_data in self.periods_data.values():
                all_transactions.extend(period_data['transactions'])
            transactions = all_transactions
        
        return random.sample(transactions, min(n_samples, len(transactions)))
    
    def get_mev_potentials(self, 
                           period_name: Optional[str] = None,
                           n_samples: int = 100) -> List[float]:
        """
        Generate MEV potentials based on transaction values and gas fees.
        This is an approximation since we don't have direct MEV data.
        
        Args:
            period_name: Specific period to sample from, or None for all periods
            n_samples: Number of samples to return
        
        Returns:
            List of MEV potential values
        """
        transactions = self.sample_transactions(period_name, n_samples)
        mev_potentials = []
        
        for tx in transactions:
            # Simple MEV potential calculation based on transaction value and gas
            value_eth = tx.get('value_eth', 0)
            gas_fee_gwei = tx.get('gas_fee_gwei', 0)
            
            # MEV potential = transaction value * some factor - gas costs
            # This is a simplified model
            mev_potential = max(0, value_eth * 1000 - gas_fee_gwei * 0.000001)
            mev_potentials.append(mev_potential)
        
        return mev_potentials
    
    def _stratified_sample(self, data: List[float], n_samples: int) -> List[float]:
        """Stratified sampling to ensure representation across the distribution."""
        if len(data) <= n_samples:
            return data
        
        # Sort data and take samples from different parts of the distribution
        sorted_data = sorted(data)
        step = len(sorted_data) / n_samples
        samples = []
        
        for i in range(n_samples):
            idx = int(i * step)
            samples.append(sorted_data[idx])
        
        return samples
    
    def sample_by_era(self, 
                     era: str, 
                     n_samples: int = 100,
                     data_type: str = "gas_fees") -> Union[List[float], List[Dict]]:
        """
        Sample data from a specific era (pre_merge or post_merge).
        
        Args:
            era: "pre_merge" or "post_merge"
            n_samples: Number of samples to return
            data_type: "gas_fees", "transactions", or "mev_potentials"
        
        Returns:
            Sampled data
        """
        era_periods = self.get_periods_by_era(era)
        if not era_periods:
            print(f"Warning: No periods found for era {era}")
            return []
        
        # Sample from all periods in the era
        all_data = []
        for period_name in era_periods:
            if data_type == "gas_fees":
                all_data.extend(self.periods_data[period_name]['gas_fees'])
            elif data_type == "transactions":
                all_data.extend(self.periods_data[period_name]['transactions'])
        
        if data_type == "mev_potentials":
            return self.get_mev_potentials(era_periods[0], n_samples)
        else:
            return random.sample(all_data, min(n_samples, len(all_data)))
    
    def get_simulation_data(self, 
                           period_type: str = None, 
                           era: str = None,
                           n_samples: int = 100) -> Dict:
        """
        Get data specifically formatted for simulation testing.
        
        Args:
            period_type: "high_volatility" or "stable"
            era: "pre_merge" or "post_merge"
            n_samples: Number of samples to return
        
        Returns:
            Dictionary with simulation-ready data
        """
        if period_type and era:
            # Get specific combination
            periods = [p for p in self.periods_data 
                      if period_type.upper() in p and era.upper() in p]
        elif period_type:
            periods = self.get_periods_by_type(period_type)
        elif era:
            periods = self.get_periods_by_era(era)
        else:
            periods = list(self.periods_data.keys())
        
        if not periods:
            return {}
        
        # Sample from the selected periods
        all_gas_fees = []
        all_transactions = []
        
        for period_name in periods:
            period_data = self.periods_data[period_name]
            all_gas_fees.extend(period_data['gas_fees'])
            all_transactions.extend(period_data['transactions'])
        
        # Sample the requested amount
        sampled_gas_fees = random.sample(all_gas_fees, min(n_samples, len(all_gas_fees)))
        sampled_transactions = random.sample(all_transactions, min(n_samples, len(all_transactions)))
        
        return {
            'periods_used': periods,
            'gas_fees': sampled_gas_fees,
            'transactions': sampled_transactions,
            'mev_potentials': self.get_mev_potentials(periods[0], n_samples),
            'metadata': {
                'period_type': period_type,
                'era': era,
                'total_samples': len(sampled_gas_fees),
                'source_periods': periods
            }
        }


# Convenience functions for easy access
def get_real_gas_fees(period_name: Optional[str] = None, n_samples: int = 100) -> List[float]:
    """Get real gas fees from fetched Ethereum data."""
    loader = EthereumDataLoader()
    return loader.sample_gas_fees(period_name, n_samples)

def get_real_mev_potentials(period_name: Optional[str] = None, n_samples: int = 100) -> List[float]:
    """Get MEV potentials based on real transaction data."""
    loader = EthereumDataLoader()
    return loader.get_mev_potentials(period_name, n_samples)

def get_real_transactions(period_name: Optional[str] = None, n_samples: int = 100) -> List[Dict]:
    """Get real transaction data from fetched Ethereum data."""
    loader = EthereumDataLoader()
    return loader.sample_transactions(period_name, n_samples)

def get_simulation_data(period_type: str = None, era: str = None, n_samples: int = 100) -> Dict:
    """Get simulation-ready data for specific period types or eras."""
    loader = EthereumDataLoader()
    return loader.get_simulation_data(period_type, era, n_samples)


