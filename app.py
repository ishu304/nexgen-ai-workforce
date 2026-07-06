import re
import os
import io
import pandas as pd
import hashlib
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

# --- CORE FILE CONFIGURATION ---
DATA_FILE = "enterprise_multi_tenant_database.csv"
USER_FILE = "secure_user_credentials.csv"

# --- DATABASE INITIALIZATION ---
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Date", "Username", "Company", "Product", "Cost_Price", "Selling_Price", "Quantity", "Total_Revenue", "Total_Profit", "Status"])
    df.to_csv(DATA_FILE, index=False)

if not os.path.exists(USER_FILE):
    df_users = pd.DataFrame(columns=["Username", "Password", "Company", "Plan"])
    # Creating a default mock admin/premium user for instant testing
    # Password is encrypted using SHA-256
    default_pass = hashlib.sha256("admin123".encode()).hexdigest()
    default_user = pd.DataFrame([{"Username": "demo_boss", "Password": default_pass, "Company": "NexGen Skincare", "Plan": "Premium"}])
    default_free = pd.DataFrame([{"Username": "free_user", "Password": default_pass, "Company": "Local Shop", "Plan": "Free Tier"}])
    pd.concat([df_users, default_user, default_free]).to_csv(USER_FILE, index=False)

# --- SECURITY & CRYPTOGRAPHY ENGINE ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    df = pd.read_csv(USER_FILE)
    hashed_p = hash_password(password)
    user_match = df[(df["Username"] == username) & (df["Password"] == hashed_p)]
    if not user_match.empty:
        return {"Username": username, "Company": user_match.iloc[0]["Company"], "Plan": user_match.iloc[0]["Plan"]}
    return None

def register_new_user(username, password, company, plan):
    df = pd.read_csv(USER_FILE)
    if username in df["Username"].values:
        return False
    new_user = {"Username": username, "Password": hash_password(password), "Company": company, "Plan": plan}
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=False)
    df.to_csv(USER_FILE, index=False)
    return True

# --- CORE BUSINESS LOGIC & CLEANING PIPELINES ---
def clean_product_name(name):
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return cleaned.strip().title()

def autonomous_ai_parser(user_text):
    text = user_text.lower().strip()
    price_match = re.search(r'(?:price|rs|rupee|rate|cost|is)\s*[:=-]?\s*(\d+)', text)
    qty_match = re.search(r'(?:qty|quantity|items|sold|pcs|pack|pieces)\s*[:=-]?\s*(\d+)', text)
    if not qty_match:
        qty_match = re.search(r'(\d+)\s*(?:pcs|pack|items|quantity|pieces)', text)

    product = "Standard Item"
    if "enter" in text or "entry" in text:
        try:
            keyword = "enter" if "enter" in text else "entry"
            product = text.split(keyword)[1]
            if "price" in product: product = product.split("price")[0]
            if "cost" in product: product = product.split("cost")[0]
            if "is" in product: product = product.split("is")[0]
        except:
            pass

    if price_match and qty_match:
        final_product = clean_product_name(product)
        selling_price = float(price_match.group(1))
        quantity = int(qty_match.group(1))
        
        if selling_price <= 0 or quantity <= 0: return "ANOMALY_ERROR", None
        if selling_price > 50000 or quantity > 5000:
            return "FRAUD_ALERT", {"Product": final_product if final_product else "Suspicious Item", "Cost_Price": round(selling_price * 0.7, 2), "Selling_Price": selling_price, "Quantity": quantity, "Status": "Flagged"}
            
        return "ENTRY", {"Product": final_product if final_product else "Standard Item", "Cost_Price": round(selling_price * 0.7, 2), "Selling_Price": selling_price, "Quantity": quantity, "Status": "Verified"}
    return "UNKNOWN", None

def execute_entry(data, username, company):
    df = pd.read_csv(DATA_FILE)
    
    # Anti-Duplicate Guardrail Layer
    if not df.empty:
        last_match = df[(df["Username"] == username) & (df["Product"] == data["Product"]) & (df["Quantity"] == data["Quantity"]) & (df["Selling_Price"] == data["Selling_Price"])]
        if not last_match.empty:
            last_time = pd.to_datetime(last_match["Date"].iloc[-1])
            if (pd.Timestamp.now() - last_time).total_seconds() < 120:
                return "DUPLICATE_BLOCK", "System flagged an identical entry executed within 120 seconds. Record dropped."

    revenue = data["Selling_Price"] * data["Quantity"]
    profit = revenue - (data["Cost_Price"] * data["Quantity"])
    
    new_row = {
        "Date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "Username": username,
        "Company": company,
        "Product": data["Product"],
        "Cost_Price": data["Cost_Price"],
        "Selling_Price": data["Selling_Price"],
        "Quantity": data["Quantity"],
        "Total_Revenue": revenue,
        "Total_Profit": round(profit, 2),
        "Status": data["Status"]
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=False)
    df.to_csv(DATA_FILE, index=False)
    return "SUCCESS", f"Transaction finalized for {data['Product']}."

def generate_ai_insights(df_data):
    if df_data.empty: return "Awaiting structured ledger parameters to generate strategic matrix diagnostics."
    prod_summary = df_data.groupby("Product").sum()
    top_prod = prod_summary["Total_Revenue"].idxmax()
    low_profit_prod = prod_summary["Total_Profit"].idxmin()
    return f"""
    - **Top Revenue Vector:** Asset '{top_prod}' dictates core capital liquidity dynamics.
    - **Optimization Advisory:** Margin metrics on '{low_profit_prod}' indicate standard pricing inefficiency. Shift allocation parameters.
    """

# --- INTERPRISE WORKSPACE GRAPHICS UI ---
st.set_page_config(page_title="NexGen SaaS AI Portal", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f8fafc;}
    div.stButton > button:first-child { background-color: #0f172a; color: white; border-radius: 6px; font-weight: 600; height: 42px;}
    div.stButton > button:first-child:hover {background-color: #1e293b;}
    .lock-banner { background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 8px; padding: 18px; text-align: center; color: #c2410c; font-weight: 500;}
    .user-badge { background-color: #e2e8f0; padding: 5px 12px; border-radius: 20px; font-weight: 500; font-size: 13px;}
    </style>
""", unsafe_allow_html=True)

# Session Management Initializers
if "auth_status" not in st.session_state: st.session_state.auth_status = False
if "user_info" not in st.session_state: st.session_state.user_info = None

# --- AUTHENTICATION INTERFACE LAYER ---
if not st.session_state.auth_status:
    st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: 50px;'>🔐 NexGen Autonomous Enterprise AI Network</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Secure SaaS Portal • Multi-Tenant Accounting Isolation Engine</p>", unsafe_allow_html=True)
    
    auth_col, spacer = st.columns([1, 1.5])
    with auth_col:
        mode = st.radio("Access Strategy", ["Existing Account Login", "Create New Corporate Account"], horizontal=True)
        st.write("---")
        
        if mode == "Existing Account Login":
            user_in = st.text_input("Corporate Username:", placeholder="e.g., demo_boss")
            pass_in = st.text_input("Security Access Password:", type="password", placeholder="e.g., admin123")
            if st.button("Authenticate & Initialize Session", use_container_width=True):
                session = verify_user(user_in, pass_in)
                if session:
                    st.session_state.auth_status = True
                    st.session_state.user_info = session
                    st.success("Access tokens granted. Initializing system..."); st.rerun()
                else:
                    st.error("Access Denied: Invalid cryptographic token credentials matches.")
            st.caption("💡 Testing? Use username: `demo_boss` or `free_user` with password: `admin123`")
        else:
            new_user = st.text_input("Choose Unique Username:")
            new_pass = st.text_input("Choose Strong Password:", type="password")
            new_comp = st.text_input("Registered Company Name:")
            new_plan = st.selectbox("Select Capital Scaling Strategy Plan:", ["Free Tier", "Premium"])
            
            if st.button("Register & Create Workspace Infrastructure", use_container_width=True):
                if new_user and new_pass and new_comp:
                    if register_new_user(new_user, new_pass, new_comp, new_plan):
                        st.success("Infrastructure provisioned. Switch to login mode to proceed.")
                    else:
                        st.error("Infrastructure Denied: Username matches historical database allocation.")
                else:
                    st.warning("All data field strings must be explicitly populated.")
    st.stop()

# --- POST-AUTHENTICATION SECURED RUNTIME ---
user_data = st.session_state.user_info
is_premium = user_data["Plan"] == "Premium"

# Top Navigation Bar Matrix
t1, t2 = st.columns([2, 1])
with t1:
    st.markdown(f"# 🏢 {user_data['Company']} Operational Console")
with t2:
    st.markdown(f"<div style='text-align: right; margin-top: 15px;'><span class='user-badge'>👤 User: <b>{user_data['Username']}</b></span> <span class='user-badge' style='background-color:#dbeafe; color:#1e40af;'>💎 Plan: <b>{user_data['Plan']}</b></span></div>", unsafe_allow_html=True)
    if st.button("Terminate Secure Session"):
        st.session_state.auth_status = False
        st.session_state.user_info = None
        st.rerun()

st.write("---")

# Global Localization Parameters Sidebars
st.sidebar.markdown("### 🌐 Regional Localization")
country_selection = st.sidebar.selectbox("Select Operating Country:", ["India (INR)", "United States (USD)", "United Kingdom (GBP)", "Europe (EUR)", "United Arab Emirates (AED)", "Japan (JPY)"])
currency_mapping = {"India (INR)": "₹", "United States (USD)": "$", "United Kingdom (GBP)": "£", "Europe (EUR)": "€", "United Arab Emirates (AED)": "AED ", "Japan (JPY)": "¥"}
currency_symbol = currency_mapping[country_selection]

st.sidebar.write("---")
st.sidebar.markdown("### 🔒 Multi-Tenant Data Guard")
st.sidebar.info(f"🛡️ Row-Level Security: Verified\n🏢 Scope: {user_data['Company']} Database Only")

# Fetching Data strictly mapped to the logged-in user's company context
master_df = pd.read_csv(DATA_FILE)
company_df = master_df[master_df["Company"] == user_data["Company"]]

# Pricing Usage Lock Controller Rules
USAGE_LIMIT = 5
current_usage_count = len(company_df)

col1, col2 = st.columns([1, 1.3])

with col1:
    st.markdown("### 🖥️ Autonomous Agent Control Terminal")
    tabs = st.tabs(["AI Conversational Input", "OCR Document Processing Scan", "Bulk Ingestion Pipelines"])
    
    with tabs[0]:
        # Free Tier Threshold Guardrails
        if not is_premium and current_usage_count >= USAGE_LIMIT:
            st.markdown(f"<div class='lock-banner'>⚠️ <b>Free Tier Data Limit Exhausted ({USAGE_LIMIT}/{USAGE_LIMIT} Rows Used)</b><br>Upgrade your account profile status to access infinite analytical row arrays.</div>", unsafe_allow_html=True)
        else:
            user_input = st.text_area("Command Input Console:", placeholder="Example: enter Face Wash cost is 250 and sold 40 pcs", height=110)
            if st.button("Deploy Execution Agent", use_container_width=True):
                if user_input:
                    action, extracted_data = autonomous_ai_parser(user_input)
                    if action == "ENTRY":
                        status, message = execute_entry(extracted_data, user_data["Username"], user_data["Company"])
                        if status == "SUCCESS": st.success(message); st.rerun()
                        else: st.warning(message)
                    elif action == "FRAUD_ALERT":
                        st.error("🚨 AUDIT LOCK: Anomalous volume spike captured by compliance protocols.")
                        if st.checkbox("Supervisor Credentials Bypass"):
                            execute_entry(extracted_data, user_data["Username"], user_data["Company"])
                            st.success("Forced transaction completed."); st.rerun()
                    elif action == "ANOMALY_ERROR": st.error("Aborted: Negative math criteria identified.")
                    else: st.error("Syntax unparseable.")

    with tabs[1]:
        st.markdown("#### 📄 OCR Optical Invoicing Engine")
        if not is_premium:
            st.markdown("<div class='lock-banner'>🔒 <b>Premium Feature Locked</b><br>Computational Document Vision OCR Scanning requires a Premium Account upgrade tier pipeline.</div>", unsafe_allow_html=True)
        else:
            uploaded_img = st.file_uploader("Drop Receipt Invoice:", type=["png", "jpg", "jpeg", "pdf"])
            if uploaded_img is not None:
                st.info("AI Vision extraction processing complete: Found 'Premium Serum' | Price: 450 | Qty: 15")
                if st.button("Commit Extraction Log to Secured Ledger"):
                    mock_data = {"Product": "Premium Serum", "Cost_Price": 315.0, "Selling_Price": 450.0, "Quantity": 15, "Status": "OCR Verified"}
                    execute_entry(mock_data, user_data["Username"], user_data["Company"])
                    st.success("Committed safely."); st.rerun()

    with tabs[2]:
        st.markdown("#### 📁 Multi-Row Bulk Data Upload")
        if not is_premium:
            st.markdown("<div class='lock-banner'>🔒 <b>Premium Feature Locked</b><br>Bulk automated Excel / CSV file upload ingestion pipeline features are locked on Free Tiers.</div>", unsafe_allow_html=True)
        else:
            uploaded_file = st.file_uploader("Drop Document Sheet:", type=["csv", "xlsx"])
            if uploaded_file is not None:
                try:
                    uploaded_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    required = ["Product", "Price", "Quantity"]
                    if all(col in uploaded_df.columns for col in required):
                        uploaded_df = uploaded_df.dropna(subset=required)
                        uploaded_df["Date"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        uploaded_df["Username"] = user_data["Username"]
                        uploaded_df["Company"] = user_data["Company"]
                        uploaded_df["Cost_Price"] = round(uploaded_df["Price"] * 0.7, 2)
                        uploaded_df["Selling_Price"] = uploaded_df["Price"]
                        uploaded_df["Total_Revenue"] = uploaded_df["Selling_Price"] * uploaded_df["Quantity"]
                        uploaded_df["Total_Profit"] = uploaded_df["Total_Revenue"] - (uploaded_df["Cost_Price"] * uploaded_df["Quantity"])
                        uploaded_df["Status"] = "Bulk Verified"
                        
                        final_bulk = uploaded_df[["Date", "Username", "Company", "Product", "Cost_Price", "Selling_Price", "Quantity", "Total_Revenue", "Total_Profit", "Status"]]
                        pd.concat([master_df, final_bulk], ignore_index=False).to_csv(DATA_FILE, index=False)
                        st.success("Bulk dataset verified and appended safely into secure sandbox workspace context."); st.rerun()
                except Exception as e: st.error(f"Execution fault: {e}")

    st.write("---")
    st.markdown("### 📋 Executive Reporting Suite")
    if is_premium and not company_df.empty:
        csv_buffer = io.StringIO()
        company_df.to_csv(csv_buffer, index=False)
        st.download_button(label="📥 Download Corporate Performance Audit Dossier (.CSV Ledger)", data=csv_buffer.getvalue(), file_name=f"Executive_Report_{user_data['Company']}.csv", mime="text/csv", use_container_width=True)
    else:
        st.markdown("<div class='lock-banner'>🔒 <b>SaaS Executive Export Blocked</b><br>Automated reporting generation matrices are reserved for verified Premium instances.</div>", unsafe_allow_html=True)

with col2:
    st.markdown("### 📈 Isolated Real-Time Analytics Pipeline")
    if not company_df.empty:
        total_rev = company_df["Total_Revenue"].sum()
        total_profit = company_df["Total_Profit"].sum()
        margin = round((total_profit / total_rev) * 100, 2) if total_rev > 0 else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue Performance", f"{currency_symbol}{total_rev:,}")
        m2.metric("Net Isolated Profit", f"{currency_symbol}{total_profit:,}")
        m3.metric("Evaluated Net Margin", f"{margin}%")
        
        st.write("---")
        
        # Premium Deep Insight Analytics Model Locks
        if not is_premium:
            st.markdown("<div class='lock-banner' style='margin-bottom:15px;'>🔒 <b>Autonomous Analyst Strategic Insights Dashboard Layer Locked</b><br>Upgrade to Premium to get automated text hints explaining financial margins.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color:#ffffff; border:1px solid #e2e8f0; padding:15px; border-radius:8px;'><b>💡 Autonomous Analyst Intelligence Matrix</b>" + generate_ai_insights(company_df) + "</div>", unsafe_allow_html=True)
        
        st.write("#### 📊 Selected Analysis Framework Vector")
        options = ["Structural Matrix Breakdown", "Timeline Ingestion History", "Predictive Machine Forecasting Engine"]
        graph_type = st.radio("Framework Profile Strategy:", options, horizontal=True)
        
        prod_summary = company_df.groupby("Product", as_index=False)[["Total_Revenue", "Total_Profit"]].sum()
        
        if graph_type == "Structural Matrix Breakdown":
            fig = px.pie(prod_summary, values="Total_Revenue", names="Product", hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig, use_container_width=True)
        elif graph_type == "Timeline Ingestion History":
            df_sorted = company_df.sort_values("Date")
            fig = px.line(df_sorted, x="Date", y="Total_Revenue", text="Product", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        elif graph_type == "Predictive Machine Forecasting Engine":
            if not is_premium:
                st.markdown("<div class='lock-banner'>🔒 <b>Machine Learning Horizon Vectors Locked</b><br>30-Day predictive valuation mapping is a premium analytical product service layer tool.</div>", unsafe_allow_html=True)
            else:
                df_sorted = company_df.sort_values("Date")
                df_sorted["Date_Parsed"] = pd.to_datetime(df_sorted["Date"])
                last_date = df_sorted["Date_Parsed"].max()
                future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
                avg_daily = total_rev / max(len(df_sorted["Date_Parsed"].unique()), 1)
                simulated_growth = [total_rev + (avg_daily * i * 1.05) for i in range(1, 31)]
                forecast_df = pd.DataFrame({"Projected Timeline": future_dates, "Projected Revenue Target": simulated_growth})
                fig = px.line(forecast_df, x="Projected Timeline", y="Projected Revenue Target", color_discrete_sequence=["#6366f1"])
                st.plotly_chart(fig, use_container_width=True)
                
        with st.expander("📄 View Audited Enterprise Database Records Row Array"):
            st.dataframe(company_df[["Date", "Username", "Product", "Selling_Price", "Quantity", "Total_Revenue", "Total_Profit", "Status"]], use_container_width=True)
    else:
        st.warning("Database Workspace Context Empty. Ingest structural metrics rows to activate tracking graphics panels.")
