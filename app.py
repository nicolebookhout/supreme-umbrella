import pandas as pd
import streamlit as st

# -------------------------
# Config / Constants
# -------------------------
GRAMS_PER_LB = 453.59237
KG_PER_LB = 0.45359237

FILE = "D6_Specs_Database.xlsx"

# Default placeholder until you replace with your Walmart/Gigaton-approved factor
DEFAULT_CO2E_AVOIDED_KG_PER_KG_PCR = 1.70  # kg CO2e avoided per kg PCR vs virgin

WALMART_GIGATON_METHODOLOGY_URL = (
    "https://www.walmartsustainabilityhub.com/content/dam/walmart-sustainability-hub/"
    "documents/project-gigaton/project-gigaton-accounting-methodology.pdf"
)

st.set_page_config(page_title="Plastic + PCR Calculator", page_icon="♻️")
st.title("♻️ Plastic + PCR Calculator")


# -------------------------
# Data Load
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(FILE)
    # Normalize part numbers to strings w/ trimmed whitespace
    df["Vendor Part Number"] = df["Vendor Part Number"].astype(str).str.strip()
    return df

df = load_data()


# -------------------------
# Sidebar: Assumptions
# -------------------------
with st.sidebar:
    st.header("Assumptions")
    co2e_avoided_kg_per_kg_pcr = st.number_input(
        "kg CO₂e avoided per kg PCR (vs virgin)",
        min_value=0.0,
        value=DEFAULT_CO2E_AVOIDED_KG_PER_KG_PCR,
        step=0.05,
        help=(
            "Set this to the factor difference your team uses for Walmart Project Gigaton reporting "
            "(virgin EF minus PCR EF)."
        ),
    )


# -------------------------
# Inputs
# -------------------------
part = st.text_input("Vendor Part Number").strip()
units = st.number_input("Units purchased", min_value=0, step=1000, value=0)


# -------------------------
# Calculation + Output
# -------------------------
if part and units > 0:
    row = df[df["Vendor Part Number"] == part]

    if row.empty:
        st.error("Part number not found.")
    else:
        r = row.iloc[0]

        # Pull needed fields (with basic safety)
        grams = float(r["Item Weight (g)"])
        pcr_pct = float(r["PCR Content %"]) if pd.notna(r.get("PCR Content %")) else 0.0

        # Mass calculations
        plastic_lbs = (grams * units) / GRAMS_PER_LB
        pcr_lbs = plastic_lbs * (pcr_pct / 100.0)

        # Gigaton-style CO2e avoided calculation
        pcr_kg = pcr_lbs * KG_PER_LB
        co2e_avoided_kg = pcr_kg * co2e_avoided_kg_per_kg_pcr
        co2e_avoided_metric_tons = co2e_avoided_kg / 1000.0

        # Results
        st.subheader("Results")
        st.metric("Plastic used (lbs)", f"{plastic_lbs:,.2f}")
        st.metric("PCR used (lbs)", f"{pcr_lbs:,.2f}")

        st.subheader("PCR Impact (Project Gigaton style)")
        st.metric("Estimated CO₂e emissions avoided", f"{co2e_avoided_metric_tons:,.3f} metric tons CO₂e")

        # Methodology hover
        with st.popover("Methodology (Project Gigaton)"):
            st.markdown(
                f"""
**What this represents**  
An estimate of **CO₂e emissions avoided** from using PCR content instead of virgin resin.

**Formula used**  
- PCR used (lb) = total plastic (lb) × PCR content %  
- PCR used (kg) = PCR used (lb) × 0.45359237  
- **CO₂e avoided (kg) = PCR used (kg) × (EF_virgin − EF_PCR)**  

In this app, **(EF_virgin − EF_PCR)** is entered in the sidebar as:  
**“kg CO₂e avoided per kg PCR (vs virgin)”**

**Walmart Project Gigaton methodology**  
This output is intended to align to the general “activity data × emissions factor” approach used in Walmart’s Project Gigaton Accounting Methodology (boundaries and factor selection should follow your internal guidance):  
{WALMART_GIGATON_METHODOLOGY_URL}

**Notes**  
- Actual results depend on resin type, geography/electricity grid, PCR process, transport, and system boundaries.  
- Replace the sidebar factor with the official Walmart/Gigaton factor(s) your team uses for reporting.
"""
            )
else:
    st.info("Enter a vendor part number and units purchased to calculate.")
