"""Local (one-at-a-time / tornado) and global (Sobol) sensitivity analysis.

Both analyses call the *same* `compute_msp` model used by the live dashboard
calculator, so results here always match what the sliders show — unlike the
original project, where the Sobol script analyzed an unrelated toy function.
"""

import numpy as np
import pandas as pd

from .economics import compute_msp
from .process import PARAM_SPECS, ProcessParameters


def tornado_analysis(base_params: ProcessParameters, param_names=None) -> pd.DataFrame:
    """One-at-a-time sensitivity: sweep each parameter across its full slider
    range (holding all others at their current base value) and record the
    resulting swing in MSP. Returns a DataFrame sorted by impact, largest first.
    """
    if param_names is None:
        param_names = list(PARAM_SPECS.keys())

    base_msp = compute_msp(base_params)
    rows = []
    for name in param_names:
        spec = PARAM_SPECS[name]
        low_params = base_params.with_override(name, spec["min"])
        high_params = base_params.with_override(name, spec["max"])
        low_msp = compute_msp(low_params)
        high_msp = compute_msp(high_params)

        # A parameter can be inversely related to MSP (e.g. higher conversion
        # lowers MSP), so sort the pair before plotting as a bar range.
        lo, hi = sorted([low_msp, high_msp])
        rows.append(
            {
                "Parameter": spec["label"],
                "Low_MSP": lo,
                "High_MSP": hi,
                "Base_MSP": base_msp,
                "Impact": hi - lo,
                "Min_Input": spec["min"],
                "Max_Input": spec["max"],
                "Unit": spec["unit"],
            }
        )

    df = pd.DataFrame(rows).sort_values("Impact", ascending=True).reset_index(drop=True)
    return df


def global_sobol_analysis(param_names=None, n_samples: int = 512, seed: int = 42) -> pd.DataFrame:
    """Variance-based global sensitivity analysis (Sobol) over the full
    parameter space, using the real MSP model as the function of interest.

    Returns a DataFrame with first-order (S1) and total-order (ST) indices.
    """
    from SALib.analyze.sobol import analyze as sobol_analyze
    from SALib.sample.sobol import sample as sobol_sample

    if param_names is None:
        param_names = list(PARAM_SPECS.keys())

    problem = {
        "num_vars": len(param_names),
        "names": param_names,
        "bounds": [[PARAM_SPECS[n]["min"], PARAM_SPECS[n]["max"]] for n in param_names],
    }

    param_values = sobol_sample(problem, n_samples, calc_second_order=False, seed=seed)

    defaults = {f: getattr(ProcessParameters(), f) for f in ProcessParameters.field_names()}

    def msp_of(sample_row):
        kwargs = dict(defaults)
        for name, value in zip(param_names, sample_row):
            kwargs[name] = value
        return compute_msp(ProcessParameters(**kwargs))

    y = np.array([msp_of(row) for row in param_values])
    si = sobol_analyze(problem, y, calc_second_order=False, print_to_console=False)

    df = pd.DataFrame(
        {
            "Parameter": [PARAM_SPECS[n]["label"] for n in param_names],
            "S1": si["S1"],
            "S1_conf": si["S1_conf"],
            "ST": si["ST"],
            "ST_conf": si["ST_conf"],
        }
    ).sort_values("ST", ascending=False).reset_index(drop=True)
    return df
