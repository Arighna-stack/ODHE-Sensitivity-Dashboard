"""Process design basis and parameter definitions for the ODHE techno-economic model.

This module is the single source of truth for every adjustable input in the
dashboard. Each entry in PARAM_SPECS drives three things at once: the sidebar
slider, the bounds used for local (tornado) sensitivity, and the bounds used
for global (Sobol) sensitivity — so the UI and the sensitivity analyses can
never drift out of sync with each other.
"""

from dataclasses import dataclass, fields


# ---------------------------------------------------------------------------
# Fixed design basis (nameplate capacity, from the ODHE process simulation).
# These are not decision variables — they describe the plant as designed.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DesignBasis:
    ethylene_capacity_tph: float = 91.6      # t/hr, nameplate ethylene output
    base_ethane_flow_tph: float = 113.0      # t/hr, ethane feed at baseline conv/sel
    electricity_load_kw: float = 30_000.0    # kW
    steam_load_tph: float = 150.0            # t/hr steam consumption
    refrigeration_load_kw: float = 250_000.0  # kW


DESIGN_BASIS = DesignBasis()


# ---------------------------------------------------------------------------
# Parameter specification: name -> (label, unit, min, max, default, step, group)
# ---------------------------------------------------------------------------
PARAM_SPECS = {
    "ethane_price": dict(
        label="Ethane Price", unit="$/ton", min=700.0, max=1400.0, default=1000.0,
        step=10.0, group="Feedstock & Market",
    ),
    "oxygen_price": dict(
        label="Oxygen Price", unit="$/ton", min=50.0, max=200.0, default=100.0,
        step=5.0, group="Feedstock & Market",
    ),
    "electricity_price": dict(
        label="Electricity Price", unit="$/kWh", min=0.03, max=0.12, default=0.07,
        step=0.005, group="Utilities",
    ),
    "steam_price": dict(
        label="Steam Price", unit="$/ton", min=8.0, max=30.0, default=15.0,
        step=1.0, group="Utilities",
    ),
    "refrigeration_price": dict(
        label="Refrigeration Price", unit="$/kWh", min=0.02, max=0.10, default=0.05,
        step=0.005, group="Utilities",
    ),
    "conversion": dict(
        label="Ethane Conversion", unit="fraction", min=0.30, max=0.80, default=0.60,
        step=0.01, group="Process Performance",
    ),
    "selectivity": dict(
        label="Ethylene Selectivity", unit="fraction", min=0.60, max=0.95, default=0.85,
        step=0.01, group="Process Performance",
    ),
    "c2h6_o2_ratio": dict(
        label="C2H6 : O2 Feed Ratio", unit="mol/mol", min=2.0, max=6.0, default=3.9,
        step=0.1, group="Process Performance",
    ),
    "capex": dict(
        label="Total CAPEX", unit="$", min=150_000_000.0, max=300_000_000.0,
        default=220_000_000.0, step=5_000_000.0, group="Financial",
    ),
    "fixed_opex_pct": dict(
        label="Fixed O&M (% of CAPEX/yr)", unit="fraction", min=0.02, max=0.08,
        default=0.04, step=0.005, group="Financial",
    ),
    "discount_rate": dict(
        label="Discount Rate", unit="fraction", min=0.06, max=0.14, default=0.10,
        step=0.005, group="Financial",
    ),
    "plant_lifetime": dict(
        label="Plant Lifetime", unit="years", min=15.0, max=25.0, default=20.0,
        step=1.0, group="Financial",
    ),
    "operating_hours": dict(
        label="Operating Hours", unit="hr/yr", min=7000.0, max=8400.0, default=8000.0,
        step=100.0, group="Financial",
    ),
}

# Baseline conversion/selectivity, used to anchor the feed-flow scaling so the
# design basis (113 t/hr ethane, 91.6 t/hr ethylene) is reproduced exactly at
# default slider values.
_BASE_CONVERSION = PARAM_SPECS["conversion"]["default"]
_BASE_SELECTIVITY = PARAM_SPECS["selectivity"]["default"]


@dataclass
class ProcessParameters:
    """A single scenario: one value per adjustable parameter."""

    ethane_price: float = PARAM_SPECS["ethane_price"]["default"]
    oxygen_price: float = PARAM_SPECS["oxygen_price"]["default"]
    electricity_price: float = PARAM_SPECS["electricity_price"]["default"]
    steam_price: float = PARAM_SPECS["steam_price"]["default"]
    refrigeration_price: float = PARAM_SPECS["refrigeration_price"]["default"]
    conversion: float = PARAM_SPECS["conversion"]["default"]
    selectivity: float = PARAM_SPECS["selectivity"]["default"]
    c2h6_o2_ratio: float = PARAM_SPECS["c2h6_o2_ratio"]["default"]
    capex: float = PARAM_SPECS["capex"]["default"]
    fixed_opex_pct: float = PARAM_SPECS["fixed_opex_pct"]["default"]
    discount_rate: float = PARAM_SPECS["discount_rate"]["default"]
    plant_lifetime: float = PARAM_SPECS["plant_lifetime"]["default"]
    operating_hours: float = PARAM_SPECS["operating_hours"]["default"]

    @classmethod
    def field_names(cls):
        return [f.name for f in fields(cls)]

    def with_override(self, name: str, value: float) -> "ProcessParameters":
        """Return a copy with a single parameter replaced (used for OAT sensitivity)."""
        kwargs = {f: getattr(self, f) for f in self.field_names()}
        kwargs[name] = value
        return ProcessParameters(**kwargs)

    def ethane_flow_tph(self) -> float:
        """Ethane feed rate needed to hit nameplate ethylene output, adjusted
        for conversion/selectivity efficiency relative to the design basis."""
        efficiency_ratio = (_BASE_CONVERSION / self.conversion) * (
            _BASE_SELECTIVITY / self.selectivity
        )
        return DESIGN_BASIS.base_ethane_flow_tph * efficiency_ratio

    def oxygen_flow_tph(self) -> float:
        return self.ethane_flow_tph() / self.c2h6_o2_ratio

    def capital_recovery_factor(self) -> float:
        r, n = self.discount_rate, self.plant_lifetime
        return (r * (1 + r) ** n) / ((1 + r) ** n - 1)
