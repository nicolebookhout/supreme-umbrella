import pandas as pd
import streamlit as st

GRAMS_PER_LB = 453.59237
FILE = "D6_Specs_Database.xlsx"

st.set_page_config(page_title="Nicole's Super Awesome Calculator", page_icon="♻️")
st.title("♻️ Nicole's Super Awesome Calculator")

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
        # Impact comparison: CO2e avoided
        # =========================
        KG_PER_LB = 0.45359237

with st.sidebar:
    st.subheader("Gigaton assumptions")
    co2e_saved_kg_per_kg = st.number_input(
        "kg CO₂e avoided per kg PCR (vs virgin)",
        min_value=0.0,
        value=1.70,   # TEMP placeholder until you replace with Walmart/Gigaton factor(s)
        step=0.05
    )

pcr_kg = pcr_lbs * KG_PER_LB
co2e_avoided_kg = pcr_kg * co2e_saved_kg_per_kg
co2e_avoided_metric_tons = co2e_avoided_kg / 1000.0
        

        st.subheader("PCR Impact (Project Gigaton)")
        st.metric("Estimated CO₂e emissions avoided", f"{co2e_avoided_metric_tons:,.3f} metric tons CO₂e")
        

        st.subheader("PCR Impact")
        st.metric("Estimated CO₂e avoided", f"{co2e_saved_metric_tons:,.3f} metric tons")
        

        with st.popover("Methodology (Project Gigaton)"):
    st.markdown("""
This calculator estimates **CO₂e emissions avoided** from PCR content using:

**CO₂e avoided (kg) = PCR mass (kg) × (EF_virgin − EF_PCR)**

Where the emissions factor difference is set using the assumption in the sidebar.
For Project Gigaton reporting, use the same emissions factor approach and boundaries
described in Walmart’s Project Gigaton Accounting Methodology.

- Walmart Project Gigaton Accounting Methodology (PDF): https://www.walmartsustainabilityhub.com/content/dam/walmart-sustainability-hub/documents/project-gigaton/project-gigaton-accounting-methodology.pdf
""")

**Disclaimer**
Results are estimates. Actual impacts vary by resin source, PCR process,
electricity grid, and transport distances.
""")
else:
    st.info("Enter a vendor part number and units to calculate.")

