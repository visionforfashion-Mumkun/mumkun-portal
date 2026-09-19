import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# 1. Page settings and branding
st.set_page_config(page_title="Mümkün Portal", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #FDFBF7;} 
    h1, h2, h3 {color: #D4AF37;} 
    .stButton>button {background-color: #D4AF37; color: white; border: none;}
    .footer {text-align: center; color: #8C7B65; font-style: italic; margin-top: 50px;}
    </style>
    """, unsafe_allow_html=True)

# 2. Database setup (Relational Structure)
# Using v3 to ensure the new columns load perfectly
conn = sqlite3.connect('mumkun_v3.db', check_same_thread=False)
c = conn.cursor()

# Create Tables
c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, supplier TEXT, weight_kg REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_date TEXT, product_id INTEGER, 
    qty INTEGER, unit_price_try REAL, shipping_per_kg_try REAL, total_weight_kg REAL, 
    weight_cost_try REAL, extra_costs_try REAL, exchange_rate REAL, total_cost_egp REAL, unit_cost_egp REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sale_date TEXT, product_id INTEGER, customer_id INTEGER, 
    qty INTEGER, unit_selling_price_egp REAL, delivery_cost_egp REAL, cogs_egp REAL, profit_egp REAL)''')
conn.commit()

# Helper Functions to fetch data for dropdowns
def get_products():
    return pd.read_sql_query("SELECT * FROM products", conn)

def get_customers():
    return pd.read_sql_query("SELECT * FROM customers", conn)

st.title("Mümkün Business Portal ✨")

# Create Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛍️ Products", "👥 Customers", "🛒 Purchases", "💰 Sales", "📊 Dashboard"])

# --- TAB 1: PRODUCTS ---
with tab1:
    st.header("Add New Product")
    with st.form("product_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Product Name")
            p_category = st.selectbox("Category", ["Skincare", "Fashion", "Accessories", "Other"])
        with col2:
            p_supplier = st.text_input("Supplier (e.g., Trendyol, Zara)")
            p_weight = st.number_input("Weight per piece (KG)", min_value=0.01, step=0.05, value=0.20)
        
        if st.form_submit_button("Save Product"):
            if p_name:
                c.execute('INSERT INTO products (name, category, supplier, weight_kg) VALUES (?,?,?,?)', 
                          (p_name, p_category, p_supplier, p_weight))
                conn.commit()
                st.success(f"Product '{p_name}' added to database.")
            else:
                st.error("Please enter a product name.")
    
    st.subheader("Product Catalog")
    st.dataframe(get_products(), use_container_width=True)

# --- TAB 2: CUSTOMERS ---
with tab2:
    st.header("Add New Customer")
    with st.form("customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            c_name = st.text_input("Customer Name")
        with col2:
            c_phone = st.text_input("Phone Number")
            
        if st.form_submit_button("Save Customer"):
            if c_name:
                c.execute('INSERT INTO customers (name, phone) VALUES (?,?)', (c_name, c_phone))
                conn.commit()
                st.success(f"Customer '{c_name}' added to database.")
            else:
                st.error("Please enter a customer name.")
            
    st.subheader("Client List")
    st.dataframe(get_customers(), use_container_width=True)

# --- TAB 3: PURCHASES ---
with tab3:
    st.header("Log a Purchase")
    prod_df = get_products()
    
    if prod_df.empty:
        st.warning("Please add a product in the 'Products' tab first.")
    else:
        with st.form("purchase_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                purchase_date = st.date_input("Purchase Date", date.today())
                product_dict = dict(zip(prod_df['name'], prod_df['id']))
                selected_prod_name = st.selectbox("Select Product", options=list(product_dict.keys()))
                qty = st.number_input("Quantity Purchased", min_value=1, step=1)
                
            with col2:
                unit_price_try = st.number_input("Supplier Price per piece (TRY)", min_value=0.0, step=10.0)
                shipping_per_kg_try = st.number_input("Shipping Rate per KG (TRY)", min_value=0.0, step=5.0, value=150.0)
                extra_costs_try = st.number_input("Extra Costs/Customs (TRY)", min_value=0.0, step=10.0)
                
            with col3:
                exchange_rate = st.number_input("Exchange Rate (TRY to EGP)", min_value=0.1, step=0.05, value=1.45)
                
            if st.form_submit_button("Calculate & Save Purchase"):
                prod_id = product_dict[selected_prod_name]
                unit_weight = prod_df.loc[prod_df['name'] == selected_prod_name, 'weight_kg'].values[0]
                
                # Math Logic
                total_weight_kg = unit_weight * qty
                weight_cost_try = total_weight_kg * shipping_per_kg_try
                product_cost_try = unit_price_try * qty
                total_try = product_cost_try + weight_cost_try + extra_costs_try
                
                total_cost_egp = total_try * exchange_rate
                unit_cost_egp = total_cost_egp / qty
                
                c.execute('''INSERT INTO purchases 
                    (purchase_date, product_id, qty, unit_price_try, shipping_per_kg_try, total_weight_kg, 
                    weight_cost_try, extra_costs_try, exchange_rate, total_cost_egp, unit_cost_egp) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)''', 
                    (str(purchase_date), prod_id, qty, unit_price_try, shipping_per_kg_try, total_weight_kg,
                     weight_cost_try, extra_costs_try, exchange_rate, total_cost_egp, unit_cost_egp))
                conn.commit()
                
                st.success(f"Purchase logged successfully for {purchase_date}!")
                st.info(f"📦 Overall Weight: {total_weight_kg:.2f} KG | 🚚 Cost of Weight: {weight_cost_try:,.2f} TRY | 💰 Overall Total Cost: {total_cost_egp:,.2f} EGP")
                
    st.subheader("Purchase History")
    purchases_df = pd.read_sql_query("""
        SELECT p.purchase_date as 'Purchase Date', pr.name as 'Product', p.qty as 'Qty', 
               p.total_weight_kg as 'Total Weight (KG)', p.weight_cost_try as 'Cost of Weight (TRY)', 
               p.total_cost_egp as 'Overall Cost (EGP)', p.unit_cost_egp as 'Unit Cost (EGP)'
        FROM purchases p JOIN products pr ON p.product_id = pr.id
    """, conn)
    st.dataframe(purchases_df, use_container_width=True)

# --- TAB 4: SALES ---
with tab4:
    st.header("Log a Sale")
    cust_df = get_customers()
    prod_df = get_products()
    
    if cust_df.empty or prod_df.empty:
        st.warning("Ensure you have at least one Product and one Customer registered.")
    else:
        with st.form("sale_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                sale_date = st.date_input("Sale Date", date.today())
                cust_dict = dict(zip(cust_df['name'], cust_df['id']))
                selected_cust = st.selectbox("Select Customer", options=list(cust_dict.keys()))
                
            with col2:
                prod_dict = dict(zip(prod_df['name'], prod_df['id']))
                selected_prod = st.selectbox("Select Product Sold", options=list(prod_dict.keys()))
                sale_qty = st.number_input("Quantity Sold", min_value=1, step=1)
                
            with col3:
                unit_selling_price_egp = st.number_input("Selling Price per piece (EGP)", min_value=0.0, step=50.0)
                delivery_cost_egp = st.number_input("Shipping in Egypt (Courier Cost EGP)", min_value=0.0, step=10.0)
                
            if st.form_submit_button("Calculate & Save Sale"):
                c_id = cust_dict[selected_cust]
                p_id = prod_dict[selected_prod]
                
                # Get average cost of this product to calculate profit
                avg_cost_df = pd.read_sql_query(f"SELECT AVG(unit_cost_egp) as avg_cost FROM purchases WHERE product_id = {p_id}", conn)
                avg_cost = avg_cost_df['avg_cost'].values[0]
                
                if pd.isna(avg_cost):
                    st.error("Cannot log a sale for a product that hasn't been purchased yet (Missing Cost Data).")
                else:
                    cogs_egp = avg_cost * sale_qty
                    revenue = unit_selling_price_egp * sale_qty
                    profit_egp = revenue - cogs_egp - delivery_cost_egp
                    
                    c.execute('''INSERT INTO sales 
                        (sale_date, product_id, customer_id, qty, unit_selling_price_egp, delivery_cost_egp, cogs_egp, profit_egp) 
                        VALUES (?,?,?,?,?,?,?,?)''', 
                        (str(sale_date), p_id, c_id, sale_qty, unit_selling_price_egp, delivery_cost_egp, cogs_egp, profit_egp))
                    conn.commit()
                    
                    st.success(f"Sale recorded for {sale_date}! Revenue: {revenue:,.2f} EGP | Cost of Goods: {cogs_egp:,.2f} EGP | Net Profit: {profit_egp:,.2f} EGP")
                    
    st.subheader("Sales History")
    sales_df = pd.read_sql_query("""
        SELECT s.sale_date as 'Sale Date', c.name as 'Customer', p.name as 'Product', s.qty as 'Qty', 
               s.unit_selling_price_egp as 'Price (EGP)', s.delivery_cost_egp as 'Egypt Shipping (EGP)', 
               s.profit_egp as 'Net Profit (EGP)'
        FROM sales s 
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
    """, conn)
    st.dataframe(sales_df, use_container_width=True)

# --- TAB 5: DASHBOARD ---
with tab5:
    st.header("Business Overview")
    col1, col2 = st.columns(2)
    
    total_sales = pd.read_sql_query("SELECT SUM(qty * unit_selling_price_egp) as rev FROM sales", conn)['rev'].values[0] or 0
    total_profit = pd.read_sql_query("SELECT SUM(profit_egp) as prof FROM sales", conn)['prof'].values[0] or 0
    
    col1.metric("Total Revenue (EGP)", f"{total_sales:,.2f}")
    col2.metric("Total Net Profit (EGP)", f"{total_profit:,.2f}")
    
    st.divider()
    
    st.subheader("Export Data")
    st.write("Download your complete database as an Excel-compatible CSV file.")
    
    # Download Full Purchases
    full_purchases = pd.read_sql_query("SELECT * FROM purchases", conn)
    st.download_button(
        label="📥 Download Purchases (CSV)",
        data=full_purchases.to_csv(index=False).encode('utf-8-sig'),
        file_name='Mumkun_Purchases.csv',
        mime='text/csv'
    )

st.markdown('<div class="footer">Made possible with love.</div>', unsafe_allow_html=True)
