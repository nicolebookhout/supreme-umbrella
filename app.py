import pandas as pd
import streamlit as st

GRAMS_PER_LB = 453.59237

# If your file is in the root of your GitHub repo, this is correct.
# Use the REAL filename including extension.
# Examples: "CSGG.xlsx" or "CSGG.csv"
POSSIBLE_FILES = ["CSGG.xlsx", "CSGG.xls", "CSGG.csv", "CSGG"]


st.set_page_config(page_title="Plastic + PCR Calculator", page_icon="♻️", layout="centered")
st.title("♻️ Plastic + PCR Calculator")
st.caption("Look up a part by Vendor Part Number, enter units purchased, and calculate lbs of plastic + PCR.")


def _normalize_col(col: str) -> str:
    """Normalize column names so we can match even if formatting differs."""
    return (
        str(col)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("-", " ")
        .replace("_", " ")
    )


def _find_first_existing_file() -> str:
    # Streamlit Cloud runs from repo root, so a plain filename works.
    for f in POSSIBLE_FILES:
        try:
            # A cheap existence check: attempt open via pandas with 0 rows read
            if f.lower().endswith(".csv"):
                pd.read_csv(f, nrows=1)
                return f
            elif f.lower().endswith((".xlsx", ".xls")):
                pd.read_excel(f, nrows=1)
                return f
            else:
                # If user typed "CSGG" with no extension, try both
                try:
                    pd.read_excel(f + ".xlsx", nrows=1)
                    return f + ".xlsx"
                except Exception:
                    pd.read_csv(f + ".csv", nrows=1)
                    return f + ".csv"
        except Exception:
            continue
    return ""


@st.cache_data
def load_data() -> pd.DataFrame:
    file_path = _find_first_existing_file()
    if not file_path:
        raise FileNotFoundError(
            "Could not find your CSGG file in the app directory. "
            "Make sure it is in the repo root and named like CSGG.xlsx or CSGG.csv."
        )

    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # Normalize columns
    df.columns = [_normalize_col(c) for c in df.columns]

    # Map expected columns (flexible matching)
    # REQUIRED: vendor part number, gram weight
    # OPTIONAL: description, gauge
    col_map = {}

    def pick_col(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    col_map["vendor_part_number"] = pick_col(
        ["vendor part number", "vendor part #", "vendor part", "vendor pn", "vendorpartnumber", "part number", "part #"]
    )
    col_map["description"] = pick_col(
        ["description", "item description", "part description", "item"]
    )
    col_map["gauge"] = pick_col(
        ["gauge", "thickness", "caliper"]
    )
    col_map["gram_weight"] = pick_col(
        ["gram weight", "gram weight (g)", "grams", "weight (g)", "item weight (g)", "item weight g", "item weight"]
    )
    col_map["pcr_percent"] = pick_col(
        ["pcr", "pcr %", "pcr percent", "pcr percentage", "pcr content", "pcr content %"]
    )

    missing = [k for k in ["vendor_part_number", "gram_weight"] if not col_map.get(k)]
    if missing:
        raise ValueError(
            "Your CSGG file is missing required columns. "
            "Required: Vendor Part Number and Gram Weight.\n\n"
            f"Detected columns: {list(df.columns)}"
        )

    # Build a clean view
    out = pd.DataFrame()
    out["vendor_part_number"] = df[col_map["vendor_part_number"]].astype(str).str.strip()
    out["description"] = df[col_map["description"]] if col_map["description"] else ""
    out["gauge"] = df[col_map["gauge"]] if col_map["gauge"] else ""
    out["gram_weight_g"] = pd.to_numeric(df[col_map["gram_weight"]], errors="coerce")

    if col_map["pcr_percent"]:
        out["pcr_percent"] = pd.to_numeric(df[col_map["pcr_percent"]], errors="coerce")
    else:
        out["pcr_percent"] = None

    # Drop rows without a vendor part number
    out = out[out["vendor_part_number"].ne("")].copy()

    return out


def grams_to_lbs(g: float) -> float:
    return g / GRAMS_PER_LB


try:
    df = load_data()
except Exception as e:
    st.error(f"Data load error: {e}")
    st.stop()

with st.expander("✅ Data loaded"):
    st.write(f"Rows: {len(df):,}")
    st.write("Columns used: vendor_part_number, description, gauge, gram_weight_g (and optional pcr_percent)")

st.subheader("Calculator")

vendor_input = st.text_input("Vendor Part Number", placeholder="e.g., 6116").strip()
units_purchased = st.number_input("Units Purchased", min_value=0, value=0, step=1)

# PCR input: if the file includes a PCR% column, we can default to it once part is found.
pcr_input = st.number_input("PCR Content (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)

if vendor_input:
    match = df[df["vendor_part_number"].str.upper() == vendor_input.upper()]

    if match.empty:
        st.warning("No match found for that Vendor Part Number.")
        st.stop()

    # If duplicates exist, take the first one (or you can add a selector)
    row = match.iloc[0]

    desc = row.get("description", "")
    gauge = row.get("gauge", "")
    gram_weight = row.get("gram_weight_g", None)

    if pd.isna(gram_weight):
        st.error("Found the part, but Gram Weight is blank or not numeric in the file.")
        st.stop()

    # If PCR% exists in file, and user hasn't changed from 0, auto-fill once
    if row.get("pcr_percent") is not None and not pd.isna(row.get("pcr_percent")) and pcr_input == 0.0:
        pcr_input = float(row.get("pcr_percent"))
        st.info(f"PCR % pulled from file: {pcr_input:.1f}% (you can override it).")

    st.markdown("### Part Details")
    c1, c2, c3 = st.columns(3)
    c1.metric("Description", str(desc) if str(desc).strip() else "—")
    c2.metric("Gauge", str(gauge) if str(gauge).strip() else "—")
    c3.metric("Gram Weight (g)", f"{float(gram_weight):.2f}")

    total_grams = float(gram_weight) * int(units_purchased)
    total_lbs = grams_to_lbs(total_grams)
    pcr_lbs = total_lbs * (float(pcr_input) / 100.0)

    st.markdown("### Results")
    r1, r2 = st.columns(2)
    r1.metric("Total Plastic Used (lbs)", f"{total_lbs:,.2f}")
    r2.metric("Total PCR Used (lbs)", f"{pcr_lbs:,.2f}")

    st.caption("Formula: plastic_lbs = (gram_weight_g × units) / 453.59237; pcr_lbs = plastic_lbs × (PCR%/100)")
else:
    st.info("Enter a Vendor Part Number to begin.")
