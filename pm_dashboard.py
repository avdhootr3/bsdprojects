import streamlit as st
import pandas as pd
import re
from pathlib import Path
import base64



# --- Page config ---
st.set_page_config(page_title="PM Project Dashboard", layout="wide")


# --- Floating Company Logo (screen + print: page 1 only) ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("logo.png")

st.markdown(f"""
    <style>
    .fixed-logo {{
        position: fixed;
        top: 15px;
        right: 25px;
        z-index: 9999;
    }}
    .print-logo-inline {{ display: none; }}
    @media print {{
        .fixed-logo {{ display: none; }}
        .print-logo-inline {{
            display: block;
            text-align: right;
            margin: 10px 25px 10px 0;
        }}
    }}
    </style>
    <div class="fixed-logo">
        <img src="data:image/png;base64,{logo_base64}" width="100" alt="Company logo">
    </div>
    <div class="print-logo-inline">
        <img src="data:image/png;base64,{logo_base64}" width="100" alt="Company logo">
    </div>
    """, unsafe_allow_html=True)

# --- Load Excel and normalize headers
# --- Load Excel directly from GitHub repo (raw link) ---
url = "https://raw.githubusercontent.com/avdhootr3/bsdprojects/main/data/Dashboard_data.xlsx"
df = pd.read_excel(url, sheet_name=0)
df.columns = df.columns.str.strip()


# --- Simple Project Filter ---
st.sidebar.header("🔍 Select Project")
project_options = sorted(df["Project"].dropna().unique().tolist())
selected_project = st.sidebar.selectbox("Project", project_options)

# Apply filter
filtered_df = df[df["Project"] == selected_project]

if filtered_df.empty:
    st.warning("No projects match your selection.")
    st.stop()

# Pick the first matching row
project = filtered_df.iloc[0]

# --- Helpers ---
def get_field(row, candidates):
    for name in candidates:
        if name in row.index:
            val = row.get(name)
            if pd.notna(val):
                return val
    return None

def format_num(value):
    """Return integer string for numeric values (including 0). Blank for NaN."""
    try:
        num = pd.to_numeric(value, errors='coerce')
        if pd.isna(num):
            return ""
        return str(int(round(num, 0)))
    except Exception:
        s = "" if value is None else str(value).strip()
        return s

def parse_percent(value):
    """
    Parse a value into integer percent (0-100). Accepts:
      - 0.67  -> 67
      - 67    -> 6700
      - "67%" -> 67
      - " 0.67 " -> 67
    Returns None for blank/NaN/unparseable.
    """
    if value is None:
        return None
    if pd.isna(value):
        return None
    s = str(value).strip()
    if s == "":
        return None
    has_pct = "%" in s
    s_clean = s.replace('%', '').replace(',', '').strip()
    try:
        num = float(s_clean)
    except Exception:
        return None
    if has_pct:
        pct = num
    else:
        if abs(num) <= 1:
            pct = num * 100
        else:
            pct = num
    pct = int(round(pct, 0))
    pct = max(-100, min(100, pct))
    return pct

def color_percent_html(pct):
    """Return HTML span with color for pct (green>0, red<0, black==0)."""
    if pct is None:
        return ""
    color = "green" if pct > 0 else ("red" if pct < 0 else "black")
    return f"<span style='color:{color}; font-weight:bold'>{pct}%</span>"

def format_date(value):
    """Format pandas/str/Excel date to DD-MMM-YYYY, safe for serials & text."""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        # handle Excel serial numbers directly
        if isinstance(value, (int, float)):
            parsed = pd.to_datetime(value, unit="d", origin="1899-12-30", errors="coerce")
        else:
            parsed = pd.to_datetime(value, errors="coerce", dayfirst=False)
        if pd.isna(parsed):
            return str(value)  # fallback: show raw value instead of 1970
        return parsed.strftime("%d-%b-%Y")
    except Exception:
        return str(value)


def break_sentences_to_html(text):
    """Insert line breaks (<br>) after '|' for markdown with unsafe_html."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text).strip()
    s = re.sub(r'([|])\s+', r'\1\n', s)
    return s.replace("\n", "<br>")

# --- Select project row ---
if filtered_df.empty:
    st.warning("No projects match your selection.")
    st.stop()

# Pick the first matching row from filtered results
project = filtered_df.iloc[0]


# --- Header ---
proj_name = get_field(project, ['Project1'])
proj_dates = get_field(project, ['Project Dates', 'ProjectDate', 'Project_Date'])
duration = get_field(project, ['Project Duration', 'Duration'])
st.markdown(f"### 📌 Project : **{proj_name or ''}**")
st.markdown(f"**📅 Project Dates**: {proj_dates or ''} &nbsp;&nbsp;&nbsp; **📆 Duration**: {duration or ''}")
st.markdown("---")

# --- First row (metrics) ---
col1, col2, col3, col4 = st.columns(4)
total_po = get_field(project, ['Total PO Amt'])
billed_till = get_field(project, ['Billed Till Date'])
open_billing = get_field(project, ['Open Billing'])
billed_raw = get_field(project, ['Billed', 'Billed %'])

col1.metric("💰 PO Amt (in Lakhs)", f"₹ {format_num(total_po)}")
col2.metric("📤 Billing Done (in Lakhs)", f"₹ {format_num(billed_till)}")
col3.metric("🧾 Open Billing (in Lakhs)", f"₹ {format_num(open_billing)}")

billed_pct = parse_percent(billed_raw)
if billed_pct is not None:
    col4.metric("📊 Billed %", f"{billed_pct}%")
    with col4:
        st.progress(min(1.0, max(0.0, billed_pct/100)))
else:
    col4.metric("📊 Billed %", "N/A")

# --- Second row (NO Profit, only Resources + Milestone) ---
line_items = []

resource_val = get_field(project, ['Resource', 'Resource Deployed', 'Resources'])
if pd.notna(resource_val):
    try:
        resource_val = str(int(float(resource_val)))
    except Exception:
        resource_val = str(resource_val).strip()
else:
    resource_val = ""
line_items.append(("👥 Resources Deployed", resource_val, False))

milestone_amt_str = get_field(project, ['Milestone billing amount', 'MilestoneBillingAmount'])
milestone_amt_str = "" if milestone_amt_str is None else str(milestone_amt_str).strip()
if milestone_amt_str != "":
    line_items.append(("💵 Milestone Billing Amount", f"₹ {milestone_amt_str}", False))

cols = st.columns(len(line_items)) if line_items else st.columns(1)
for i, (label, val, is_html) in enumerate(line_items):
    cols[i].markdown(f"**{label}**: {val}", unsafe_allow_html=True)

# --- Billing Milestone ---
billing_milestone = get_field(project, ['Billing Milestone'])
if billing_milestone:
    st.markdown("###### 📅 Billing Milestone")
    st.markdown(break_sentences_to_html(billing_milestone), unsafe_allow_html=True)

# --- Scope / Overall Progress ---
col1, col2 = st.columns(2)
col1.markdown("### 🔧 Scope")
scope_val = get_field(project, ['Scope', 'ScopeDetails'])
col1.markdown(break_sentences_to_html(scope_val), unsafe_allow_html=True)

col2.markdown("### 📈 Overall Progress")
overall_val = get_field(project, ['Overall Progress'])
col2.markdown(break_sentences_to_html(overall_val), unsafe_allow_html=True)

# --- Tech / Weekly Plan ---
col1, col2 = st.columns(2)
col1.markdown("### 🛠️ Technology / Tools")
tech_val = get_field(project, ['Technology / tools', 'Technology'])
col1.markdown(break_sentences_to_html(tech_val), unsafe_allow_html=True)

col2.markdown("### 📅 Weekly Plan")
weekly_val = get_field(project, ['Weekly Plan'])
col2.markdown(break_sentences_to_html(weekly_val), unsafe_allow_html=True)

# --- Challenges & Risks ---
challenges_val = get_field(project, ['Challenges / Risks'])
if challenges_val:
    st.markdown("### ⚠️ Challenges & Risks")
    st.markdown(break_sentences_to_html(challenges_val), unsafe_allow_html=True)

# --- Footer ---
updated_on = get_field(project, ['Update Date', 'Updated On', 'Update'])
st.markdown("---")
st.caption("Updated on: " + format_date(updated_on))


