# MEV-resistant consensus mechanism

[![python](https://img.shields.io/badge/Python-v3.11.3-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![build status](https://github.com/pre-commit/pre-commit/actions/workflows/main.yml/badge.svg)](https://github.com/xujiahuayz/mev-resist-consensus/actions/workflows/pylint.yml)

The repository simulates maximal extractable value (MEV) attacks and models a new MEV-resistant consensus mechanism.

## Setup

```
git clone https://github.com/xujiahuayz/mev-resist-consensus.git
cd mev-resist-consensus
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

### Figure 4 & 5: Theoretical Restaking Plots
Generates theoretical plots showing builder and proposer growth rates and stake evolution over time.
```bash
python plots/theory/restaking.py
```

### Figure 6: Comparison of Block Production by Attack and Benign Participants
Generates heatmaps showing the proportion of blocks built by attacking participants for PoS and PBS.
```bash
python plots/ss/block_build_proportions.py
```

### Figure 7: Side-by-Side Comparison of the Percentage of MEV Profit
Generates stacked area plots showing MEV profit distribution among validators/builders, users, and uncaptured MEV for PoS and PBS.
```bash
python plots/ss/pos_profit.py
python plots/ss/pbs_profit.py
```

### Figure 8: Auction Bids Over Time
Generates a plot showing bid dynamics across auction rounds for a selected block.
```bash
python plots/ss/bidding_dynamic.py
```

### Figure 9: Block Valuations vi,t Over Rounds
Generates a plot showing block value dynamics across auction rounds for a selected block.
```bash
python plots/ss/bidding_dynamic.py
```

### Figure 10: Stake Evolution Over 10,000 Blocks for Participants with Different Initial Stakes
Generates three separate plots showing stake evolution for PoS validators, PBS builders, and PBS proposers with different initial stake levels.
```bash
python plots/ss/plot_restaking.py
```

### Figure 11: Inversion Count Heatmaps Under Varying Numbers of MEV-Seeking Participants
Generates heatmaps showing transaction ordering inversion counts for PoS and PBS under different configurations of MEV-seeking participants.
```bash
python plots/ss/tx_order.py
```
