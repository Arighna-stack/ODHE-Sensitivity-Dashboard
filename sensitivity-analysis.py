import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure results folder exists
results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(results_dir, exist_ok=True)

# -- SALib imports --
from SALib.sample.sobol import sample as sobol_sample   # sampler
from SALib.analyze.sobol import analyze as sobol_analyze  # analyzer

# Define your problem
problem = {
    'num_vars': 3,
    'names': ['conversion', 'selectivity', 'C2H6_O2_ratio'],
    'bounds': [[0.30, 0.80], [0.60, 0.95], [1.0, 3.0]]
}

# Generate samples
param_values = sobol_sample(problem, 1024, calc_second_order=False)

# Your TEA function
def odhe_tea(conv, sel, ratio):
    revenue = 1000 * conv * sel
    opex    = 200 * (1 - conv) + 100 * (1 - sel)
    capex   = 500 * ratio
    return revenue - opex - capex

# Run TEA
Y = np.array([odhe_tea(*params) for params in param_values])

# Perform analysis
Si = sobol_analyze(problem, Y, calc_second_order=False, print_to_console=False)

# Save indices
df_Si = pd.DataFrame({
    'Parameter': problem['names'],
    'S1': Si['S1'],
    'ST': Si['ST']
})
df_Si.to_csv(os.path.join(results_dir, 'odhe_sensitivity_indices.csv'), index=False)

# Plot
fig, ax = plt.subplots()
x = np.arange(len(problem['names']))
ax.bar(x - 0.2, Si['S1'], width=0.4, label='S1')
ax.bar(x + 0.2, Si['ST'], width=0.4, label='ST')
ax.set_xticks(x)
ax.set_xticklabels(problem['names'], rotation=20, ha='right')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(results_dir, 'odhe_sensitivity_plot.png'))
