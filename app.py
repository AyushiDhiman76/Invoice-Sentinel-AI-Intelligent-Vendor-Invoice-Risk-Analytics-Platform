import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import tempfile
import re


from PyPDF2 import PdfReader
from sklearn.ensemble import IsolationForest
from auth import register_user, login_user
from inference.predict_freight import predict_freight_cost
from inference.predict_invoice_flag import predict_invoice_flag


# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# LOGIN / SIGNUP PAGE
if not st.session_state.logged_in:

    menu = st.sidebar.selectbox(
        "Menu",
        ["Login", "Signup"]
    )

    if menu == "Signup":

        st.title("📝 Signup")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):

            if register_user(new_user, new_pass):
                st.success("Account Created Successfully")
            else:
                st.error("Username Already Exists")

    else:

        st.title("🔐 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            if login_user(username, password):
                st.session_state.logged_in = True
                st.rerun()

            else:
                st.error("Invalid Credentials")

    st.stop()

# -------------------------
# USER LOGGED IN HAI
# -------------------------

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------
st.set_page_config(
    page_title="Vendor Invoice Intelligence Portal",
    page_icon="📦",
    layout="wide"
)

# -------------------------------------------------------
# Header Section
# -------------------------------------------------------
st.markdown("""
# 📦 Vendor Invoice Intelligence Portal  
### AI-Driven Freight Cost Prediction & Invoice Risk Flagging

This internal analytics portal leverages machine learning to  
- **Forecast freight costs accurately**
- **Detect risky or abnormal vendor invoices**
- **Reduce financial leakage and manual workload**
""")

st.divider()

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------
st.sidebar.title("🔍 Model Selection")
selected_model = st.sidebar.radio(
    "Choose Prediction Module",
    [
        "Freight Cost Prediction",
        "Invoice Manual Approval Flag",
        "Analytics Dashboard",
        "PDF Invoice Upload"
    ]
)

st.sidebar.markdown("""
---
**Business Impact**
- 📉 Improved cost forecasting  
- 🧾 Reduced invoice fraud & anomalies  
- ⚙️ Faster finance operations
""")

# -------------------------------------------------------
# Freight Cost Prediction
# -------------------------------------------------------
if selected_model == "Freight Cost Prediction":
    st.subheader("🚚 Freight Cost Prediction")

    st.markdown("""
    **Objective:**  
    Predict freight cost for a vendor invoice using **Invoice Dollars**  
    to support budgeting, forecasting, and vendor negotiations.
    """)

    with st.form("freight_form"):
        col1, col2 = st.columns(2)

        with col1:
            dollars = st.number_input(
                "💰 Invoice Dollars",
                min_value=1.0,
                value=18500.0
            )

        with col2:
            quantity = st.number_input(
                "💰 Quantity",
                min_value=1,
                value=1200
            )
        submit_freight = st.form_submit_button("🔮 Predict Freight Cost")

    if submit_freight:
        input_data = {
            "Quantity": [quantity],
            "Dollars": [dollars]
        }

        prediction = predict_freight_cost(input_data)['Predicted_Freight']

        st.success("Prediction completed successfully.")

        st.metric(
            label="📊 Estimated Freight Cost",
            value=f"${prediction[0]:,.2f}"
        )



# -------------------------------------------------------
# Invoice Flag Prediction
# -------------------------------------------------------
elif selected_model == "Invoice Manual Approval Flag":
    st.subheader("🚨 Invoice Manual Approval Prediction")

    st.markdown("""
    **Objective:**  
    Predict whether a vendor invoice should be **flagged for manual approval**  
    based on abnormal cost, freight, or delivery patterns.
    """)

    with st.form("invoice_flag_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            invoice_quantity = st.number_input(
                "Invoice Quantity",
                min_value=1,
                value=50
            )
            freight = st.number_input(
                "Freight Cost",
                min_value=0.0,
                value=1.73
            )

        with col2:
            invoice_dollars = st.number_input(
                "Invoice Dollars",
                min_value=1.0,
                value=352.95
            )
            total_item_quantity = st.number_input(
                "Total Item Quantity",
                min_value=1,
                value=162
            )

        with col3:
            total_item_dollars = st.number_input(
                "Total Item Dollars",
                min_value=1.0,
                value=2476.0
            )

        submit_flag = st.form_submit_button("🧠 Evaluate Invoice Risk")

    if submit_flag:
        input_data = {
            "invoice_quantity": [invoice_quantity],
            "invoice_dollars": [invoice_dollars],
            "freight_invoiced": [freight],
            "total_item_quantity": [total_item_quantity],
            "total_item_dollars": [total_item_dollars]
        }

        result = predict_invoice_flag(input_data)

        # -------------------------
        # Anomaly Detection
        # -------------------------

        train_data = pd.DataFrame({
            "invoice_quantity": [50, 60, 80, 100, 120],
            "invoice_dollars": [300, 450, 700, 1000, 1500],
            "freight_invoiced": [5, 10, 15, 20, 25],
            "total_item_quantity": [60, 70, 90, 120, 150],
            "total_item_dollars": [350, 500, 800, 1200, 1700]
       })

        anomaly_model = IsolationForest(
            contamination=0.1,
            random_state=42
       )

        anomaly_model.fit(train_data)

        anomaly_input = pd.DataFrame(input_data)

        anomaly_prediction = anomaly_model.predict(anomaly_input)[0]
        anomaly_score = anomaly_model.decision_function(anomaly_input)[0]

        flag_prediction = result["Predicted_flag"].iloc[0]

        is_flagged = bool(flag_prediction)

        if is_flagged:

            st.error("⚠️ Invoice requires MANUAL APPROVAL")

            st.subheader("🤖 Risk Explanation")

            reasons = []

            if abs(invoice_dollars - total_item_dollars) > 5:
                reasons.append("Invoice amount mismatch")

            if freight > 50:
                reasons.append("High freight cost")

            if len(reasons) == 0:
                reasons.append("Abnormal invoice pattern detected")

            for reason in reasons:
                st.write("•", reason)

        else:
            st.success("✅ Invoice is SAFE for Auto-Approval")

        # -------------------------
        # Anomaly Detection Result
        # -------------------------

        st.subheader("🛡️ Anomaly Detection")

        if anomaly_prediction == 1:
            st.success("✅ Normal Invoice")

        elif anomaly_score > -0.15:
            st.warning("⚠️ Suspicious Invoice")

        else:
            st.error("🚨 Highly Anomalous Invoice")

elif selected_model == "Analytics Dashboard":

    st.subheader("📊 Analytics Dashboard")

    import os
    import sqlite3

    conn = sqlite3.connect("data/inventory.db")

    vendor_df = pd.read_sql_query(
    "SELECT * FROM vendor_invoice LIMIT 5",
    conn
    )

    # Vendor Score Calculation

    vendor_score = (
    vendor_df.groupby("VendorName")
    .agg({
        "Dollars": "mean",
        "Freight": "mean"
    })
    .reset_index()
    )
    max_freight = vendor_score["Freight"].max()

    vendor_score["PerformanceScore"] = (100 -(vendor_score["Freight"] / max_freight) * 50
    )

    vendor_score["PerformanceScore"] = (
         vendor_score["PerformanceScore"]
        .clip(lower=50)
        .round(2)
)
    
    st.subheader("🏆 Vendor Performance Score")

    st.dataframe(
        vendor_score[
        ["VendorName", "PerformanceScore"]
    ].sort_values(
        by="PerformanceScore",
        ascending=False
       )
    )

    top_score = (
    vendor_score
    .sort_values(
        by="PerformanceScore",
        ascending=False
    )
    .head(10)
    )

    fig_score = px.bar(
       top_score,
       x="VendorName",
       y="PerformanceScore",
       title="Top Vendor Performance"
    )

    st.plotly_chart(
        fig_score,
        use_container_width=True
    )


   # KPI Cards

    total_invoices = len(vendor_df)

    approved = len(
      vendor_df[vendor_df["Approval"] == "Approved"]
    )

    flagged = len(
      vendor_df[vendor_df["Approval"] == "Flagged"]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Invoices", total_invoices)

    with col2:
        st.metric("Approved", approved)

    with col3:
        st.metric("Flagged", flagged)


   # Top Vendors by Spend

    top_vendors = (
    vendor_df.groupby("VendorName")["Dollars"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    )

    st.subheader("🏆 Top Vendors by Spend")

    fig1 = px.bar(
    x=top_vendors.index,
    y=top_vendors.values,
    labels={"x": "Vendor", "y": "Total Spend"}
    )

    st.plotly_chart(fig1, use_container_width=True)


# Freight Distribution

    freight_data = (
    vendor_df.groupby("VendorName")["Freight"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    )

    st.subheader("🚚 Freight Distribution")

    fig2 = px.bar(
    x=freight_data.index,
    y=freight_data.values,
    labels={"x": "Vendor", "y": "Freight"}
    )

    st.plotly_chart(fig2, use_container_width=True)


# Invoice Amount Distribution

    amount_dist = (
        vendor_df["Dollars"]
       .round(-1)
       .value_counts()
       .sort_index()
    )

    st.subheader("💰 Invoice Amount Distribution")

    fig3 = px.bar(
        x=amount_dist.index,
        y=amount_dist.values,
        labels={"x": "Invoice Amount", "y": "Count"}
    )

    st.plotly_chart(fig3, use_container_width=True)

    conn.close()


elif selected_model == "PDF Invoice Upload":

    st.subheader("📄 PDF Invoice Upload")

    uploaded_file = st.file_uploader(
        "Upload Invoice PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        reader = PdfReader(pdf_path)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text

        st.success("✅ PDF Uploaded Successfully")

        st.subheader("📑 Extracted Invoice Content")

        st.text_area(
            "Invoice Text",
            text,
            height=300
        )
        try:

            invoice_quantity = int(
                re.search(
                r"Invoice Quantity:\s*(\d+)",
                text
            ).group(1)
        )

            invoice_dollars = float(
                re.search(
                r"Invoice Dollars:\s*(\d+)",
                text
            ).group(1)
        )

            total_item_quantity = int(
                re.search(
                r"Total Item Quantity:\s*(\d+)",
                text
            ).group(1)
        )

            total_item_dollars = float(
                re.search(
                r"Total Item Dollars:\s*(\d+)",
                text
            ).group(1)
       )

            freight = float(
                re.search(
                r"Freight Invoiced:\s*(\d+)",
                text
            ).group(1)
            )

            st.subheader("📊 Extracted Values")

            st.metric("Invoice Quantity:", invoice_quantity)
            st.metric("Invoice Dollars:", invoice_dollars)
            st.metric("Total Item Quantity:", total_item_quantity)
            st.metric("Total Item Dollars:", total_item_dollars)
            st.metric("Freight:", freight)

            input_data = {
                "invoice_quantity": [invoice_quantity],
                "invoice_dollars": [invoice_dollars],
                "freight_invoiced": [freight],
                "total_item_quantity": [total_item_quantity],
                "total_item_dollars": [total_item_dollars]
         }

            result = predict_invoice_flag(input_data)

            flag = result["Predicted_flag"].iloc[0]

            st.subheader("🤖 AI Decision")

            if flag == 1:
                st.error("⚠️ Manual Approval Required")
            else:
                st.success("✅ Auto Approved")


        except Exception as e:
            st.error(f"Error: {e}")