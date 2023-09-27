"""This file contains the configuration settings for the market environment."""

from blockchain_env.settings import PROJECT_ROOT

DATA_PATH = PROJECT_ROOT / "data"
FIGURE_PATH = PROJECT_ROOT / "figures"
CACHE_PATH = PROJECT_ROOT / ".cache"

BASE_FEE = 10
GAS_LIMIT = 30000000
BUILDER_STRATEGY_LIST = ["greedy", "random", "FCFS"]
PROPOSER_STRATEGY_LIST = ["greedy", "random", "cheap"]