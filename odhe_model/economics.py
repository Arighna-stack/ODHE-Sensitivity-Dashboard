"""Techno-economic cost model: cost breakdown and Minimum Selling Price (MSP)."""

from .process import DESIGN_BASIS, ProcessParameters


def cost_breakdown(p: ProcessParameters) -> dict:
    """Annual cost breakdown ($/yr) for a given scenario."""
    ethane_flow = p.ethane_flow_tph()
    oxygen_flow = p.oxygen_flow_tph()

    annualized_capex = p.capex * p.capital_recovery_factor()
    fixed_opex = p.fixed_opex_pct * p.capex
    ethane_cost = p.ethane_price * ethane_flow * p.operating_hours
    oxygen_cost = p.oxygen_price * oxygen_flow * p.operating_hours
    electricity_cost = p.electricity_price * DESIGN_BASIS.electricity_load_kw * p.operating_hours
    steam_cost = p.steam_price * DESIGN_BASIS.steam_load_tph * p.operating_hours
    refrigeration_cost = (
        p.refrigeration_price * DESIGN_BASIS.refrigeration_load_kw * p.operating_hours
    )

    total = (
        annualized_capex
        + fixed_opex
        + ethane_cost
        + oxygen_cost
        + electricity_cost
        + steam_cost
        + refrigeration_cost
    )

    return {
        "Annualized CAPEX": annualized_capex,
        "Fixed O&M": fixed_opex,
        "Ethane Feedstock": ethane_cost,
        "Oxygen": oxygen_cost,
        "Electricity": electricity_cost,
        "Steam": steam_cost,
        "Refrigeration": refrigeration_cost,
        "Total Annual Cost": total,
    }


def ethylene_production_annual(p: ProcessParameters) -> float:
    """Annual ethylene output (tons/yr) at nameplate capacity."""
    return DESIGN_BASIS.ethylene_capacity_tph * p.operating_hours


def compute_msp(p: ProcessParameters) -> float:
    """Minimum Selling Price of ethylene ($/ton)."""
    total_cost = cost_breakdown(p)["Total Annual Cost"]
    return total_cost / ethylene_production_annual(p)
