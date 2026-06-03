import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# =========================
# AI CONFIG
# =========================
genai.configure(api_key="YOUR_API_KEY_HERE")  # replace this

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
)
""")

conn.commit()

# =========================
# UI
# =========================
st.title("💰 Personal Finance Tracker")

# =========================
# INPUT FORM
# =========================
date = st.date_input("Date")

category = st.selectbox(
    "Category",
    ["Food", "Travel", "Shopping", "Bills", "Other"]
)

amount = st.number_input("Amount", min_value=0.0)
description = st.text_input("Description")

# =========================
# SAVE DATA
# =========================
if st.button("Save Expense"):
    cursor.execute("""
        INSERT INTO expenses (date, category, amount, description)
        VALUES (?, ?, ?, ?)
    """, (str(date), category, amount, description))

    conn.commit()
    st.success("Expense Saved Successfully!")

# =========================
# LOAD DATA
# =========================
df = pd.read_sql_query("SELECT * FROM expenses", conn)

st.subheader("📋 Expense Records")
st.dataframe(df)

# =========================
# SAFE CALCULATIONS
# =========================
total_expense = df["amount"].sum() if not df.empty else 0
total_records = len(df)

top_category = "N/A"
if not df.empty:
    top_category = df.groupby("category")["amount"].sum().idxmax()

# =========================
# DASHBOARD
# =========================
st.subheader("📊 Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Total Expenses", f"₹{total_expense}")
col2.metric("Total Records", total_records)
col3.metric("Top Category", top_category)

# =========================
# PIE CHART
# =========================
if not df.empty:
    st.subheader("📈 Expense Distribution")

    category_data = df.groupby("category")["amount"].sum()

    fig, ax = plt.subplots()
    ax.pie(category_data, labels=category_data.index, autopct="%1.1f%%")
    st.pyplot(fig)

# =========================
# BUDGET TRACKER
# =========================
st.subheader("💵 Monthly Budget Tracker")

budget = st.number_input("Enter Monthly Budget", min_value=0.0, value=10000.0)
remaining = budget - total_expense

st.metric("Remaining Budget", f"₹{remaining}")

# =========================
# DELETE EXPENSE
# =========================
st.subheader("🗑 Delete Expense")

delete_id = st.number_input("Enter Expense ID to Delete", min_value=1, step=1)

if st.button("Delete Expense"):
    cursor.execute("DELETE FROM expenses WHERE id=?", (delete_id,))
    conn.commit()
    st.success("Expense Deleted Successfully!")
    st.rerun()

# =========================
# AI ADVISOR
# =========================
st.subheader("🤖 AI Financial Advisor")

if st.button("Get AI Advice"):

    if df.empty:
        st.warning("No expenses to analyze yet.")
    else:
        expense_summary = df.groupby("category")["amount"].sum().to_string()

        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(f"""
        You are a financial advisor.

        Give simple saving tips based on these expenses:

        {expense_summary}
        """)

        st.markdown(response.text)
