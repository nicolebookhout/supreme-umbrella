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

        st.subheader("Results")
        st.metric("Plastic used (lbs)", f"{plastic_lbs:,.2f}")
        st.metric("PCR used (lbs)", f"{pcr_lbs:,.2f}")
