import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import io

# 1. Page settings and Elegant Pink MÜMKÜN Branding
st.set_page_config(page_title="Mümkün Portal", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Tajawal:wght@300;400;500&display=swap');
    
    /* Overall Background and Text */
    .stApp {
        background-color: #FFF0F5; /* Soft pale pink / lavender blush */
        color: #5C4A4A; /* Soft brown/dark rose */
        font-family: 'Tajawal', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Cormorant Garamond', serif !important;
        color: #D1889B !important; /* Soft Rose/Pink */
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #F8E4E8; /* Soft blush pink */
        color: #5C4A4A;
        border: 1px solid #D1889B; /* Rose border */
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #D1889B; /* Rose on hover */
        color: #FFFFFF;
        border-color: #B97083;
    }
    
    /* Input Fields */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #FFFFFF;
        border-radius: 6px;
        border: 1px solid #F0D9DE;
    }
    
    /* Footer */
    .footer {
        text-align: center; 
        color: #D1889B; 
        font-style: italic; 
        font-family: 'Cormorant Garamond', serif;
        margin-top: 50px;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Database setup (v5 with Safe Migration for Bank Fees)
DB_FILE = 'mumkun_v5.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, supplier TEXT, weight_kg REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_date TEXT, product_id INTEGER, 
    qty INTEGER, currency TEXT, unit_price_foreign REAL, extra_costs_foreign REAL, exchange_rate REAL, 
    shipping_per_kg_egp REAL, total_weight_kg REAL, weight_cost_egp REAL, bank_fees_egp REAL, total_cost_egp REAL, unit_cost_egp REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT, sale_date TEXT, product_id INTEGER, customer_id INTEGER, 
    qty INTEGER, unit_selling_price_egp REAL, delivery_cost_egp REAL, cogs_egp REAL, profit_egp REAL)''')
conn.commit()

# SMART MIGRATION: Add the "bank_fees_egp" column to the database safely
try:
    c.execute("ALTER TABLE purchases ADD COLUMN bank_fees_egp REAL DEFAULT 0.0")
    conn.commit()
except sqlite3.OperationalError:
    pass

def get_products(): return pd.read_sql_query("SELECT * FROM products", conn)
def get_customers(): return pd.read_sql_query("SELECT * FROM customers", conn)

st.title("Mümkün Business Portal ✨")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛍️ Products", "👥 Customers", "🛒 Purchases", "💰 Sales", "📊 Dashboard"])

# --- TAB 1: PRODUCTS ---
with tab1:
    st.header("Add New Product")
    with st.form("product_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("Product Name").strip()
            p_category = st.selectbox("Category", ["Skincare", "Fashion", "Accessories", "Other"])
        with col2:
            p_supplier = st.text_input("Supplier (e.g., Trendyol, Zara, Shein)")
            p_weight = st.number_input("Weight per piece (KG)", min_value=0.01, step=0.05, value=0.20)
        
        if st.form_submit_button("Save Product"):
            if p_name:
                c.execute("SELECT id FROM products WHERE name = ?", (p_name,))
                if c.fetchone():
                    st.error(f"⚠️ A product named '{p_name}' already exists! ID was not duplicated.")
                else:
                    c.execute('INSERT INTO products (name, category, supplier, weight_kg) VALUES (?,?,?,?)', 
                              (p_name, p_category, p_supplier, p_weight))
                    conn.commit()
                    st.success(f"Product '{p_name}' added to database.")
            else:
                st.error("Please enter a product name.")
    
    st.subheader("Product Catalog")
    prod_df = get_products()
    st.dataframe(prod_df, use_container_width=True)

    if not prod_df.empty:
        with st.expander("✏️ Edit or Delete a Product"):
            edit_p_name = st.selectbox("Select Product to Edit", prod_df['name'])
            selected_p = prod_df[prod_df['name'] == edit_p_name].iloc[0]
            
            c1, c2 = st.columns(2)
            new_p_name = c1.text_input("Edit Name", selected_p['name'], key="ep_name")
            new_p_weight = c2.number_input("Edit Weight (KG)", value=float(selected_p['weight_kg']), key="ep_w")
            
            col_update, col_del = st.columns(2)
            if col_update.button("Update Product"):
                c.execute("UPDATE products SET name=?, weight_kg=? WHERE id=?", (new_p_name, new_p_weight, int(selected_p['id'])))
                conn.commit()
                st.success("Updated!")
                st.rerun()
            if col_del.button("❌ Delete Product"):
                c.execute("DELETE FROM products WHERE id=?", (int(selected_p['id']),))
                conn.commit()
                st.success("Deleted!")
                st.rerun()

# --- TAB 2: CUSTOMERS ---
with tab2:
    st.header("Add New Customer")
    with st.form("customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            c_name = st.text_input("Customer Name").strip()
        with col2:
            c_phone = st.text_input("Phone Number").strip()
            
        if st.form_submit_button("Save Customer"):
            if c_name:
                c.execute("SELECT id FROM customers WHERE name = ?", (c_name,))
                if c.fetchone():
                    st.error(f"⚠️ Customer '{c_name}' already exists!")
                else:
                    c.execute('INSERT INTO customers (name, phone) VALUES (?,?)', (c_name, c_phone))
                    conn.commit()
                    st.success(f"Customer '{c_name}' added to database.")
            else:
                st.error("Please enter a customer name.")
            
    st.subheader("Client List")
    cust_df = get_customers()
    st.dataframe(cust_df, use_container_width=True)

    if not cust_df.empty:
        with st.expander("✏️ Edit or Delete a Customer"):
            edit_c_name = st.selectbox("Select Customer to Edit", cust_df['name'])
            selected_c = cust_df[cust_df['name'] == edit_c_name].iloc[0]
            
            c1, c2 = st.columns(2)
            new_c_name = c1.text_input("Edit Name", selected_c['name'], key="ec_name")
            new_c_phone = c2.text_input("Edit Phone", selected_c['phone'], key="ec_phone")
            
            col_update, col_del = st.columns(2)
            if col_update.button("Update Customer"):
                c.execute("UPDATE customers SET name=?, phone=? WHERE id=?", (new_c_name, new_c_phone, int(selected_c['id'])))
                conn.commit()
                st.success("Updated!")
                st.rerun()
            if col_del.button("❌ Delete Customer"):
                c.execute("DELETE FROM customers WHERE id=?", (int(selected_c['id']),))
                conn.commit()
                st.success("Deleted!")
                st.rerun()

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
                currency = st.selectbox("Currency", ["TRY", "USD", "EUR", "AED", "SAR", "GBP", "EGP"])
                
            with col2:
                unit_price_foreign = st.number_input("Supplier Price per piece (in selected currency)", min_value=0.0, step=10.0)
                extra_costs_foreign = st.number_input("Extra Costs/Customs (in selected currency)", min_value=0.0, step=10.0)
                exchange_rate = st.number_input("Exchange Rate (to EGP)", min_value=0.1, step=0.05, value=1.45)
                
            with col3:
                shipping_per_kg_egp = st.number_input("Shipping Rate per KG (EGP)", min_value=0.0, step=10.0, value=250.0)
                bank_fees_egp = st.number_input("Bank Fees (EGP)", min_value=0.0, step=10.0, value=0.0)
                
            if st.form_submit_button("Calculate & Save Purchase"):
                prod_id = product_dict[selected_prod_name]
                unit_weight = prod_df.loc[prod_df['name'] == selected_prod_name, 'weight_kg'].values[0]
                
                total_weight_kg = unit_weight * qty
                weight_cost_egp = total_weight_kg * shipping_per_kg_egp 
                
                product_cost_foreign = unit_price_foreign * qty
                total_foreign = product_cost_foreign + extra_costs_foreign
                
                # Convert foreign currency to EGP, add Egypt shipping, add Bank Fees
                total_cost_egp = (total_foreign * exchange_rate) + weight_cost_egp + bank_fees_egp
                unit_cost_egp = total_cost_egp / qty
                
                c.execute('''INSERT INTO purchases 
                    (purchase_date, product_id, qty, currency, unit_price_foreign, extra_costs_foreign, exchange_rate, 
                    shipping_per_kg_egp, total_weight_kg, weight_cost_egp, bank_fees_egp, total_cost_egp, unit_cost_egp) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                    (str(purchase_date), prod_id, qty, currency, unit_price_foreign, extra_costs_foreign, exchange_rate,
                     shipping_per_kg_egp, total_weight_kg, weight_cost_egp, bank_fees_egp, total_cost_egp, unit_cost_egp))
                conn.commit()
                
                st.success(f"Purchase logged successfully for {purchase_date}!")
                st.info(f"📦 Overall Weight: {total_weight_kg:.2f} KG | 🚚 Cost of Weight: {weight_cost_egp:,.2f} EGP | 🏦 Bank Fees: {bank_fees_egp:,.2f} EGP | 💰 Total Cost: {total_cost_egp:,.2f} EGP")
                
    st.subheader("Purchase History")
    purchases_df = pd.read_sql_query("""
        SELECT p.id, p.purchase_date as 'Date', pr.name as 'Product', p.qty as 'Qty', 
               p.currency as 'Currency', p.unit_price_foreign as 'Price (Foreign)', 
               p.bank_fees_egp as 'Bank Fees (EGP)', p.weight_cost_egp as 'Weight Cost (EGP)', 
               p.total_cost_egp as 'Overall Cost (EGP)', p.unit_cost_egp as 'Unit Cost (EGP)'
        FROM purchases p JOIN products pr ON p.product_id = pr.id
    """, conn)
    st.dataframe(purchases_df.drop(columns=['id']), use_container_width=True)

    if not purchases_df.empty:
        with st.expander("✏️ Edit or Delete a Purchase"):
            edit_p_id = st.selectbox("Select Purchase ID to Edit/Delete", purchases_df['id'])
            selected_purch = pd.read_sql_query(f"SELECT * FROM purchases WHERE id={edit_p_id}", conn).iloc[0]
            
            st.write(f"Editing Purchase ID: {edit_p_id}")
            with st.form("edit_purchase_form"):
                e_qty = st.number_input("Edit Quantity", value=int(selected_purch['qty']), min_value=1)
                e_price = st.number_input("Edit Unit Price (Foreign)", value=float(selected_purch['unit_price_foreign']))
                e_extra = st.number_input("Edit Extra Costs (Foreign)", value=float(selected_purch['extra_costs_foreign']))
                e_rate = st.number_input("Edit Exchange Rate", value=float(selected_purch['exchange_rate']))
                e_ship = st.number_input("Edit Shipping Rate/KG (EGP)", value=float(selected_purch['shipping_per_kg_egp']))
                e_bank = st.number_input("Edit Bank Fees (EGP)", value=float(selected_purch['bank_fees_egp']))
                
                col_update, col_del = st.columns(2)
                if col_update.form_submit_button("Update Purchase"):
                    # Recalculate
                    unit_weight = prod_df.loc[prod_df['id'] == selected_purch['product_id'], 'weight_kg'].values[0]
                    t_weight = unit_weight * e_qty
                    w_cost = t_weight * e_ship
                    t_cost_egp = (((e_price * e_qty) + e_extra) * e_rate) + w_cost + e_bank
                    u_cost_egp = t_cost_egp / e_qty
                    
                    c.execute('''UPDATE purchases SET qty=?, unit_price_foreign=?, extra_costs_foreign=?, 
                                 exchange_rate=?, shipping_per_kg_egp=?, total_weight_kg=?, weight_cost_egp=?, 
                                 bank_fees_egp=?, total_cost_egp=?, unit_cost_egp=? WHERE id=?''',
                              (e_qty, e_price, e_extra, e_rate, e_ship, t_weight, w_cost, e_bank, t_cost_egp, u_cost_egp, int(edit_p_id)))
                    conn.commit()
                    st.success("Purchase Updated!")
                    st.rerun()
                    
                if col_del.form_submit_button("❌ Delete Purchase"):
                    c.execute("DELETE FROM purchases WHERE id=?", (int(edit_p_id),))
                    conn.commit()
                    st.success("Purchase deleted!")
                    st.rerun()

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
                    
                    st.success(f"Sale recorded for {sale_date}! Revenue: {revenue:,.2f} EGP | Net Profit: {profit_egp:,.2f} EGP")
                    
    st.subheader("Sales History")
    sales_df = pd.read_sql_query("""
        SELECT s.id, s.sale_date as 'Sale Date', c.name as 'Customer', p.name as 'Product', s.qty as 'Qty', 
               s.unit_selling_price_egp as 'Price (EGP)', s.delivery_cost_egp as 'Egypt Shipping (EGP)', 
               s.profit_egp as 'Net Profit (EGP)'
        FROM sales s 
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
    """, conn)
    st.dataframe(sales_df.drop(columns=['id']), use_container_width=True)

    if not sales_df.empty:
        with st.expander("✏️ Edit or Delete a Sale"):
            edit_s_id = st.selectbox("Select Sale ID to Edit/Delete", sales_df['id'])
            selected_sale = pd.read_sql_query(f"SELECT * FROM sales WHERE id={edit_s_id}", conn).iloc[0]
            
            with st.form("edit_sale_form"):
                e_s_qty = st.number_input("Edit Quantity Sold", value=int(selected_sale['qty']), min_value=1)
                e_s_price = st.number_input("Edit Selling Price (EGP)", value=float(selected_sale['unit_selling_price_egp']))
                e_s_deliv = st.number_input("Edit Courier Cost (EGP)", value=float(selected_sale['delivery_cost_egp']))
                
                col_update_s, col_del_s = st.columns(2)
                if col_update_s.form_submit_button("Update Sale"):
                    avg_cost_df = pd.read_sql_query(f"SELECT AVG(unit_cost_egp) as avg_cost FROM purchases WHERE product_id = {int(selected_sale['product_id'])}", conn)
                    avg_cost = avg_cost_df['avg_cost'].values[0]
                    cogs = avg_cost * e_s_qty
                    rev = e_s_price * e_s_qty
                    prof = rev - cogs - e_s_deliv
                    
                    c.execute('''UPDATE sales SET qty=?, unit_selling_price_egp=?, delivery_cost_egp=?, cogs_egp=?, profit_egp=? WHERE id=?''',
                              (e_s_qty, e_s_price, e_s_deliv, cogs, prof, int(edit_s_id)))
                    conn.commit()
                    st.success("Sale Updated!")
                    st.rerun()
                    
                if col_del_s.form_submit_button("❌ Delete Sale"):
                    c.execute("DELETE FROM sales WHERE id=?", (int(edit_s_id),))
                    conn.commit()
                    st.success("Sale deleted!")
                    st.rerun()

# --- TAB 5: DASHBOARD & BACKUP ---
with tab5:
    st.header("Business Overview")
    col1, col2 = st.columns(2)
    
    total_sales = pd.read_sql_query("SELECT SUM(qty * unit_selling_price_egp) as rev FROM sales", conn)['rev'].values[0] or 0
    total_profit = pd.read_sql_query("SELECT SUM(profit_egp) as prof FROM sales", conn)['prof'].values[0] or 0
    
    col1.metric("Total Revenue (EGP)", f"{total_sales:,.2f}")
    col2.metric("Total Net Profit (EGP)", f"{total_profit:,.2f}")
    
    st.divider()
    
    # SYSTEM BACKUP AND RESTORE SECTION
    st.header("💾 System Backup & Restore")
    st.write("Download your database file regularly to keep your Mümkün data perfectly safe.")
    
    b_col1, b_col2, b_col3 = st.columns(3)
    
    # Download Database DB File
    with b_col1:
        st.subheader("1. System Backup")
        with open(DB_FILE, "rb") as f:
            st.download_button(
                label="📥 Download System File (.db)",
                data=f,
                file_name=f"mumkun_backup_{date.today()}.db",
                mime="application/octet-stream"
            )
            
    # Download Excel Report
    with b_col2:
        st.subheader("2. Excel Report")
        
        # Gather all tables
        df_prod = pd.read_sql_query("SELECT * FROM products", conn)
        df_cust = pd.read_sql_query("SELECT * FROM customers", conn)
        df_purch = pd.read_sql_query("SELECT * FROM purchases", conn)
        df_sales = pd.read_sql_query("SELECT * FROM sales", conn)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_prod.to_excel(writer, index=False, sheet_name='Products')
            df_cust.to_excel(writer, index=False, sheet_name='Customers')
            df_purch.to_excel(writer, index=False, sheet_name='Purchases')
            df_sales.to_excel(writer, index=False, sheet_name='Sales')
            
        st.download_button(
            label="📊 Download Excel File (.xlsx)",
            data=output.getvalue(),
            file_name=f"Mumkun_Financial_Report_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
            
    # Upload Database Button
    with b_col3:
        st.subheader("3. Restore System Backup")
        uploaded_file = st.file_uploader("Upload your .db backup file", type=["db"])
        
        if uploaded_file is not None:
            if st.button("⚠️ Confirm Restore"):
                conn.close()
                with open(DB_FILE, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("System restored successfully! Refreshing...")
                st.rerun()

st.markdown('<div class="footer">Made possible with love.</div>', unsafe_allow_html=True)