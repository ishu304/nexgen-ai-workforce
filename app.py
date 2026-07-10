"""
main.py
--------
Personal Data Analyst Toolkit (Streamlit)

This is a single-user, local, sellable tool — NOT a multi-tenant SaaS.
There is no admin panel, no roles, no credits/plan system, because this
app and its data live entirely on the buyer's own machine: anyone with
the files has full control of them anyway, so building "access control"
into a locally-run app can't actually be enforced. See README.md for the
full explanation and monetization notes.

Run with:
    streamlit run main.py
"""

import io
import json
import platform
import traceback
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from datetime import datetime

import data_handler as dh
import security as sec

# ----------------------------------------------------------------------
# App / support config
# ----------------------------------------------------------------------
APP_VERSION = "1.0.0"
SUPPORT_EMAIL = "feedback.ishupal@gmail.com"


def _diagnostic_lines() -> list:
    """Basic, non-personal diagnostic info — no dataset or file content."""
    return [
        f"App Version: {APP_VERSION}",
        f"Operating System: {platform.system()} {platform.release()}",
        f"Python Version: {platform.python_version()}",
    ]


def build_feedback_mailto() -> str:
    """
    Build a mailto: link that opens the user's default email app with the
    support address, subject, and a pre-filled body template. Nothing here
    is sent automatically — the user reviews and sends it themselves.
    """
    subject = f"ISHUPAL Feedback - {APP_VERSION}"
    body_lines = _diagnostic_lines() + [
        "",
        "Feedback Type (Bug Report / Feature Request / General Feedback): ",
        "Description: ",
        "Steps to Reproduce (if applicable): ",
    ]
    body = "\n".join(body_lines)
    query = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    return f"mailto:{SUPPORT_EMAIL}?{query}"


def build_copy_text() -> str:
    """
    Text for the 'Copy Error Details' button: the latest captured app
    error if one exists, otherwise just basic diagnostics. Never includes
    dataset contents or other personal files.
    """
    lines = _diagnostic_lines()
    last_error = st.session_state.get("last_error")
    if last_error:
        lines += ["", "Last Error:", last_error]
    return "\n".join(lines)


def render_copy_error_button(label: str, text_to_copy: str, key: str, height: int = 46) -> None:
    """
    Renders a button that copies `text_to_copy` to the clipboard via the
    browser Clipboard API. Implemented as a small embedded HTML/JS
    component since Streamlit has no native clipboard-copy widget.
    """
    safe_text = json.dumps(text_to_copy)
    safe_label = json.dumps(label)
    html_code = f"""
    <button id="{key}" style="
        width:100%; padding:0.5rem 1.1rem; border:none; border-radius:8px;
        font-weight:600; cursor:pointer; font-size:0.95rem;
        background:linear-gradient(90deg, #16c98d, #00b4d8); color:white;">
      {label}
    </button>
    <script>
      const btn_{key} = document.getElementById("{key}");
      btn_{key}.addEventListener("click", function() {{
        navigator.clipboard.writeText({safe_text}).then(function() {{
          btn_{key}.innerText = "✅ Copied!";
          setTimeout(function() {{ btn_{key}.innerText = {safe_label}; }}, 1500);
        }}).catch(function() {{
          btn_{key}.innerText = "⚠️ Copy failed";
          setTimeout(function() {{ btn_{key}.innerText = {safe_label}; }}, 1500);
        }});
      }});
    </script>
    """
    components.html(html_code, height=height)

# ----------------------------------------------------------------------
# Page config + global style (dark neon theme, fixed text-contrast bug)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Data Analyst Toolkit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    :root {
        --bg-deep: #0a0c14;
        --bg-panel: #12162a;
        --border-soft: #262b45;
        --text-main: #e6e8f0;
        --text-dim: #9aa0c0;
        --accent-cyan: #00e0ff;
        --accent-violet: #6a5cff;
    }

    .stApp {
        background: radial-gradient(circle at top left, #101425 0%, #0a0c14 60%);
        color: var(--text-main);
    }

    /* Force readable text color on every native Streamlit text element,
       regardless of the browser/OS light-vs-dark override. This fixes
       the "black text on black background" visibility bug. */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div,
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    .stText, .stCaption, .stAlert, .stMetric,
    section[data-testid="stSidebar"] * ,
    div[data-testid="stForm"] * ,
    div[data-testid="stExpander"] * {
        color: var(--text-main) !important;
    }

    /* Inputs: keep a light field background with dark, clearly visible text */
    input, textarea,
    div[data-baseweb="select"] * ,
    div[data-baseweb="input"] * {
        color: #0a0c14 !important;
    }
    div[data-baseweb="select"] > div,
    input, textarea {
        background-color: #eef0fb !important;
        border-radius: 8px !important;
    }

    /* Dataframe / table text */
    div[data-testid="stDataFrame"] * {
        color: #0a0c14 !important;
    }

    section[data-testid="stSidebar"] {
        background: #0d0f1a;
        border-right: 1px solid var(--border-soft);
    }

    .app-title {
        font-size: 1.6rem;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-violet));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }

    .app-subtitle {
        color: var(--text-dim) !important;
        font-size: 0.9rem;
        margin-top: 0;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, var(--bg-panel), var(--bg-deep));
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div {
        color: var(--text-main) !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #00b4d8, var(--accent-violet));
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
    }
    .stButton > button:hover {
        opacity: 0.9;
        color: white !important;
    }
    .stDownloadButton > button {
        background: linear-gradient(90deg, #16c98d, #00b4d8);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    div[data-testid="stExpander"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
    }

    div[data-testid="stForm"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
        padding: 12px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Session state init
# ----------------------------------------------------------------------
for key, default in [
    ("logged_in", False),
    ("username", None),
    ("page", "Dashboard"),
    ("last_error", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.page = "Dashboard"


# ----------------------------------------------------------------------
# LOGIN / SETUP PAGE
# ----------------------------------------------------------------------
def render_login():
    users = dh.load_users()
    left, mid, right = st.columns([1, 1.1, 1])

    with mid:
        st.markdown(
            "<div style='text-align:center; margin-top:60px;'>"
            "<div class='app-title'>📊 Data Analyst Toolkit</div>"
            "<p class='app-subtitle'>Your personal, local, offline data workspace</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.write("")

        if not users:
            # First-run setup — create the one local profile
            with st.container(border=True):
                st.subheader("Set up your local profile")
                st.caption("This runs once. Your password is hashed and stored only on this machine.")
                new_username = st.text_input("Choose a username")
                new_name = st.text_input("Your name")
                new_password = st.text_input("Choose a password", type="password")
                if st.button("Create profile", use_container_width=True):
                    if not new_username or not new_password:
                        st.error("Username and password are required.")
                    else:
                        creds = sec.create_credentials(new_password)
                        dh.create_local_profile(new_username, new_name or new_username, creds["password_hash"], creds["salt"])
                        st.success("Profile created. Please log in below.")
                        st.rerun()
            return

        with st.container(border=True):
            st.subheader("Sign in")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                user = dh.get_user(username)
                if user is None:
                    st.error("User not found.")
                elif not sec.verify_password(password, user.get("salt", ""), user.get("password_hash", "")):
                    st.error("Incorrect password.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.page = "Dashboard"
                    st.rerun()


# ----------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------------------------
def render_sidebar(user: dict):
    st.sidebar.markdown(
        "<div class='app-title' style='font-size:1.2rem;'>📊 Data Toolkit</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(f"**{user.get('name', st.session_state.username)}**")
    st.sidebar.divider()

    pages = ["Dashboard", "Analytics", "Data Entry", "Settings"]
    for p in pages:
        if st.sidebar.button(p, use_container_width=True, type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()

    st.sidebar.divider()

    # --- Freemium placeholders (inactive for now) ---
    st.sidebar.button(
        "⭐ Upgrade to Pro",
        use_container_width=True,
        disabled=True,
        help="Pro features (Advanced Analytics, Cloud Auto-Backup, Team Features) are coming soon.",
    )
    st.sidebar.link_button(
        "💬 Feedback / Support",
        build_feedback_mailto(),
        use_container_width=True,
        help=f"Opens your email app, pre-addressed to {SUPPORT_EMAIL}",
    )
    with st.sidebar:
        render_copy_error_button(
            "📋 Copy Error Details",
            build_copy_text(),
            key="copy_error_btn",
        )
    st.sidebar.caption(f"v{APP_VERSION} · Free local edition")
    with st.sidebar.expander("ℹ️ About"):
        st.caption(
            "Data Analyst Toolkit is a free, local-first data cleaning and "
            "charting tool. Your data never leaves this machine — everything "
            "is stored in local JSON files. No account, no cloud, no tracking."
        )
        st.caption(f"Support: {SUPPORT_EMAIL}")

    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        logout()
        st.rerun()


# ----------------------------------------------------------------------
# DASHBOARD PAGE
# ----------------------------------------------------------------------
def render_dashboard(user: dict):
    st.markdown("<div class='app-title'>Dashboard Overview</div>", unsafe_allow_html=True)
    st.markdown(f"<p class='app-subtitle'>Welcome back, {user.get('name')}</p>", unsafe_allow_html=True)
    st.write("")

    datasets = dh.get_user_datasets(st.session_state.username)
    total_rows = sum(d.get("rows", 0) for d in datasets)
    last_upload = datasets[-1]["uploaded_at"] if datasets else "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("Datasets Saved", len(datasets))
    c2.metric("Total Rows Processed", f"{total_rows:,}")
    c3.metric("Last Activity", last_upload)

    st.write("")
    st.subheader("Your Datasets")
    if not datasets:
        st.info("No datasets yet. Go to **Analytics** to upload a file, or **Data Entry** to start typing data manually.")
    else:
        summary_rows = [
            {
                "File / Name": d["source_filename"],
                "Uploaded": d["uploaded_at"],
                "Rows": d["rows"],
                "Columns": len(d["columns"]),
            }
            for d in datasets
        ]
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------
# ANALYTICS PAGE
# ----------------------------------------------------------------------
def render_analytics(user: dict):
    st.markdown("<div class='app-title'>Analytics Engine</div>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Upload, clean, merge, chart, and export your data</p>", unsafe_allow_html=True)
    st.write("")

    tab_upload, tab_merge = st.tabs(["📤 Upload & Clean", "🔗 Merge Multiple Files"])

    with tab_upload:
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"], key="single_upload")
        if uploaded_file is not None:
            try:
                raw_df = dh.read_uploaded_file(uploaded_file)
                st.write(f"Raw data: **{raw_df.shape[0]} rows × {raw_df.shape[1]} columns**")

                cleaned_df = dh.clean_dataframe(raw_df)
                st.success(
                    f"Cleaning complete → {cleaned_df.shape[0]} rows remaining "
                    f"({raw_df.shape[0] - cleaned_df.shape[0]} removed as null/duplicate rows)"
                )

                with st.expander("Preview cleaned data", expanded=True):
                    st.dataframe(cleaned_df.head(50), use_container_width=True)

                st.markdown("#### 🤖 Auto Insights")
                with st.container(border=True):
                    for point in dh.generate_insights(cleaned_df):
                        st.markdown(f"- {point}")

                col_a, col_b, col_c = st.columns(3)
                if col_a.button("💾 Save cleaned dataset"):
                    dh.save_processed_data(st.session_state.username, cleaned_df, uploaded_file.name)
                    st.success("Dataset saved.")
                    st.rerun()
                col_b.download_button(
                    "⬇️ Download as CSV",
                    data=dh.df_to_csv_bytes(cleaned_df),
                    file_name=f"cleaned_{uploaded_file.name.rsplit('.',1)[0]}.csv",
                    mime="text/csv",
                )
                col_c.download_button(
                    "⬇️ Download as Excel",
                    data=dh.df_to_excel_bytes(cleaned_df),
                    file_name=f"cleaned_{uploaded_file.name.rsplit('.',1)[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            except Exception as e:
                st.error(f"Could not process file: {e}")

    with tab_merge:
        st.caption("Upload 2 or more files with similar columns to combine them into one dataset.")
        merge_files = st.file_uploader(
            "Upload multiple CSV/Excel files", type=["csv", "xlsx", "xls"],
            accept_multiple_files=True, key="merge_upload"
        )
        merge_mode = st.radio(
            "Merge mode", ["Stack rows (append)", "Side-by-side (join columns)"], horizontal=True
        )
        if merge_files and len(merge_files) >= 2:
            try:
                dfs = [dh.read_uploaded_file(f) for f in merge_files]
                mode = "stack" if merge_mode.startswith("Stack") else "side_by_side"
                merged = dh.merge_datasets(dfs, mode=mode)
                cleaned_merged = dh.clean_dataframe(merged)
                st.success(f"Merged {len(merge_files)} files → {cleaned_merged.shape[0]} rows, {cleaned_merged.shape[1]} columns")
                st.dataframe(cleaned_merged.head(50), use_container_width=True)

                merge_name = st.text_input("Name this merged dataset", value="merged_dataset")
                if st.button("💾 Save merged dataset"):
                    dh.save_processed_data(st.session_state.username, cleaned_merged, f"{merge_name}.csv")
                    st.success("Merged dataset saved.")
                    st.rerun()
            except Exception as e:
                st.error(f"Could not merge files: {e}")
        elif merge_files:
            st.info("Upload at least 2 files to merge.")

    st.divider()
    st.subheader("Build a Chart")

    datasets = dh.get_user_datasets(st.session_state.username)
    if not datasets:
        st.info("Upload and save a dataset above to start charting.")
        return

    options = [f"{i+1}. {d['source_filename']} ({d['uploaded_at']})" for i, d in enumerate(datasets)]
    choice = st.selectbox("Select a saved dataset", options)
    idx = options.index(choice)
    df = dh.dataset_to_dataframe(datasets[idx])

    if df.empty:
        st.warning("This dataset has no rows to chart.")
        return

    with st.expander("🤖 Auto Insights for this dataset"):
        for point in dh.generate_insights(df):
            st.markdown(f"- {point}")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols = df.columns.tolist()

    col1, col2, col3 = st.columns(3)
    chart_type = col1.selectbox("Chart Type", ["Bar", "Pie", "Line", "Area"])
    x_axis = col2.selectbox("X-axis / Category", all_cols)
    y_axis = col3.selectbox("Y-axis / Value", numeric_cols if numeric_cols else all_cols)

    dark_template = "plotly_dark"

    # Aggregate by category so repeated labels sum/count instead of duplicating
    chart_df = df.copy()
    if y_axis in numeric_cols:
        chart_df = chart_df.groupby(x_axis, as_index=False)[y_axis].sum()
    else:
        chart_df = chart_df.groupby(x_axis, as_index=False).size().rename(columns={"size": y_axis})
    chart_df = chart_df.sort_values(y_axis, ascending=False)

    unique_categories = chart_df[x_axis].nunique()

    if chart_type in ("Bar", "Pie") and unique_categories > 12:
        st.info(
            f"'{x_axis}' has {unique_categories} unique values — showing only the top ones "
            f"keeps the chart readable. Adjust below if needed."
        )
        top_n = st.slider("Show top N categories (rest grouped as 'Others')", 3, min(30, unique_categories), 10)
        top_rows = chart_df.head(top_n)
        rest_sum = chart_df.iloc[top_n:][y_axis].sum()
        if rest_sum > 0:
            others_row = pd.DataFrame({x_axis: ["Others"], y_axis: [rest_sum]})
            chart_df = pd.concat([top_rows, others_row], ignore_index=True)
        else:
            chart_df = top_rows

    try:
        if chart_type == "Bar":
            fig = px.bar(chart_df, x=x_axis, y=y_axis, template=dark_template, color=x_axis)
        elif chart_type == "Pie":
            fig = px.pie(chart_df, names=x_axis, values=y_axis, template=dark_template)
        elif chart_type == "Line":
            fig = px.line(chart_df, x=x_axis, y=y_axis, template=dark_template)
        else:  # Area
            fig = px.area(chart_df, x=x_axis, y=y_axis, template=dark_template)

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e6e8f0",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render chart: {e}")


# ----------------------------------------------------------------------
# DATA ENTRY PAGE — manual typing, no file needed
# ----------------------------------------------------------------------
def render_data_entry(user: dict):
    st.markdown("<div class='app-title'>Data Entry</div>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Type data in directly — add, edit, or delete rows by hand</p>", unsafe_allow_html=True)
    st.write("")

    datasets = dh.get_user_datasets(st.session_state.username)

    with st.expander("➕ Start a brand-new dataset"):
        new_name = st.text_input("Dataset name", value="my_data_entry")
        cols_text = st.text_input("Column names (comma-separated)", value="Name, Value, Date")
        if st.button("Create dataset"):
            columns = [c.strip() for c in cols_text.split(",") if c.strip()]
            if not columns:
                st.error("Please provide at least one column name.")
            else:
                dh.create_blank_dataset(st.session_state.username, f"{new_name}.csv", columns)
                st.success("Dataset created — select it below to start typing rows.")
                st.rerun()

    if not datasets:
        st.info("No datasets yet — create one above.")
        return

    options = [f"{i+1}. {d['source_filename']}" for i, d in enumerate(datasets)]
    choice = st.selectbox("Select a dataset to edit", options)
    idx = options.index(choice)
    record = datasets[idx]
    df = dh.dataset_to_dataframe(record)
    columns = record.get("columns", list(df.columns))

    st.markdown("#### Add a new row")
    with st.form("add_row_form", clear_on_submit=True):
        new_row = {}
        cols_ui = st.columns(min(len(columns), 4)) if columns else [st]
        for i, col_name in enumerate(columns):
            new_row[col_name] = cols_ui[i % len(cols_ui)].text_input(col_name, key=f"entry_{col_name}")
        submitted = st.form_submit_button("Add row")
        if submitted:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            dh.overwrite_dataset(st.session_state.username, idx, df)
            st.success("Row added.")
            st.rerun()

    st.markdown("#### Existing rows")
    if df.empty:
        st.info("No rows yet — add one above.")
    else:
        edited_df = st.data_editor(
            df, use_container_width=True, num_rows="dynamic", key=f"editor_{idx}"
        )
        col_save, col_export = st.columns(2)
        if col_save.button("💾 Save changes"):
            dh.overwrite_dataset(st.session_state.username, idx, edited_df)
            st.success("Changes saved.")
            st.rerun()
        col_export.download_button(
            "⬇️ Export this dataset (CSV)",
            data=dh.df_to_csv_bytes(edited_df),
            file_name=f"{record['source_filename'].rsplit('.',1)[0]}.csv",
            mime="text/csv",
        )


# ----------------------------------------------------------------------
# SETTINGS PAGE
# ----------------------------------------------------------------------
def render_settings(user: dict):
    st.markdown("<div class='app-title'>Settings</div>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Manage your local profile</p>", unsafe_allow_html=True)
    st.write("")

    with st.container(border=True):
        st.subheader("Change password")
        current_pw = st.text_input("Current password", type="password")
        new_pw = st.text_input("New password", type="password")
        confirm_pw = st.text_input("Confirm new password", type="password")
        if st.button("Update password"):
            if not sec.verify_password(current_pw, user.get("salt", ""), user.get("password_hash", "")):
                st.error("Current password is incorrect.")
            elif not new_pw or new_pw != confirm_pw:
                st.error("New passwords don't match (or are empty).")
            else:
                creds = sec.create_credentials(new_pw)
                dh.update_password(st.session_state.username, creds["salt"], creds["password_hash"])
                st.success("Password updated.")

    st.write("")
    st.caption(
        "All your data lives locally in the `data/` folder next to this app "
        "(users.json, processed_data.json). Back it up by copying that folder."
    )


# ----------------------------------------------------------------------
# APP ROUTER
# ----------------------------------------------------------------------
def main():
    if not st.session_state.logged_in:
        render_login()
        return

    user = dh.get_user(st.session_state.username)
    if user is None:
        logout()
        st.rerun()
        return

    render_sidebar(user)

    try:
        if st.session_state.page == "Dashboard":
            render_dashboard(user)
        elif st.session_state.page == "Analytics":
            render_analytics(user)
        elif st.session_state.page == "Data Entry":
            render_data_entry(user)
        elif st.session_state.page == "Settings":
            render_settings(user)
        else:
            render_dashboard(user)
    except Exception:
        tb = traceback.format_exc()
        if st.session_state.get("last_error") != tb:
            # First time we've seen this error: store it, then rerun once
            # so the sidebar's "Copy Error Details" button picks it up.
            st.session_state["last_error"] = tb
            st.rerun()
        st.error(
            "⚠️ Something went wrong loading this page. Click "
            "**📋 Copy Error Details** in the sidebar, then use "
            "**💬 Feedback / Support** to send it to us."
        )


if __name__ == "__main__":
    main()
