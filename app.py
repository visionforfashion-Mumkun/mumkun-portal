import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date

# 1. Page settings and branding
st.set_page_config(page_title="Mümkün Portal", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #FDFBF7;} 
    h1, h2, h3 {color: #D4AF37;} 
    .stButton>button {background-color: #D4AF37; color: white; border: none;}
    .footer {text-align: center; color: #8C7B65; font-style: italic; margin-top: 50px;}
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #EBE4D3;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Database setup
conn = sqlite3.connect('mumkun_database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_date TEXT, customer_name TEXT, item_desc TEXT, category TEXT, seller_website TEXT,
        weight_kg REAL, price_try REAL, internal_turkey_try REAL, exchange_rate REAL,
        cbe_fee_egp REAL, shipping_to_egypt_egp REAL, internal_egypt_egp REAL, packaging_egp REAL,
        total_cost_egp REAL, selling_price_egp REAL, profit_egp REAL
    )
''')
conn.commit()

# --- NEW: Sidebar for Backup & Restore ---
with st.sidebar:
    st.header("🛠️ Database Management")
    st.write("Use this section to restore your data if the server goes to sleep.")
    
    uploaded_file = st.file_uploader("Upload Backup CSV", type=['csv'])
    if uploaded_file is not None:
        if st.button("Restore Database"):
            try:
                restore_df = pd.read_csv(uploaded_file)
                # Overwrite the empty database with the uploaded backup
                restore_df.to_sql('orders', conn, if_exists='replace', index=False)
                st.success("✅ Data restored! Please refresh the page.")
            except Exception as e:
                st.error("Error restoring data. Make sure it is the exact Mümkün backup file.")
# -----------------------------------------

st.title("Mümkün Business Portal ✨")

def calculate_international_shipping(weight):
    if weight <= 0.5:
        return 200
    elif weight <= 1.0:
        return 350
    elif weight <= 5.0:
        return 350 + ((weight - 1.0) * 150)
    else:
        return 950 + ((weight - 5.0) * 100)

with st.expander("📦 Add New Order", expanded=False):
    with st.form("new_order_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Product & Customer Info")
            order_date = st.date_input("Order Date", date.today())
            customer_name = st.text_input("Customer Name")
            item_desc = st.text_input("Item Description")
            category = st.selectbox("Category", ["Fashion", "Skincare", "Other"])
            seller_website = st.text_input("Website/Seller (e.g., Trendyol)")
            
        with col2:
            st.subheader("Turkey Costs & Weight")
            weight_kg = st.number_input("Weight (KG)", min_value=0.1, step=0.1, value=0.5)
            price_try = st.number_input("Item Price (TRY)", min_value=0.0, step=10.0)
            internal_turkey_try = st.number_input("Internal Delivery Turkey (TRY)", min_value=0.0, step=5.0)
            exchange_rate = st.number_input("Exchange Rate (TRY to EGP)", min_value=0.1, step=0.05, value=1.45)
            
        with col3:
            st.subheader("Egypt Costs & Sales")
            cbe_fee_egp = st.number_input("CBE Currency Fee (EGP)", min_value=0.0, step=10.0)
            internal_egypt_egp = st.number_input("Internal Delivery Egypt (EGP)", min_value=0.0, step=10.0, value=75.0)
            packaging_egp = st.number_input("Packaging Cost (EGP)", min_value=0.0, step=5.0, value=35.0)
            selling_price_egp = st.number_input("Selling Price to Customer (EGP)", min_value=0.0, step=50.0)

        submit_button = st.form_submit_button("Calculate & Save Order")

        if submit_button:
            shipping_to_egypt_egp = calculate_international_shipping(weight_kg)
            cost_in_try = price_try + internal_turkey_try
            converted_cost_egp = cost_in_try * exchange_rate
            total_cost_egp = converted_cost_egp + cbe_fee_egp + shipping_to_egypt_egp + internal_egypt_egp + packaging_egp
            profit_egp = selling_price_egp - total_cost_egp

            c.execute('''
                INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (str(order_date), customer_name, item_desc, category, seller_website, weight_kg, 
                  price_try, internal_turkey_try, exchange_rate, cbe_fee_egp, shipping_to_egypt_egp, 
                  internal_egypt_egp, packaging_egp, total_cost_egp, selling_price_egp, profit_egp))
            conn.commit()
            
            st.success(f"Order saved successfully! Total Cost: {total_cost_egp:,.2f} EGP | Net Profit: {profit_egp:,.2f} EGP")

df = pd.read_sql_query("SELECT * FROM orders", conn)

if not df.empty:
    st.header("📈 Financial Dashboard")
    
    total_revenue = df['selling_price_egp'].sum()
    total_cost = df['total_cost_egp'].sum()
    total_profit = df['profit_egp'].sum()
    margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"{total_revenue:,.0f} EGP")
    m2.metric("Total Costs", f"{total_cost:,.0f} EGP")
    m3.metric("Net Profit", f"{total_profit:,.0f} EGP")
    m4.metric("Profit Margin", f"{margin:.1f}%")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        profit_by_cat = df.groupby('category')['profit_egp'].sum().reset_index()
        fig_pie = px.pie(profit_by_cat, values='profit_egp', names='category', 
                         title='Profit Distribution by Category',
                         color_discrete_sequence=['#D4AF37', '#8C7B65', '#EBE4D3'])
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        financials_by_date = df.groupby('order_date')[['selling_price_egp', 'total_cost_egp']].sum().reset_index()
        financials_by_date.rename(columns={'selling_price_egp': 'Revenue', 'total_cost_egp': 'Cost'}, inplace=True)
        
        fig_bar = px.bar(financials_by_date, x='order_date', y=['Revenue', 'Cost'],
                         title='Revenue vs Cost Over Time',
                         barmode='group',
                         color_discrete_map={'Revenue': '#D4AF37', 'Cost': '#8C7B65'})
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              xaxis_title="Date", yaxis_title="Amount (EGP)")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    
    st.header("📊 Full Order History")
    st.dataframe(df, use_container_width=True)
    
    st.download_button(
        label="📥 Download Database as Excel (CSV)",
        data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name='Mumkun_Full_Database.csv',
        mime='text/csv'
    )
else:
    st.info("Database is currently empty. Add new orders, or open the sidebar menu to restore a backup!")

st.markdown('<div class="footer">Made possible with love.</div>', unsafe_allow_html=True)
