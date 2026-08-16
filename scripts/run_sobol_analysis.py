"""CLI entry point for the global Sobol sensitivity analysis.

Runs against the *same* MSP model used by the Streamlit dashboard (see
odhe_model/economics.py) and writes indices + a bar chart to results/.
"""

import os
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from odhe_model import global_sobol_analysis  # noqa: E402

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def main(n_samples: int = 1024):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    df = global_sobol_analysis(n_samples=n_samples)
    csv_path = os.path.join(RESULTS_DIR, "odhe_sensitivity_indices.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved indices to {csv_path}")

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(df))
    ax.bar([i - 0.2 for i in x], df["S1"], width=0.4, label="S1 (first-order)")
    ax.bar([i + 0.2 for i in x], df["ST"], width=0.4, label="ST (total-order)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["Parameter"], rotation=30, ha="right")
    ax.set_ylabel("Sensitivity Index")
    ax.set_title("ODHE MSP — Global Sobol Sensitivity")
    ax.legend()
    plt.tight_layout()

    plot_path = os.path.join(RESULTS_DIR, "odhe_sensitivity_plot.png")
    plt.savefig(plot_path, dpi=150)
    print(f"Saved plot to {plot_path}")


if __name__ == "__main__":
    main()
