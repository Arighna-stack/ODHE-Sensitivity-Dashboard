# ODHE Techno-Economic Sensitivity Dashboard ⚗️

An interactive **Streamlit dashboard** for the techno-economic analysis of ethylene
production via **Oxidative Dehydrogenation of Ethane (ODHE)**. It computes the
**Minimum Selling Price (MSP)** of ethylene from feedstock, utility, process, and
financial inputs, and quantifies which of those inputs actually drive economic
risk using both local (tornado) and global (Sobol) sensitivity analysis.

## Why this exists

Techno-economic models are only useful if you know which assumptions matter.
This dashboard doesn't just report a single MSP number — it lets you interrogate
the model: sweep every parameter across its plausible range (tornado analysis),
and quantify variance contribution and interaction effects across the full
parameter space (Sobol global sensitivity), all against the *same* underlying
cost model so the two analyses always agree with each other and with the live
calculator.

## Features

- 🔧 **13 adjustable parameters** across four groups — feedstock & market prices,
  utilities, process performance (conversion, selectivity, feed ratio), and
  financials (CAPEX, discount rate, plant lifetime, operating hours)
- 💰 **Real-time MSP calculation** with a full annual cost breakdown (bar +
  pie charts) and margin vs. a user-set ethylene market price
- 🌪️ **Tornado chart** — one-at-a-time sensitivity across each parameter's
  full range, sorted by impact on MSP
- 🌐 **Global Sobol sensitivity** — variance-based first-order (S1) and
  total-order (ST) indices computed via [SALib](https://salib.readthedocs.io/),
  capturing interaction effects the tornado chart can't see
  (cached, adjustable sample size)
- 📥 **CSV export** for the current scenario, cost breakdown, tornado results,
  and Sobol indices

## Architecture

```
ODHE_Dashboard.py        # Streamlit UI — sliders, tabs, charts
odhe_model/
  process.py             # ProcessParameters + PARAM_SPECS (single source of truth
                          # for slider bounds, tornado ranges, and Sobol bounds)
  economics.py            # Cost breakdown & MSP calculation
  sensitivity.py           # Tornado (OAT) and Sobol (global) analysis —
                            # both call the same compute_msp() as the live UI
scripts/
  run_sobol_analysis.py    # CLI entry point, writes results/*.csv and *.png
```

Every input parameter is declared once, in `odhe_model/process.py`. The sidebar
sliders, the tornado sweep ranges, and the Sobol sampling bounds all read from
that one definition, so the UI and both sensitivity analyses can never drift
out of sync.

## How to Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
streamlit run ODHE_Dashboard.py
```

The app opens at `http://localhost:8501`.

### Run the standalone Sobol analysis (CLI)

```bash
python scripts/run_sobol_analysis.py
```

Writes `results/odhe_sensitivity_indices.csv` and `results/odhe_sensitivity_plot.png`.

## Deploying

The repo is ready for [Streamlit Community Cloud](https://streamlit.io/cloud):
point it at `ODHE_Dashboard.py` as the main file — `requirements.txt` and
`.streamlit/config.toml` (theme) are already in place.

## Modeling notes

- Ethylene output is held at nameplate capacity (91.6 t/hr); ethane feed rate
  scales inversely with conversion × selectivity relative to the design
  basis, so lower process efficiency shows up as higher feedstock cost rather
  than lower output.
- CAPEX is annualized with the standard capital recovery factor,
  `CRF = r(1+r)^n / ((1+r)^n - 1)`.
- Fixed O&M is modeled as an adjustable **% of CAPEX/year** rather than a
  hardcoded constant, which is standard TEA practice and keeps the assumption
  transparent and testable.
- This is a screening-level model meant to demonstrate sensitivity-analysis
  methodology, not a substitute for a rigorous Aspen/HYSYS-based cost estimate.

## Tech Stack

Streamlit · Plotly · pandas · NumPy · [SALib](https://salib.readthedocs.io/) (Sobol sampling/analysis) · matplotlib (CLI script only)
