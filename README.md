# MEV-resistant consensus mechanism

[![python](https://img.shields.io/badge/Python-v3.11.3-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![build status](https://github.com/pre-commit/pre-commit/actions/workflows/main.yml/badge.svg)](https://github.com/xujiahuayz/pbs/actions/workflows/pylint.yml)

The repository simulates maximal extractable value (MEV) attacks and models a new MEV-resistant consensus mechanism.

## Setup

```
git clone https://github.com/xujiahuayz/pbs.git
cd pbs
```

### Give execute permission to your script and then run `setup_repo.sh`

```
chmod +x setup_repo.sh
./setup_repo.sh
. venv/bin/activate
```

or follow the step-by-step instructions below between the two horizontal rules:

---

#### Create a python virtual environment

- MacOS / Linux

```bash
python3 -m venv venv
```

- Windows

```bash
python -m venv venv
```

#### Activate the virtual environment

- MacOS / Linux

```bash
. venv/bin/activate
```

- Windows (in Command Prompt, NOT Powershell)

```bash
venv\Scripts\activate.bat
```
#### Install toml

```
pip install toml
```

#### Install the project in editable mode

```bash
pip install -e ".[dev]"
```

#### Install pre-commit
```bash
pre-commit install
```

---

## Code Structure and Figure Generation Guide

This project analyzes MEV (Maximal Extractable Value) dynamics in PoS and PBS systems. The codebase is organized as follows:

- **plots/ss/**: Contains Python scripts for generating figures and data analysis.
- **figures/ss/**: Stores the output figures (PNGs) and intermediate data (JSON/CSV) used in the paper.
- **data/**: Contains raw and processed data used for analysis.

### Mapping Paper Figures to Code

| Paper Figure | Output File(s) in `figures/ss/` | Script(s) in `plots/ss/` | How to Generate |
|--------------|----------------------------------|--------------------------|-----------------|
| **Figure 4**<br>Side-by-side comparison of cumulative block production by MEV-seeking vs. non-MEV-seeking participants. | `pos_cumulative_selection_3x3_grid.png`<br>`pbs_cumulative_selection_3x3_grid.png` | `pos_selection_3x3.py`<br>`pbs_selection_3x3.py` | Run:<br>`python plots/ss/pos_selection_3x3.py`<br>`python plots/ss/pbs_selection_3x3.py` |
| **Figure 5**<br>MEV profit distribution among users, validators, and uncaptured MEV. | `pos_mev_distribution_user_attack_0.png`<br>`pos_mev_distribution_user_attack_12.png`<br>`pos_mev_distribution_user_attack_24.png`<br>`pos_mev_distribution_user_attack_50.png`<br>`pbs_mev_distribution_user_attack_0.png`<br>`pbs_mev_distribution_user_attack_12.png`<br>`pbs_mev_distribution_user_attack_24.png`<br>`pbs_mev_distribution_user_attack_50.png` | `pos_profit.py`<br>`pbs_profit.py` | Run:<br>`python plots/ss/pos_profit.py`<br>`python plots/ss/pbs_profit.py` |
| **Figure 6**<br>Example auction within a block (bid trajectory). | `bid_dynamics_selected_block.png` | `bidding_dynamic.py` | Run:<br>`python plots/ss/bidding_dynamic.py` |
| **Figure 7**<br>Block value over rounds for each builder. | `block_value_dynamics_selected_block.png` | `bidding_dynamic.py` | Run:<br>`python plots/ss/bidding_dynamic.py` |
| **Figure 8**<br>Inversion Count Heatmaps. | `inversion_counts_for_pos.png`<br>`inversion_counts_for_pbs.png` | `tx_order.py` | Run:<br>`python plots/ss/tx_order.py` |

---
