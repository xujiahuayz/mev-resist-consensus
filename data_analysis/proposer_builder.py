import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Load the data
df = pd.read_csv('pbs_c/cmake-build-debug/pbsBlocks.csv')

# Analyze the data
print(df.describe())