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

## Run scripts

Below are the commands to generate each figure in the paper. Copy and paste each command into your terminal as needed.

### Figure 4: Block Build Proportions
Generates block build proportions plots for PoS and PBS showing the percentage of attacking vs benign entities at block 1000.
```bash
python plots/ss/block_build_proportions.py
```

### Figure 5: MEV Profit Distribution
Generates MEV profit distribution plots for PoS and PBS.
```bash
python plots/ss/pos_profit.py
python plots/ss/pbs_profit.py
```

### Figure 6 & 7: Auction Bid and Block Value Dynamics
Generates auction bid and block value dynamics plots.
```bash
python plots/ss/bidding_dynamic.py
```

### Figure 8: Inversion Count Heatmaps
Generates inversion count heatmaps for PoS and PBS.
```bash
python plots/ss/tx_order.py
```
