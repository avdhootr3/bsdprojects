import streamlit as st
import pandas as pd
import re
from pathlib import Path
import base64



# --- Page config ---
st.set_page_config(page_title="Project Dashboard", layout="wide")


# --- Floating Company Logo (screen + print: page 1 only) ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("logo.png")

st.markdown(f"""
    <style>
    /* Screen: keep floating logo like before */
    .fixed-logo {{
        position: fixed;
        top: 15px;
        right: 25px;
        z-index: 9999;
    }}

    /* Inline logo is hidden on screen */
    .print-logo-inline {{ display: none; }}

    /* Print rules */
    @media print {{
        /* Hide the floating (fixed) one while printing to avoid overlap */
        .fixed-logo {{ display: none; }}

        /* Show a single inline logo at the very top of page 1 only (flows with content) */
        .print-logo-inline {{
            display: block;
            text-align: right;
            margin: 10px 25px 10px 0; /* adjust if needed */


        }}
    }}
    </style>

    <!-- Screen (floating) -->
    <div class="fixed-logo">
        <img src="data:image/png;base64,{logo_base64}" width="100" alt="Company logo">
    </div>

    <!-- Print-only (appears once at start of document, i.e., on page 1) -->
    <div class="print-logo-inline">
        <img src="data:image/png;base64,{logo_base64}" width="100" alt="Company logo">
    </div>
    """, unsafe_allow_html=True)


st.markdown("""
    <style>
    /* Use theme variables so it works in light & dark mode */
    div[data-testid="stMetric"] {
        border: 1px solid var(--secondary-background-color);
        border-radius: 8px;
        padding: 8px;
        background-color: var(--background-color);
        color: var(--text-color);
    }

    div[data-testid="column"] > div > div {
        border: 1px solid var(--secondary-background-color);
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 8px;
        background-color: var(--background-color);
        color: var(--text-color);
    }

    div[data-testid="stMetric"], 
    div[data-testid="column"] > div > div {
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    

    @media print {
    /* Force clean black & white for everything */
    body, [class^="st-"], [data-testid] {
        background: #ffffff !important;
        color: #000000 !important;
    }

    /* Metrics (top row) */
    div[data-testid="stMetric"] {
        border: 1px solid #000000 !important;
        border-radius: 4px;
        padding: 6px;
        background: #ffffff !important;
        color: #000000 !important;
    }

    /* All content boxes inside columns */
    div[data-testid="column"] > div > div {
        border: 1px solid #000000 !important;
        border-radius: 4px;
        padding: 6px;
        margin-bottom: 6px;
        background: #ffffff !important;
        color: #000000 !important;
    }

    /* Headings bold + clear */
    h1, h2, h3, h4, h5, h6, strong {
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* Remove shadows in print */
    * {
        box-shadow: none !important;
    }

    /* --- Logo print fix (always full on page 1) --- */
    .print-logo-inline {
        display: block !important;
        text-align: right;
        margin: 40px 25px 20px 0;  /* keep away from page edge */
        page-break-after: avoid;   /* don’t push content to new page */
    }
    .print-logo-inline img {
        width: 120px !important;   /* fixed safe width */
        height: auto !important;   /* keep proportions */
        max-width: none !important;
        max-height: none !important;
        object-fit: contain !important;
    }


}
    


    </style>
""", unsafe_allow_html=True)



# --- Load Excel and normalize headers
df = pd.read_excel("Dashboard_data.xlsx", sheet_name=0)
df.columns = df.columns.str.strip()


# --- Filters & Search  ---
# --- Dynamic Filters & Search ---
st.sidebar.header("🔍 Filter Projects")

# --- Session state defaults ---
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "All"
if "selected_project" not in st.session_state:
    st.session_state.selected_project = "All"
if "selected_type" not in st.session_state:
    st.session_state.selected_type = "All"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""


# --- Clear Filters Button  ---
if st.sidebar.button("🧹 Clear Filters"):
    # wipe widget state so it behaves like a hard reload
    for k in ("selected_region", "selected_project", "selected_type", "search_query"):
        st.session_state.pop(k, None)
    st.rerun()  # re-run after state is wiped -> search box empties




# --- Search Box ---
st.session_state.search_query = st.sidebar.text_input(
    "Search by keyword:",
    value=st.session_state.search_query
)

# --- Step 1: Calculate available filter options based on current selections ---
temp_df = df.copy()

# Apply all filters progressively for dynamic option calculation
if st.session_state.selected_region != "All":
    temp_df = temp_df[temp_df["Region"] == st.session_state.selected_region]
if st.session_state.selected_project != "All":
    temp_df = temp_df[temp_df["Project"] == st.session_state.selected_project]
if st.session_state.selected_type != "All":
    temp_df = temp_df[temp_df["Type"] == st.session_state.selected_type]

# Available options based on filtered temp_df
region_options = ["All"] + sorted(df["Region"].dropna().unique().tolist())
project_options = ["All"] + sorted(temp_df["Project"].dropna().unique().tolist())
type_options = ["All"] + sorted(temp_df["Type"].dropna().unique().tolist())

# --- Step 2: Render dropdowns ---
st.session_state.selected_region = st.sidebar.selectbox(
    "Select Region",
    region_options,
    index=region_options.index(st.session_state.selected_region) if st.session_state.selected_region in region_options else 0
)
# Update project list based on region selection
temp_df = df.copy()
if st.session_state.selected_region != "All":
    temp_df = temp_df[temp_df["Region"] == st.session_state.selected_region]
project_options = ["All"] + sorted(temp_df["Project"].dropna().unique().tolist())

st.session_state.selected_project = st.sidebar.selectbox(
    "Select Project",
    project_options,
    index=project_options.index(st.session_state.selected_project) if st.session_state.selected_project in project_options else 0
)
# Update type list based on region + project
if st.session_state.selected_project != "All":
    temp_df = temp_df[temp_df["Project"] == st.session_state.selected_project]
type_options = ["All"] + sorted(temp_df["Type"].dropna().unique().tolist())

st.session_state.selected_type = st.sidebar.selectbox(
    "Select Type",
    type_options,
    index=type_options.index(st.session_state.selected_type) if st.session_state.selected_type in type_options else 0
)

# --- Step 3: Apply final filters ---
filtered_df = df.copy()
if st.session_state.selected_region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == st.session_state.selected_region]
if st.session_state.selected_project != "All":
    filtered_df = filtered_df[filtered_df["Project"] == st.session_state.selected_project]
if st.session_state.selected_type != "All":
    filtered_df = filtered_df[filtered_df["Type"] == st.session_state.selected_type]

if st.session_state.search_query:
    search_lower = st.session_state.search_query.lower()
    filtered_df = filtered_df[
        filtered_df.apply(lambda row: search_lower in row.to_string().lower(), axis=1)
    ]

# --- Step 4: Current Filters Summary ---
st.sidebar.markdown("**Current Filters:**")
st.sidebar.write(f"Region: {st.session_state.selected_region}")
st.sidebar.write(f"Project: {st.session_state.selected_project}")
st.sidebar.write(f"Type: {st.session_state.selected_type}")
if st.session_state.search_query:
    st.sidebar.write(f"Search: {st.session_state.search_query}")


# --- END Filters & Search replacement ---



# Pick first project in filtered list
if not filtered_df.empty:
    project = filtered_df.iloc[0]
else:
    st.warning("No projects match your selection.")
    st.stop()

# From here down, keep your *existing* rendering logic using 'project'



# --- Helpers ---
def get_field(row, candidates):
    """Return first non-null value for any name in candidates list (handles header variants)."""
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
      - 67    -> 67
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
    """Format pandas/str date to DD-MMM-YYYY, or return blank if none."""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        parsed = pd.to_datetime(value)
        return parsed.strftime("%d-%b-%Y")
    except Exception:
        return "" if value is None else str(value)

def break_sentences_to_html(text):
    """Insert line breaks (<br>) after '.', '/', '!' or '?' for markdown with unsafe_html."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text).strip()
    s = re.sub(r'([.!?/])\s+', r'\1\n', s)
    return s.replace("\n", "<br>")

# --- Select project row ---
if filtered_df.empty:
    st.warning("No projects match your selection.")
    st.stop()

# Pick the first matching row from filtered results
project = filtered_df.iloc[0]


# --- Header
# --- Ensure we have the Project column name (proj_name_field) ---
proj_name_field = next((c for c in df.columns if c.lower().strip() == 'project'), None)
if proj_name_field is None:
    proj_name_field = next((c for c in df.columns if 'project' in c.lower()), None)

if proj_name_field is None:
    st.error("Could not find a 'Project' column in the Excel. Please check headers.")
    st.stop()

# --- Select first matching project from filtered_df (filters must be applied earlier) ---
if 'filtered_df' not in globals():
    # fallback: if you accidentally removed the filter block, use full df
    filtered_df = df.copy()

if filtered_df.empty:
    st.warning("No projects match your selection.")
    st.stop()

project = filtered_df.iloc[0]

proj_name = get_field(project, [proj_name_field, 'Project'])
proj_dates = get_field(project, ['Project Dates', 'Project Dates ', 'ProjectDate', 'Project_Date'])
duration = get_field(project, ['Project Duration', 'ProjectDuration', 'Duration', 'Project Duration '])
st.markdown(f"### 📌 Project : **{proj_name or ''}**")
st.markdown(f"**📅 Project Dates**: {proj_dates or ''} &nbsp;&nbsp;&nbsp; **📆 Duration**: {duration or ''}")
st.markdown("---")

# --- First row
col1, col2, col3, col4 = st.columns(4)

total_po = get_field(project, ['Total PO Amt', 'Total PO Amt ', 'Total_PO_Amt', ' Total PO Amt '])
billed_till = get_field(project, ['Billed Till Date', 'Billed Till Date '])
open_billing = get_field(project, ['Open Billing', 'Open Billing '])
billed_raw = get_field(project, ['Billed', 'Billed ', 'Billed %', 'Billed%'])
billing_milestone = get_field(project, ['Billing Milestone', 'Billing Milestone '])

col1.metric("💰 PO Amt (in Lakhs)", f"₹ {format_num(total_po)}")
col2.metric("📤 Billing Done (in Lakhs)", f"₹ {format_num(billed_till)}")
col3.metric("🧾 Open Billing (in Lakhs)", f"₹ {format_num(open_billing)}")

billed_pct = parse_percent(billed_raw)
if billed_pct is not None:
    col4.metric("📊 Billed %", f"{billed_pct}%")
    with col4:
        prog = max(0, min(100, billed_pct)) / 100.0
        st.progress(prog)
else:
    col4.metric("📊 Billed %", "N/A")


# --- Second row
profit_ytd_raw = get_field(project, ['Profit_YTD MIS', 'Profit_YTD_MIS', 'Profit_YTD MIS'])
profit_fy_raw  = get_field(project, ['Profit_FY24-25_MIS', 'Profit_FY24-25 MIS', 'Profit_FY24-25_MIS'])
profit_ytd = parse_percent(profit_ytd_raw)
profit_fy  = parse_percent(profit_fy_raw)

# ✅ Modified: handle text or numeric for Resources Deployed
resource_val = get_field(project, ['Resource', 'Resource Deployed', 'Resources', 'Resource '])
if pd.notna(resource_val):
    try:
        # try numeric formatting
        resource_val = str(int(float(resource_val)))
    except Exception:
        # keep as string if not numeric
        resource_val = str(resource_val).strip()
else:
    resource_val = ""

# ⬇ Milestone amount as TEXT (no numeric formatting)
milestone_amt_str = get_field(project, ['Milestone billing amount', 'Milestone billing amount ', 'MilestoneBillingAmount'])
milestone_amt_str = "" if milestone_amt_str is None else str(milestone_amt_str).strip()

line_items = []
if profit_ytd is not None and profit_ytd != 0:
    line_items.append(("💹 Profit YTD MIS (%)", color_percent_html(profit_ytd), True))
if profit_fy is not None and profit_fy != 0:
    line_items.append(("📈 Profit FY24-25 MIS (%)", color_percent_html(profit_fy), True))

line_items.append(("👥 Resources Deployed", resource_val, False))
if milestone_amt_str != "":
    line_items.append(("💵 Milestone Billing Amount", f"₹ {milestone_amt_str}", False))

if len(line_items) == 0:
    cols = st.columns(1)
else:
    cols = st.columns(len(line_items))

for i, (label, val, is_html) in enumerate(line_items):
    target_col = cols[i]
    if is_html:
        target_col.markdown(f"**{label}**: {val}", unsafe_allow_html=True)
    else:
        target_col.markdown(f"**{label}**: {val}")

# --- Billing Milestone (Full width for multi-line text) ---
if billing_milestone:
    st.markdown("###### 📅 Billing Milestone")
    st.markdown(break_sentences_to_html(billing_milestone), unsafe_allow_html=True)



# --- Scope / Overall Progress
col1, col2 = st.columns(2)
col1.markdown("### 🔧 Scope")
scope_val = get_field(project, ['Scope', 'Scope ', 'ScopeDetails'])
col1.markdown(break_sentences_to_html(scope_val), unsafe_allow_html=True)

col2.markdown("### 📈 Overall Progress")
overall_val = get_field(project, ['Overall Progress', 'OverallProgress', 'Overall Progress '])
col2.markdown(break_sentences_to_html(overall_val), unsafe_allow_html=True)

# --- Tech / Weekly Plan
col1, col2 = st.columns(2)
col1.markdown("### 🛠️ Technology / Tools")
tech_val = get_field(project, ['Technology / tools', 'Technology / tools ', 'Technology', 'Technology / Tools'])
col1.markdown(break_sentences_to_html(tech_val), unsafe_allow_html=True)

col2.markdown("### 📅 Weekly Plan")
weekly_val = get_field(project, ['Weekly Plan', 'WeeklyPlan', 'Weekly Plan '])
col2.markdown(break_sentences_to_html(weekly_val), unsafe_allow_html=True)

# --- Footer
updated_on = get_field(project, ['Update Date', 'Updated On', 'Update', 'UpdateDate'])
st.markdown("---")
st.caption("Updated on: " + format_date(updated_on))
