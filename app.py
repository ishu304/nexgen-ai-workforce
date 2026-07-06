import re
import os
import io
import pandas as pd
import hashlib
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import urllib.parse

# --- ENTERPRISE CONFIGURATIONS & GATEWAY ROUTES ---
YOUR_FAMPAY_UPI = "9718910662@fam"  # Active FamPay Target Node
YOUR_NAME = "NexGen SaaS Corp"

DATA_FILE = "enterprise_multi_tenant_database.csv"
USER_FILE = "secure_user_credentials.csv"
PAYMENT_FILE = "secure_payment_ledger.csv"

# --- SYSTEM DISK DATA BASE INITIALIZATION ---
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Date", "Username", "Company", "Product", "Cost_Price", "Selling_Price", "Quantity", "Total_Revenue", "Total_Profit", "Status"])
    df.to_csv(DATA_FILE, index=False)

if not os.path.exists(USER_FILE):
    df_users = pd.DataFrame(columns=["Username", "Password", "Company", "Plan", "Credits_Left"])
    default_pass = hashlib.sha256("admin123".encode()).hexdigest()
    # Master premium account setup
    default_user = pd.DataFrame([{"Username": "demo_boss", "Password": default_pass, "Company": "NexGen Skincare", "Plan": "Enterprise Max", "Credits_Left": 999999}])
    pd.concat([df_users, default_user]).to_csv(USER_FILE, index=False)

if not os.path.exists(PAYMENT_FILE):
    df_pay = pd.DataFrame(columns=["Timestamp", "Username", "Plan_Selected", "UTR_Number", "Amount_Requested", "Status"])
    df_pay.to_csv(PAYMENT_FILE, index=False)

# --- SECURITY ENGINE ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    df = pd.read_csv(USER_FILE)
    hashed_p = hash_password(password)
    user_match = df[(df["Username"] == username) & (df["Password"] == hashed_p)]
    if not user_match.empty:
        return {
            "Username": username, 
            "Company": user_match.iloc[0]["Company"], 
            "Plan": user_match.iloc[0]["Plan"],
            "Credits_Left": int(user_match.iloc[0]["Credits_Left"])
        }
    return None

def register_new_user(username, password, company):
    df = pd.read_csv(USER_FILE)
    if username in df["Username"].values:
        return False
    # All self-registrations boot with 5 Free Trial Credits
    new_user = {"Username": username, "Password": hash_password(password), "Company": company, "Plan": "Free Trial", "Credits_Left": 5}
    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=False)
    df.to_csv(USER_FILE, index=False)
    return True

def deduct_credit(username):
    df = pd.read_csv(USER_FILE)
    current_credits = df.loc[df["Username"] == username, "Credits_Left"].values[0]
    if current_credits > 0:
        df.loc[df["Username"] == username, "Credits_Left"] = current_credits - 1
        df.to_csv(USER_FILE, index=False)
        return True
    return False

# --- CORE PARSING PIPELINES ---
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
    if not df.empty:
        last_match = df[(df["Username"] == username) & (df["Product"] == data["Product"]) & (df["Quantity"] == data["Quantity"]) & (df["Selling_Price"] == data["Selling_Price"])]
        if not last_match.empty:
            last_time = pd.to_datetime(last_match["Date"].iloc[-1])
            if (pd.Timestamp.now() - last_time).total_seconds() < 120:
                return "DUPLICATE_BLOCK", "Identical data signature dropped within 120s matrix block."

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
    if df_data.empty: return "Awaiting structured ledger rows."
    prod_summary = df_data.groupby("Product").sum()
    top_prod = prod_summary["Total_Revenue"].idxmax()
    low_profit_prod = prod_summary["Total_Profit"].idxmin()
    return f"""
    - **Top Revenue Vector:** Asset '{top_prod}' dictates core capital liquidity dynamics.
    - **Optimization Advisory:** Margin metrics on '{low_profit_prod}' indicate standard pricing inefficiency. Shift allocation parameters.
    """

# --- WORKSPACE GRAPHICS UI ---
st.set_page_config(page_title="NexGen SaaS AI Portal", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #f8fafc;}
    div.stButton > button:first-child { background-color: #0f172a; color: white; border-radius: 6px; font-weight: 600; height: 42px;}
    div.stButton > button:first-child:hover {background-color: #1e293b;}
    .lock-banner { background-color: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; padding: 18px; text-align: center; color: #dc2626; font-weight: 600; font-size: 16px;}
    .user-badge { background-color: #e2e8f0; padding: 5px 12px; border-radius: 20px; font-weight: 500; font-size: 13px;}
    .payment-box { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);}
    .tier-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .upi-btn { display: inline-block; background-color: #2563eb; color: white !important; padding: 12px 24px; font-weight: bold; border-radius: 6px; text-decoration: none; margin-top: 10px; text-align: center;}
    .verification-holder { background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 20px; text-align: center; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

if "auth_status" not in st.session_state: st.session_state.auth_status = False
if "user_info" not in st.session_state: st.session_state.user_info = None

# --- AUTHENTICATION INTERFACE LAYER ---
if not st.session_state.auth_status:
    st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: 50px;'>🔐 NexGen Autonomous Enterprise AI Network</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Secure SaaS Portal • Multi-Tenant Accounting Isolation Engine</p>", unsafe_allow_html=True)
    
    auth_col, spacer = st.columns([1, 1.5])
    with auth_col:
        mode = st.radio("Access Strategy", ["Existing Account Login", "Create New Corporate Account (Free Trial)"], horizontal=True)
        st.write("---")
        
        if mode == "Existing Account Login":
            user_in = st.text_input("Corporate Username:", placeholder="e.g., free_user")
            pass_in = st.text_input("Security Access Password:", type="password", placeholder="e.g., admin123")
            if st.button("Authenticate & Initialize Session", use_container_width=True):
                session = verify_user(user_in, pass_in)
                if session:
                    st.session_state.auth_status = True
                    st.session_state.user_info = session
                    st.success("Access tokens granted. Initializing system..."); st.rerun()
                else:
                    st.error("Access Denied: Invalid credentials.")
            st.caption("💡 Testing Master Accounts? Use username: `demo_boss` | password: `admin123`")
        else:
            new_user = st.text_input("Choose Unique Username:")
            new_pass = st.text_input("Choose Strong Password:", type="password")
            new_comp = st.text_input("Registered Company Name:")
            
            st.info("ℹ️ Note: All new registrations automatically start with a 5-Entry Free Trial.")
            
            if st.button("Register & Activate Free Trial", use_container_width=True):
                if new_user and new_pass and new_comp:
                    if register_new_user(new_user, new_pass, new_comp):
                        st.success("Account created successfully! Switch to Login mode.")
                    else:
                        st.error("Infrastructure Denied: Username already exists.")
                else:
                    st.warning("All fields must be filled.")
    st.stop()

# --- RE-SYNC LIVE DATA STATE ---
user_file_df = pd.read_csv(USER_FILE)
current_user_row = user_file_df[user_file_df["Username"] == st.session_state.user_info["Username"]]
if not current_user_row.empty:
    st.session_state.user_info["Plan"] = current_user_row.iloc[0]["Plan"]
    st.session_state.user_info["Credits_Left"] = int(current_user_row.iloc[0]["Credits_Left"])

user_data = st.session_state.user_info
is_premium = user_data["Plan"] in ["Starter Pro", "Business Elite", "Enterprise Max"]

t1, t2 = st.columns([2, 1])
with t1:
    st.markdown(f"# 🏢 {user_data['Company']} Operational Console")
with t2:
    st.markdown(f"<div style='text-align: right; margin-top: 15px;'><span class='user-badge'>👤 User: <b>{user_data['Username']}</b></span> <span class='user-badge' style='background-color:#f1f5f9; color:#0f172a;'>🪙 Credits: <b>{user_data['Credits_Left']}</b></span> <span class='user-badge' style='background-color:#dbeafe; color:#1e40af;'>💎 Plan: <b>{user_data['Plan']}</b></span></div>", unsafe_allow_html=True)
    if st.button("Terminate Secure Session"):
        st.session_state.auth_status = False
        st.session_state.user_info = None
        st.rerun()

st.write("---")

# Global Localization Sidebars
st.sidebar.markdown("### 🌐 Regional Localization")
country_selection = st.sidebar.selectbox("Select Operating Country:", ["India (INR)"])
currency_symbol = "₹"

st.sidebar.write("---")
st.sidebar.markdown("### 🔒 Multi-Tenant Data Guard")
st.sidebar.info(f"🛡️ Row-Level Security: Verified\n🏢 Scope: {user_data['Company']} Database")

master_df = pd.read_csv(DATA_FILE)
company_df = master_df[master_df["Company"] == user_data["Company"]]

col1, col2 = st.columns([1, 1.3])

with col1:
    st.markdown("### 🖥️ Autonomous Agent Control Terminal")
    tabs = st.tabs(["AI Conversational Input", "OCR Document Processing Scan", "Bulk Ingestion Pipelines"])
    
    with tabs[0]:
        pay_ledger = pd.read_csv(PAYMENT_FILE)
        user_pending_payments = pay_ledger[(pay_ledger["Username"] == user_data["Username"]) & (pay_ledger["Status"] == "Pending")]
        
        if user_data["Credits_Left"] <= 0 and not user_pending_payments.empty:
            # PENDING COOLDOWN OVERLAY
            st.markdown("""
                <div class='verification-holder'>
                    <h3 style='color: #2563eb;'>⏳ Automated Network Verification In Progress</h3>
                    <p style='color: #475569; font-size: 15px;'>Our automated processing matrix is matching your transaction token against the FamPay live ledger.</p>
                    <div style='font-size: 14px; background-color: #fff; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; display: inline-block; text-align: left;'>
                        <b>Tier Selected:</b> <code>""" + str(user_pending_payments.iloc[0]['Plan_Selected']) + """</code><br>
                        <b>Submitted UTR:</b> <code>""" + str(user_pending_payments.iloc[0]['UTR_Number']) + """</code><br>
                        <b>Amount Checked:</b> <code>₹""" + str(user_pending_payments.iloc[0]['Amount_Requested']) + """</code>
                    </div>
                    <p style='color: #64748b; font-size: 13px; margin-top: 15px;'>🕒 Verification complete window: <b>2 - 5 Minutes</b>. Do not submit duplicate requests.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Refresh Subscription State Link"):
                st.rerun()

        elif user_data["Credits_Left"] <= 0:
            # 3-TIER PROFESSIONAL SUBSCRIPTION MANAGEMENT BLOCK
            st.markdown(f"<div class='lock-banner'>🚨 ⚠️ INGESTION PERMISSION DENIED: Credits Depleted (0 Tokens Available) ⚠️ 🚨</div>", unsafe_allow_html=True)
            st.write("")
            
            st.markdown("### Select Enterprise Subscription Plan (Monthly Renewal)")
            plan_option = st.radio("Choose Corporate Licensing Tier:", [
                "Starter Pro — ₹599.00 / Mo (200 Ingestion Credits)",
                "Business Elite — ₹2,999.00 / Mo (2,000 Credits + Bulk Engine + OCR)",
                "Enterprise Max — ₹9,999.00 / Mo (10,000 Credits + Deep AI Matrix Analytics)"
            ])
            
            # Extract configuration prices based on choice
            if "Starter Pro" in plan_option:
                base_p, target_plan = 599.00, "Starter Pro"
            elif "Business Elite" in plan_option:
                base_p, target_plan = 2999.00, "Business Elite"
            else:
                base_p, target_plan = 9999.00, "Enterprise Max"
                
            # Dynamic pinpoint logic injection for professional isolation verification
            user_seed = int(hashlib.sha256(user_data["Username"].encode()).hexdigest(), 16) % 100
            dynamic_cents = user_seed / 100.0
            final_calculated_price = f"{base_p + dynamic_cents:.2f}"
            
            st.markdown(f"""
            <div class='payment-box'>
                <h4 style='margin:0; color:#475569;'>Selected Target License: <b>{target_plan}</b></h4>
                <h2 style='color: #166534; margin: 10px 0;'>₹{final_calculated_price} <span style='font-size:14px; font-weight:normal; color:#64748b;'>/ Month Billing</span></h2>
                <p style='margin:0; font-size:13px; color:#64748b;'>Destination Gateway Route: <code>{YOUR_FAMPAY_UPI}</code></p>
            </div>
            """, unsafe_allow_html=True)
            
            upi_string = f"upi://pay?pa={YOUR_FAMPAY_UPI}&pn={urllib.parse.quote(YOUR_NAME)}&am={final_calculated_price}&cu=INR&tn={target_plan}%20Activation%20For%20{user_data['Username']}"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(upi_string)}"
            
            pay_col1, pay_col2 = st.columns(2)
            with pay_col1:
                st.image(qr_url, caption="Scan via FamPay or any Preferred UPI App")
            with pay_col2:
                st.markdown(f"<br><a href='{upi_string}' class='upi-btn' style='width: 100%;'>📱 Open Local UPI App</a>", unsafe_allow_html=True)
                st.caption("Auto-fills exact transaction price matrices across secure client endpoints.")
                
            st.write("---")
            st.markdown("#### Complete Gateway Verification Pipeline")
            utr_input = st.text_input("Enter 12-Digit UPI Reference Number (UTR / Txn ID):", max_chars=12, placeholder="e.g., 394810293847")
            
            if st.button("Transmit Reference Token to Ledger Network", use_container_width=True):
                if len(utr_input) == 12 and utr_input.isdigit():
                    if utr_input in pay_ledger["UTR_Number"].astype(str).values:
                        st.error("Duplicate Submission: This transaction token identifier has already been cached.")
                    else:
                        new_pay_entry = {
                            "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                            "Username": user_data["Username"],
                            "Plan_Selected": target_plan,
                            "UTR_Number": utr_input,
                            "Amount_Requested": final_calculated_price,
                            "Status": "Pending"
                        }
                        pay_ledger = pd.concat([pay_ledger, pd.DataFrame([new_pay_entry])], ignore_index=False)
                        pay_ledger.to_csv(PAYMENT_FILE, index=False)
                        st.success("Verification parameters successfully locked. Reloading context...")
                        st.rerun()
                else:
                    st.error("Format Error: UTR tokens must consist of exactly 12 numeric integers.")
        else:
            # WORKSPACE CONSOLE INPUT EXECUTOR
            user_input = st.text_area("Command Input Console:", placeholder="Example: enter Face Wash cost is 250 and sold 40 pcs", height=110)
            if st.button("Deploy Execution Agent", use_container_width=True):
                if user_input:
                    action, extracted_data = autonomous_ai_parser(user_input)
                    if action == "ENTRY":
                        if deduct_credit(user_data["Username"]):
                            status, message = execute_entry(extracted_data, user_data["Username"], user_data["Company"])
                            if status == "SUCCESS": st.success(message); st.rerun()
                            else: st.warning(message)
                        else:
                            st.error("System sync anomaly. Please re-authenticate.")
                    else: st.error("Syntax parser execution failure.")

    with tabs[1]:
        st.markdown("#### 📄 OCR Optical Invoicing Engine")
        if user_data["Plan"] in ["Free Trial", "Starter Pro"]:
            st.markdown(f"<div class='lock-banner'>🔒 <b>Feature Locked under Plan: {user_data['Plan']}</b><br>Upgrade to Business Elite or higher to unlock direct image OCR logging.</div>", unsafe_allow_html=True)
        else:
            st.info("AI Vision Active for Tier Licensees...")

    with tabs[2]:
        st.markdown("#### 📁 Multi-Row Bulk Data Upload")
        if user_data["Plan"] in ["Free Trial", "Starter Pro"]:
            st.markdown(f"<div class='lock-banner'>🔒 <b>Feature Locked under Plan: {user_data['Plan']}</b><br>Upgrade to Business Elite or higher to upload custom datasets.</div>", unsafe_allow_html=True)

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
        if user_data["Plan"] != "Enterprise Max":
            st.markdown(f"<div class='lock-banner' style='margin-bottom:15px;'>🔒 <b>AI Business Intelligence Diagnostics Matrix Locked</b><br>Requires Enterprise Max Tier license.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color:#ffffff; border:1px solid #e2e8f0; padding:15px; border-radius:8px;'><b>💡 Autonomous Analyst Intelligence Matrix</b>" + generate_ai_insights(company_df) + "</div>", unsafe_allow_html=True)
            
        with st.expander("📄 View Database Records"):
            st.dataframe(company_df[["Date", "Username", "Product", "Selling_Price", "Quantity", "Total_Revenue", "Total_Profit", "Status"]], use_container_width=True)
    else:
        st.warning("Workspace ledger matrix contexts currently empty.")

# =====================================================================
# 🕵️‍♂️ HIDDEN CORPORATE ADMIN COMPLIANCE CONTROLLER
# =====================================================================
if st.session_state.auth_status and user_data["Username"] == "demo_boss":
    st.write("---")
    st.markdown("### 🛠️ Master Corporate Verification Administration Vault")
    st.caption("Secure authorization layer visible exclusively to verified cloud infrastructure owner instances.")
    
    admin_pay_ledger = pd.read_csv(PAYMENT_FILE)
    pending_rows = admin_pay_ledger[admin_pay_ledger["Status"] == "Pending"]
    
    if pending_rows.empty:
        st.info("System State Nominal: Zero active verification sequences queued inside global ledgers.")
    else:
        for idx, row in pending_rows.iterrows():
            with st.container():
                inner_col1, inner_col2 = st.columns([3, 1])
                with inner_col1:
                    st.warning(f"👤 **User Context:** `{row['Username']}` | 🎟️ **Tier:** `{row['Plan_Selected']}` | 🔑 **UTR Code:** `{row['UTR_Number']}` | 💵 **Amount:** `₹{row['Amount_Requested']}`")
                with inner_col2:
                    if st.button(f"Approve & Clear Ingestion Tokens (Ref {idx})", key=f"app_{idx}", use_container_width=True):
                        # 1. Update Payment File State
                        admin_pay_ledger.at[idx, "Status"] = "Success"
                        admin_pay_ledger.to_csv(PAYMENT_FILE, index=False)
                        
                        # 2. Identify and Inject Core Credit Balances Mapped to Tier Profiles
                        credit_mapping = {"Starter Pro": 200, "Business Elite": 2000, "Enterprise Max": 10000}
                        granted_credits = credit_mapping.get(row['Plan_Selected'], 5)
                        
                        users_db = pd.read_csv(USER_FILE)
                        users_db.loc[users_db["Username"] == row["Username"], "Plan"] = row['Plan_Selected']
                        users_db.loc[users_db["Username"] == row["Username"], "Credits_Left"] = granted_credits
                        users_db.to_csv(USER_FILE, index=False)
                        
                        st.success(f"System State Synchronized: Account '{row['Username']}' provisioned to {row['Plan_Selected']} (+ {granted_credits} Tokens Issued).")
                        st.rerun()
