import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# 1. إعدادات الصفحة والتصميم الفني (ألوان دافئة، بيج وعاجي)
st.set_page_config(page_title="Mümkün Portal", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #FDFBF7;} 
    h1, h2, h3 {color: #D4AF37;} 
    .stButton>button {background-color: #D4AF37; color: white; border: none;}
    .footer {text-align: center; color: #8C7B65; font-style: italic; margin-top: 50px;}
    </style>
    """, unsafe_allow_html=True)

# 2. إعداد قاعدة البيانات (لن تُمسح وتحتفظ بالبيانات)
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

st.title("Mümkün Business Portal ✨")

# 3. دالة حساب تكلفة الشحن الدولي بناءً على فئات الوزن (يمكنك تعديل الأرقام حسب شركة الشحن)
def calculate_international_shipping(weight):
    if weight <= 0.5:
        return 200  # فئة النصف كيلو
    elif weight <= 1.0:
        return 350  # فئة الكيلو
    elif weight <= 5.0:
        return 350 + ((weight - 1.0) * 150) # الكيلو بـ 350 وأي كيلو إضافي بـ 150
    else:
        return 950 + ((weight - 5.0) * 100) # شحنات ثقيلة

# 4. واجهة إدخال البيانات والتكاليف
st.header("📦 إضافة شحنة جديدة")
with st.form("new_order_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("معلومات المنتج والعميل")
        order_date = st.date_input("تاريخ الطلب", date.today())
        customer_name = st.text_input("اسم العميل")
        item_desc = st.text_input("وصف المنتج")
        category = st.selectbox("التصنيف", ["Fashion", "Skincare", "Other"])
        seller_website = st.text_input("الموقع/المورد (مثل Trendyol)")
        
    with col2:
        st.subheader("التكاليف في تركيا والوزن")
        weight_kg = st.number_input("الوزن بالكيلوجرام (KG)", min_value=0.1, step=0.1, value=0.5)
        price_try = st.number_input("سعر المنتج (TRY)", min_value=0.0, step=10.0)
        internal_turkey_try = st.number_input("توصيل داخلي بتركيا (TRY)", min_value=0.0, step=5.0)
        exchange_rate = st.number_input("سعر صرف الليرة مقابل الجنيه", min_value=0.1, step=0.05, value=1.45)
        
    with col3:
        st.subheader("التكاليف في مصر والبيع")
        cbe_fee_egp = st.number_input("عمولة تدبير العملة للبنك (EGP)", min_value=0.0, step=10.0)
        internal_egypt_egp = st.number_input("توصيل داخلي بمصر (EGP)", min_value=0.0, step=10.0, value=75.0)
        packaging_egp = st.number_input("تكلفة التغليف (EGP)", min_value=0.0, step=5.0, value=35.0)
        selling_price_egp = st.number_input("سعر البيع للعميل (EGP)", min_value=0.0, step=50.0)

    submit_button = st.form_submit_button("حساب التكلفة وحفظ العملية")

    if submit_button:
        # العمليات الحسابية
        shipping_to_egypt_egp = calculate_international_shipping(weight_kg)
        cost_in_try = price_try + internal_turkey_try
        converted_cost_egp = cost_in_try * exchange_rate
        total_cost_egp = converted_cost_egp + cbe_fee_egp + shipping_to_egypt_egp + internal_egypt_egp + packaging_egp
        profit_egp = selling_price_egp - total_cost_egp

        # حفظ البيانات في قاعدة البيانات
        c.execute('''
            INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (str(order_date), customer_name, item_desc, category, seller_website, weight_kg, 
              price_try, internal_turkey_try, exchange_rate, cbe_fee_egp, shipping_to_egypt_egp, 
              internal_egypt_egp, packaging_egp, total_cost_egp, selling_price_egp, profit_egp))
        conn.commit()
        
        st.success(f"تم حفظ الشحنة بنجاح! التكلفة الإجمالية: {total_cost_egp:,.2f} جنيه | صافي الربح: {profit_egp:,.2f} جنيه")

# 5. عرض قاعدة البيانات وإمكانية تحميلها كـ Excel
st.header("📊 قاعدة البيانات وسجل العمليات")
df = pd.read_sql_query("SELECT * FROM orders", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    # زر التحميل
    st.download_button(
        label="📥 تحميل قاعدة البيانات كملف Excel (CSV)",
        data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name='Mumkun_Full_Database.csv',
        mime='text/csv'
    )
else:
    st.info("قاعدة البيانات فارغة حالياً. ابدأ بإضافة شحنات جديدة!")

st.markdown('<div class="footer">Made possible with love.</div>', unsafe_allow_html=True)