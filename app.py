import pandas as pd
import streamlit as st

FILE_PATH = "CSGG.xlsx"
GRAMS_PER_POUND = 453.59237

st.set_page_config(page_title="Plastic + PCR Calculator", page_icon="♻️", layout="centered")

# Simple styling (optional but makes it feel less spreadsheet-y)
st.markdown(
    """
    <style>
      .block-container {max-width: 820px;}
      div[data-testid="stMetricValue"] {font-size: 32px;}
      .hint {opacity: 0.8; font-size: 0.95rem;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("♻️ Plastic + PCR Calculator")
st.caption("Enter a vendor part number and annual units to estimate plastic and PCR usage.")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Normalize the key fields for matching
    df["Vendor Part Number"] = df["Vendor Part Number"].astype(str).str.strip()
    return df

df = load_data(FILE_PATH)

# Inputs
col1, col2 = st.columns([2, 1])
with col1:
    part = st.text_input("Vendor Part Number", placeholder="e.g., 3001").strip()
with col2:
    units = st.number_input("Units purchased", min_value=0, step=1000, value=0)

st.markdown('<div class="hint">Tip: part numbers must match the database. If you want partial matching, I can add it.</div>', unsafe_allow_html=True)

if part and units:
    match = df[df["Vendor Part Number"] == part]

    if match.empty:
        st.error("Part number not found in the database.")
        st.stop()

    row = match.iloc[0]

    # Pull fields
    desc = row.get("Item Description", "")
    material = row.get("Material", "")
    gram_weight = row.get("Item Weight (g)", None)
    pcr_pct = row.get("PCR Content %", 0)

    # Validate numbers
    if pd.isna(gram_weight):
        st.error("This part is missing Item Weight (g).")
        st.stop()

    try:
        gram_weight = float(gram_weight)
    except Exception:
        st.error("Item Weight (g) is not a number for this part.")
        st.stop()

    # PCR % could be blank
    pcr_pct = 0 if pd.isna(pcr_pct) else float(pcr_pct)

    # Calculations
    total_grams = gram_weight * units
    plastic_lbs = total_grams / GRAMS_PER_POUND
    pcr_lbs = plastic_lbs * (pcr_pct / 100.0)

    # Display
    st.subheader("Result")
    st.write(f"**{part}**  |  {desc}  |  {material}  |  PCR: {pcr_pct:.1f}%")
    st.write(f"Item weight: **{gram_weight:,.2f} g/unit**")

    m1, m2 = st.columns(2)
    m1.metric("Total Plastic Used (lbs)", f"{plastic_lbs:,.2f}")
    m2.metric("Total PCR Used (lbs)", f"{pcr_lbs:,.2f}")

    with st.expander("Show calculation details"):
        st.write(f"Total grams = {gram_weight:,.2f} × {units:,.0f} = {total_grams:,.0f} g")
        st.write(f"Plastic lbs = {total_grams:,.0f} / {GRAMS_PER_POUND} = {plastic_lbs:,.2f} lbs")
        st.write(f"PCR lbs = {plastic_lbs:,.2f} × ({pcr_pct:.1f}/100) = {pcr_lbs:,.2f} lbs")

else:
    st.info("Enter a vendor part number and units purchased to calculate usage.")
