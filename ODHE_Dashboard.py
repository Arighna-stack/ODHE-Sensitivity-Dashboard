import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="ODHE Sensitivity Dashboard", layout="wide")

st.title("🧠 ODHE Techno-Economic Sensitivity Dashboard")

st.markdown("""
This dashboard estimates the **Minimum Selling Price (MSP)** of ethylene produced by the ODHE process based on key variable costs.
Adjust the sliders to see how MSP changes with different economic parameters.
""")

# Sidebar Inputs
st.sidebar.header("🔧 Adjust Parameters")

ethane_price = st.sidebar.slider('Ethane Price ($/ton)', 800, 1300, 1000, step=50)
electricity_price = st.sidebar.slider('Electricity Price ($/kWh)', 0.05, 0.10, 0.07, step=0.01)
steam_price = st.sidebar.slider('Steam Price ($/ton)', 10, 25, 15, step=1)
refrigeration_price = st.sidebar.slider('Refrigeration Price ($/kWh)', 0.03, 0.08, 0.05, step=0.01)

# Constants
hours_per_year = 8000
ethylene_production_annual = 91.6 * hours_per_year  # tons/year
capex = 220_000_000  # USD
opex_base = 578_000_000  # USD/year

# Annualized CAPEX
discount_rate = 0.1
plant_lifetime = 20
annualized_capex = capex * (discount_rate * (1 + discount_rate) ** plant_lifetime) / ((1 + discount_rate) ** plant_lifetime - 1)

# Feed and utility rates
ethane_flow = 113  # tons/hr
oxygen_flow = 29   # tons/hr
electricity_load = 30 * 1000  # kW
steam_load = 150 * 1000       # kW equivalent
refrigeration_load = 250 * 1000  # kW

# MSP Calculation
ethane_cost = ethane_price * ethane_flow * hours_per_year
oxygen_cost = 100 * oxygen_flow * hours_per_year
electricity_cost = electricity_price * electricity_load * hours_per_year
steam_cost = steam_price * steam_load * hours_per_year / 1000
refrigeration_cost = refrigeration_price * refrigeration_load * hours_per_year

total_annual_cost = annualized_capex + opex_base + ethane_cost + oxygen_cost + electricity_cost + steam_cost + refrigeration_cost
msp = total_annual_cost / ethylene_production_annual

st.metric(label="💰 MSP (Minimum Selling Price)", value=f"${msp:,.2f} per ton ethylene")

# Sensitivity Plot for Ethane Price
ethane_prices = np.linspace(800, 1300, 6)
msp_ethane = []
for p in ethane_prices:
    ethane_cost = p * ethane_flow * hours_per_year
    total_cost = annualized_capex + opex_base + ethane_cost + oxygen_cost + electricity_cost + steam_cost + refrigeration_cost
    msp_value = total_cost / ethylene_production_annual
    msp_ethane.append(msp_value)

fig, ax = plt.subplots(figsize=(8,5))
ax.plot(ethane_prices, msp_ethane, marker='o')
ax.set_title('MSP vs Ethane Price')
ax.set_xlabel('Ethane Price ($/ton)')
ax.set_ylabel('MSP ($/ton ethylene)')
ax.grid(True)
st.pyplot(fig)

st.markdown("""---  
Made with ❤️ using Streamlit  
""")
