"""
data_handler.py
-----------------
All local JSON persistence + data cleaning logic lives here.
No SQL / SQLite / external DB is used anywhere in this project.
"""

import json
import os
from datetime import datetime

import pandas as pd

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROCESSED_DATA_FILE = os.path.join(DATA_DIR, "processed_data.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ----------------------------------------------------------------------
# Generic JSON helpers
# ----------------------------------------------------------------------
def load_json(filepath: str, default=None):
    """Load a JSON file. Returns `default` if the file doesn't exist yet."""
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}


def save_json(filepath: str, data) -> None:
    """Save a dict/list to a JSON file with pretty formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, default=str)


# ----------------------------------------------------------------------
# User management (users.json)
# ----------------------------------------------------------------------
def load_users() -> dict:
    """Returns the full users dict: {username: {...user record...}}"""
    return load_json(USERS_FILE, default={})


def save_users(users: dict) -> None:
    save_json(USERS_FILE, users)


def get_user(username: str):
    """Fetch a single user record by username. Returns None if not found."""
    users = load_users()
    return users.get(username)


def create_local_profile(username: str, name: str, password_hash: str, salt: str) -> None:
    """Create a single local profile (no roles, no credits/plan — personal tool)."""
    users = load_users()
    users[username] = {
        "name": name,
        "salt": salt,
        "password_hash": password_hash,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_users(users)


def update_password(username: str, salt: str, password_hash: str) -> bool:
    """Update a local profile's stored salt + hash (used by the Settings page)."""
    users = load_users()
    if username not in users:
        return False
    users[username]["salt"] = salt
    users[username]["password_hash"] = password_hash
    save_users(users)
    return True


# ----------------------------------------------------------------------
# Bulk data cleaning (CSV / Excel uploads)
# ----------------------------------------------------------------------
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Automated cleaning pipeline:
    - Drop fully-empty rows/columns
    - Drop duplicate rows
    - Drop rows containing any null values
    - Strip whitespace from string columns
    - Reset index
    """
    cleaned = df.copy()

    # Drop columns/rows that are entirely empty
    cleaned = cleaned.dropna(axis=1, how="all")
    cleaned = cleaned.dropna(axis=0, how="all")

    # Strip whitespace on text columns
    for col in cleaned.select_dtypes(include="object").columns:
        cleaned[col] = cleaned[col].astype(str).str.strip()

    # Drop duplicate rows
    cleaned = cleaned.drop_duplicates()

    # Drop rows with any remaining nulls
    cleaned = cleaned.dropna(axis=0, how="any")

    cleaned = cleaned.reset_index(drop=True)
    return cleaned


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """
    Reads a Streamlit UploadedFile (CSV or Excel) into a DataFrame.
    """
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")


def save_processed_data(username: str, df: pd.DataFrame, source_filename: str) -> None:
    """
    Persist a cleaned dataset into processed_data.json under the uploading
    user's namespace, along with metadata (upload time, row/col counts).
    """
    store = load_json(PROCESSED_DATA_FILE, default={})

    record = {
        "source_filename": source_filename,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": len(df),
        "columns": list(df.columns),
        "data": df.to_dict(orient="records"),
    }

    if username not in store:
        store[username] = []
    store[username].append(record)

    save_json(PROCESSED_DATA_FILE, store)


def get_user_datasets(username: str) -> list:
    """Return all previously uploaded/cleaned datasets for a user."""
    store = load_json(PROCESSED_DATA_FILE, default={})
    return store.get(username, [])


def dataset_to_dataframe(record: dict) -> pd.DataFrame:
    """Convert a stored dataset record back into a DataFrame for charting."""
    return pd.DataFrame(record.get("data", []))


def overwrite_dataset(username: str, dataset_index: int, df: pd.DataFrame) -> bool:
    """
    Replace the data/rows/columns of an existing dataset record in place
    (used after manual row add/edit/delete in the Data Entry page).
    """
    store = load_json(PROCESSED_DATA_FILE, default={})
    records = store.get(username, [])
    if dataset_index < 0 or dataset_index >= len(records):
        return False
    records[dataset_index]["data"] = df.to_dict(orient="records")
    records[dataset_index]["rows"] = len(df)
    records[dataset_index]["columns"] = list(df.columns)
    records[dataset_index]["last_edited"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    store[username] = records
    save_json(PROCESSED_DATA_FILE, store)
    return True


def create_blank_dataset(username: str, name: str, columns: list) -> None:
    """
    Create a brand-new empty dataset with a chosen set of columns —
    for pure manual data entry (no file upload needed).
    """
    store = load_json(PROCESSED_DATA_FILE, default={})
    record = {
        "source_filename": name,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": 0,
        "columns": columns,
        "data": [],
    }
    if username not in store:
        store[username] = []
    store[username].append(record)
    save_json(PROCESSED_DATA_FILE, store)


def merge_datasets(dfs: list, mode: str = "stack") -> pd.DataFrame:
    """
    Combine multiple DataFrames into one.
    mode="stack": append rows on top of each other (same/similar columns).
    mode="side_by_side": join columns side by side on their row index.
    """
    dfs = [d for d in dfs if d is not None and not d.empty]
    if not dfs:
        return pd.DataFrame()
    if mode == "side_by_side":
        return pd.concat(dfs, axis=1)
    # default: stack rows, union of columns, missing values become NaN
    return pd.concat(dfs, axis=0, ignore_index=True, sort=False)


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes, ready for a Streamlit download button."""
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to XLSX bytes, ready for a Streamlit download button."""
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buffer.getvalue()


# ----------------------------------------------------------------------
# Auto AI Insights (rule-based, no external API needed)
# ----------------------------------------------------------------------
def generate_insights(df: pd.DataFrame) -> list:
    """
    Analyze a cleaned DataFrame and return a list of plain-language
    insight strings: column types, key stats, correlations, outliers,
    and top categories. Pure pandas/numpy — no external AI call required.
    """
    insights = []
    if df.empty:
        return ["Dataset is empty — nothing to analyze."]

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols = df.select_dtypes(include="object").columns.tolist()

    # Try to auto-detect date-like text columns
    date_cols = []
    for col in text_cols:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                date_cols.append(col)
        except Exception:
            pass
    text_cols = [c for c in text_cols if c not in date_cols]

    # --- Overview ---
    insights.append(
        f"📦 Dataset has **{len(df)} rows** and **{len(df.columns)} columns** "
        f"({len(numeric_cols)} numeric, {len(text_cols)} categorical, {len(date_cols)} date-like)."
    )

    # --- Numeric column stats ---
    for col in numeric_cols[:6]:
        series = df[col].dropna()
        if series.empty:
            continue
        mean_v, min_v, max_v = series.mean(), series.min(), series.max()
        insights.append(
            f"📊 **{col}** ranges from {min_v:,.2f} to {max_v:,.2f}, averaging {mean_v:,.2f}."
        )
        # Simple outlier flag using IQR
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
            if len(outliers) > 0:
                insights.append(
                    f"⚠️ **{col}** has {len(outliers)} potential outlier value(s) far from the typical range."
                )

    # --- Categorical column top values ---
    for col in text_cols[:4]:
        counts = df[col].value_counts()
        if not counts.empty:
            top_val, top_count = counts.index[0], counts.iloc[0]
            pct = top_count / len(df) * 100
            insights.append(
                f"🏷️ **{col}**: most frequent value is \"{top_val}\" ({top_count} rows, {pct:.1f}%), "
                f"with {counts.shape[0]} unique values overall."
            )

    # --- Date range ---
    for col in date_cols[:2]:
        parsed = pd.to_datetime(df[col], errors="coerce", format="mixed").dropna()
        if not parsed.empty:
            insights.append(
                f"📅 **{col}** spans from {parsed.min().date()} to {parsed.max().date()}."
            )

    # --- Correlations between numeric columns ---
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        seen = set()
        strong_pairs = []
        for c1 in numeric_cols:
            for c2 in numeric_cols:
                if c1 == c2 or (c2, c1) in seen:
                    continue
                seen.add((c1, c2))
                val = corr.loc[c1, c2]
                if pd.notna(val) and abs(val) >= 0.6:
                    strong_pairs.append((c1, c2, val))
        for c1, c2, val in strong_pairs[:3]:
            direction = "positively" if val > 0 else "negatively"
            insights.append(
                f"🔗 **{c1}** and **{c2}** are strongly {direction} correlated (r = {val:.2f})."
            )

    # --- Missing data note (should be near-zero after cleaning) ---
    total_nulls = int(df.isna().sum().sum())
    if total_nulls > 0:
        insights.append(f"🧹 Note: {total_nulls} null value(s) remain after cleaning.")

    return insights
