import pandas as pd
import streamlit as st

GRAMS_PER_LB = 453.59237
FILE = "D6_Specs_Database.xlsx"

st.set_page_config(page_title="Plastic + PCR Calculator", page_icon="♻️")
st.title("♻️ Plastic + PCR Calculator")

@st.cache_data
def load_data():
    df = pd.read_excel(FILE)
    df["Vendor Part Number"] = df["Vendor Part Number"].astype(str).str.strip()
    return df

df = load_data()

part = st.text_input("Vendor Part Number").strip()
units = st.number_input("Units purchased", min_value=0, step=1000, value=0)

if part and units:
    row = df[df["Vendor Part Number"] == part]

    if row.empty:
        st.error("Part number not found.")
    else:
        r = row.iloc[0]
        grams = float(r["Item Weight (g)"])
        pcr_pct = float(r["PCR Content %"]) if pd.notna(r["PCR Content %"]) else 0.0

        plastic_lbs = (grams * units) / GRAMS_PER_LB
        pcr_lbs = plastic_lbs * (pcr_pct / 100)
# =========================
# Impact comparison: miles driven equivalent
# =========================

KG_PER_LB = 0.45359237
DEFAULT_CO2E_SAVED_KG_PER_KG_RPET = 1.70  # editable assumption
MTCO2E_PER_MILE = 3.93e-4  # EPA gasoline passenger vehicle

# Optional assumptions control
with st.sidebar:
    st.subheader("Impact assumptions")
    co2e_saved_kg_per_kg = st.number_input(
        "kg CO₂e avoided per kg rPET (vs virgin PET)",
        min_value=0.0,
        value=DEFAULT_CO2E_SAVED_KG_PER_KG_RPET,
        step=0.05
    )

# Calculations
co2e_saved_kg_per_lb = co2e_saved_kg_per_kg * KG_PER_LB
co2e_saved_kg = pcr_lbs * co2e_saved_kg_per_lb
co2e_saved_metric_tons = co2e_saved_kg / 1000

miles_equivalent = co2e_saved_metric_tons / MTCO2E_PER_MILE

st.subheader("Results")
st.metric("Plastic used (lbs)", f"{plastic_lbs:,.2f}")
st.metric("PCR used (lbs)", f"{pcr_lbs:,.2f}")
st.subheader("PCR Impact")

st.metric("Pounds of PCR used", f"{pcr_lbs:,.1f} lb")
st.metric("Estimated CO₂e avoided", f"{co2e_saved_metric_tons:,.3f} metric tons")
st.metric("Equivalent gasoline miles avoided", f"{miles_equivalent:,.0f} miles")

with st.popover("Methodology"):
    st.markdown("""
**How this is calculated**
- PCR used (lb) = total plastic (lb) × PCR content %
- CO₂e avoided = PCR used × CO₂e savings per lb rPET

**Assumptions**
- Virgin PET ≈ 2.15 kg CO₂e/kg  
- rPET ≈ 0.45 kg CO₂e/kg  
- Difference = **1.70 kg CO₂e/kg rPET** (adjustable)

**EPA equivalency**
- Gasoline passenger vehicle: **3.93×10⁻4 metric tons CO₂e per mile**

**Disclaimer**
Results are estimates. Actual impacts vary by resin source, PCR process,
electricity grid, and transport distances.
""")
