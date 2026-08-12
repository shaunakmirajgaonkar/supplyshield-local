import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "supplyshield.db"

st.set_page_config(page_title="SupplyShield Local", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.stApp { background:#f5f8fb; color:#172033; }
.block-container { max-width:1450px; padding-top:1.4rem; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e0e6ed; }
h1,h2,h3,h4,p,label,div,span { color:#172033; }
.card { background:#fff; border:1px solid #e0e6ed; border-radius:14px; padding:18px; margin-bottom:14px; }
.small { color:#607086 !important; font-size:.92rem; }
.badge { display:inline-block; padding:5px 10px; border-radius:999px; background:#edf4ff; color:#1856a8 !important; font-weight:600; }
</style>
""", unsafe_allow_html=True)

def conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE NOT NULL,
        product_name TEXT NOT NULL,
        category TEXT,
        supplier TEXT,
        seller TEXT,
        declared_price REAL,
        market_price REAL,
        shipment_id TEXT,
        shipment_date TEXT,
        origin TEXT,
        destination TEXT,
        seller_history REAL,
        metadata_quality REAL,
        created_at TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS assessments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        price_anomaly REAL,
        shipment_anomaly REAL,
        seller_anomaly REAL,
        metadata_anomaly REAL,
        supplier_anomaly REAL,
        risk_score REAL,
        risk_band TEXT,
        explanation TEXT,
        created_at TEXT NOT NULL
    )""")
    c.commit(); c.close()

def clamp(x):
    return max(0.0, min(100.0, float(x)))

def calculate_risk(price_anomaly, shipment_anomaly, seller_anomaly, metadata_anomaly, supplier_anomaly):
    # Transparent weights; higher signal = greater counterfeit-risk concern.
    score = (
        0.30 * clamp(price_anomaly)
        + 0.20 * clamp(shipment_anomaly)
        + 0.20 * clamp(seller_anomaly)
        + 0.15 * clamp(metadata_anomaly)
        + 0.15 * clamp(supplier_anomaly)
    )
    return round(clamp(score), 1)

def risk_band(score):
    if score >= 75: return "Critical"
    if score >= 55: return "High"
    if score >= 30: return "Moderate"
    return "Low"

def price_signal(declared, market):
    if market <= 0:
        return 0.0
    deviation = abs(declared - market) / market * 100
    # Very large deviations are capped rather than treated as proof of counterfeiting.
    return round(clamp(deviation * 1.5), 1)

def build_explanation(parts):
    names = {
        "price": "pricing anomaly",
        "shipment": "shipment anomaly",
        "seller": "seller-behavior signal",
        "metadata": "product-metadata signal",
        "supplier": "supplier signal",
    }
    active = [names[k] for k,v in parts.items() if v >= 55]
    if not active:
        return "No individual risk signal crossed the elevated-review threshold. Continue normal verification and supply-chain controls."
    return "Elevated review signals: " + ", ".join(active) + ". These are screening indicators, not proof that a product is counterfeit."

def assess_row(row):
    p = price_signal(float(row.declared_price), float(row.market_price))
    # Input scores are deliberately operational signals, not truth labels.
    shipment = clamp(float(row.shipment_anomaly))
    seller = clamp(100 - float(row.seller_history))
    metadata = clamp(100 - float(row.metadata_quality))
    supplier = clamp(float(row.supplier_anomaly))
    score = calculate_risk(p, shipment, seller, metadata, supplier)
    parts = {"price":p,"shipment":shipment,"seller":seller,"metadata":metadata,"supplier":supplier}
    return p, shipment, seller, metadata, supplier, score, risk_band(score), build_explanation(parts)

init_db()

with st.sidebar:
    st.markdown("## 🛡️ SupplyShield")
    st.caption("Local supply-chain counterfeit risk screening")
    page = st.radio("Workspace", [
        "Overview","Product Register","Risk Assessment",
        "Batch CSV Analysis","Analytics","Data Export"
    ])
    st.divider()
    st.markdown("### System status")
    st.success("ALL SYSTEMS LOCAL")
    st.caption("SQLite · Pandas · NumPy · Plotly")
    st.caption("No external APIs required.")

st.title("🛡️ SupplyShield Local")
st.caption("Supply-chain counterfeit-risk screening workspace using transparent operational signals.")
st.markdown('<span class="badge">LOCAL-FIRST SUPPLY-CHAIN INTELLIGENCE</span>', unsafe_allow_html=True)

if page == "Overview":
    c = conn()
    products = pd.read_sql_query("SELECT * FROM products", c)
    assessments = pd.read_sql_query("SELECT * FROM assessments", c)
    c.close()
    a,b,d,e = st.columns(4)
    a.metric("Products", len(products))
    b.metric("Assessments", len(assessments))
    d.metric("High / Critical", int((assessments.risk_score >= 55).sum()) if not assessments.empty else 0)
    e.metric("Average risk", f"{assessments.risk_score.mean():.1f}" if not assessments.empty else "—")
    st.info("A higher score means greater need for review under the entered assumptions. It does not establish that a product is counterfeit.")
    if assessments.empty:
        st.markdown('<div class="card"><b>No risk assessments yet.</b><br><span class="small">Register products and run an assessment to populate this workspace.</span></div>', unsafe_allow_html=True)
    else:
        view = assessments.merge(products[["id","product_code","product_name","supplier","seller"]], left_on="product_id", right_on="id")
        st.subheader("Recent risk assessments")
        st.dataframe(view[["product_code","product_name","supplier","seller","risk_score","risk_band","explanation"]], use_container_width=True, hide_index=True)

elif page == "Product Register":
    st.header("Product & Supply-Chain Register")
    with st.form("product_form"):
        code = st.text_input("Product code *")
        name = st.text_input("Product name *")
        category = st.text_input("Category")
        supplier = st.text_input("Supplier")
        seller = st.text_input("Seller")
        c1,c2 = st.columns(2)
        declared = c1.number_input("Declared price", min_value=0.0, value=100.0)
        market = c2.number_input("Reference market price", min_value=0.0, value=100.0)
        c3,c4 = st.columns(2)
        shipment = c3.text_input("Shipment ID")
        shipdate = c4.date_input("Shipment date")
        origin = st.text_input("Origin")
        destination = st.text_input("Destination")
        c5,c6 = st.columns(2)
        seller_history = c5.slider("Seller history / reliability",0,100,75)
        metadata_quality = c6.slider("Product metadata quality",0,100,85)
        if st.form_submit_button("Register product"):
            if not code.strip() or not name.strip():
                st.error("Product code and product name are required.")
            else:
                try:
                    c=conn()
                    c.execute("""INSERT INTO products
                    (product_code,product_name,category,supplier,seller,declared_price,market_price,shipment_id,shipment_date,origin,destination,seller_history,metadata_quality,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (code.strip(),name.strip(),category.strip(),supplier.strip(),seller.strip(),declared,market,shipment.strip(),str(shipdate),origin.strip(),destination.strip(),seller_history,metadata_quality,datetime.now().isoformat(timespec="seconds")))
                    c.commit(); c.close()
                    st.success("Product registered locally.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Product code already exists.")
    c=conn()
    df=pd.read_sql_query("SELECT * FROM products ORDER BY id DESC",c); c.close()
    st.subheader("Registered products")
    st.dataframe(df,use_container_width=True,hide_index=True)

elif page == "Risk Assessment":
    st.header("Counterfeit Risk Assessment")
    c=conn()
    products=pd.read_sql_query("SELECT id,product_code,product_name,supplier,seller,declared_price,market_price,seller_history,metadata_quality FROM products ORDER BY product_name",c)
    c.close()
    if products.empty:
        st.warning("Register a product first.")
    else:
        opts={f"{r.product_code} · {r.product_name}":int(r.id) for _,r in products.iterrows()}
        selected=st.selectbox("Product",list(opts))
        row=products[products.id==opts[selected]].iloc[0]
        st.write(f"**Supplier:** {row.supplier or 'Not provided'}  ·  **Seller:** {row.seller or 'Not provided'}")
        st.caption("Signals are entered or derived locally and should be corroborated with invoices, serial records, inspection evidence and authorized supply-chain controls.")
        c1,c2=st.columns(2)
        shipment=c1.slider("Shipment anomaly",0,100,20,5)
        supplier=c2.slider("Supplier anomaly",0,100,20,5)
        result=assess_row(type("R",(),{"declared_price":row.declared_price,"market_price":row.market_price,"shipment_anomaly":shipment,"seller_history":row.seller_history,"metadata_quality":row.metadata_quality,"supplier_anomaly":supplier})())
        p,sh,se,me,su,score,bandv,explanation=result
        m1,m2,m3=st.columns(3)
        m1.metric("Risk score",f"{score}/100")
        m2.metric("Risk band",bandv)
        m3.metric("Price anomaly",f"{p}")
        st.progress(score/100)
        st.markdown("### Factor signals")
        factors=pd.DataFrame({"Signal":["Pricing","Shipment","Seller","Metadata","Supplier"],"Score":[p,sh,se,me,su]})
        st.dataframe(factors,use_container_width=True,hide_index=True)
        st.info(explanation)
        if st.button("Save risk assessment",type="primary"):
            c=conn()
            c.execute("""INSERT INTO assessments(product_id,price_anomaly,shipment_anomaly,seller_anomaly,metadata_anomaly,supplier_anomaly,risk_score,risk_band,explanation,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",(opts[selected],p,sh,se,me,su,score,bandv,explanation,datetime.now().isoformat(timespec="seconds")))
            c.commit(); c.close()
            st.success("Assessment saved locally.")
            st.rerun()

elif page == "Batch CSV Analysis":
    st.header("Batch CSV Analysis")
    st.caption("Upload a synthetic or authorized CSV. Data is processed in memory locally and is not sent to an external API.")
    sample = pd.DataFrame([
        ["SKU-1001","Medical Device A","Supplier Alpha","Seller One",95,100,15,82,90,10],
        ["SKU-1002","Consumer Product B","Supplier Beta","Seller Two",35,100,60,48,55,70],
        ["SKU-1003","Component C","Supplier Gamma","Seller Three",98,100,10,92,95,5],
    ],columns=["product_code","product_name","supplier","seller","declared_price","market_price","shipment_anomaly","seller_history","metadata_quality","supplier_anomaly"])
    st.download_button("Download sample CSV",sample.to_csv(index=False).encode(), "supplyshield_sample.csv","text/csv")
    uploaded=st.file_uploader("Upload product-risk CSV",type=["csv"])
    if uploaded:
        try:
            df=pd.read_csv(uploaded)
            required={"product_code","product_name","supplier","seller","declared_price","market_price","shipment_anomaly","seller_history","metadata_quality","supplier_anomaly"}
            missing=required-set(df.columns)
            if missing:
                st.error("Missing columns: " + ", ".join(sorted(missing)))
            else:
                outputs=[]
                for _,r in df.iterrows():
                    res=assess_row(r)
                    outputs.append([*res])
                out=df.copy()
                out[["price_anomaly","shipment_signal","seller_signal","metadata_signal","supplier_signal","risk_score","risk_band","explanation"]]=pd.DataFrame(outputs,index=df.index)
                st.dataframe(out,use_container_width=True,hide_index=True)
                st.download_button("Download analyzed CSV",out.to_csv(index=False).encode(),"supplyshield_analyzed.csv","text/csv")
        except Exception as ex:
            st.error(f"Could not process CSV: {ex}")

elif page == "Analytics":
    st.header("Supply-Chain Risk Analytics")
    c=conn()
    a=pd.read_sql_query("SELECT * FROM assessments",c)
    p=pd.read_sql_query("SELECT * FROM products",c)
    c.close()
    if a.empty:
        st.info("Create assessments to populate analytics.")
    else:
        merged=a.merge(p[["id","product_name","supplier","seller"]],left_on="product_id",right_on="id")
        fig=px.bar(merged,x="product_name",y="risk_score",color="risk_band",hover_data=["supplier","seller"],title="Product counterfeit-risk screening scores")
        fig.update_layout(template="plotly_white",paper_bgcolor="white",plot_bgcolor="white",yaxis_range=[0,100])
        st.plotly_chart(fig,use_container_width=True)
        dist=a.risk_band.value_counts().reset_index()
        dist.columns=["risk_band","count"]
        fig2=px.pie(dist,names="risk_band",values="count",title="Risk-band distribution")
        fig2.update_layout(template="plotly_white",paper_bgcolor="white")
        st.plotly_chart(fig2,use_container_width=True)

elif page == "Data Export":
    st.header("Data Export")
    c=conn()
    for table in ["products","assessments"]:
        df=pd.read_sql_query(f"SELECT * FROM {table}",c)
        st.subheader(table.replace("_"," ").title())
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button(f"Download {table}.csv",df.to_csv(index=False).encode(),f"{table}.csv","text/csv")
    c.close()

st.divider()
st.caption("SupplyShield Local · Explainable screening and decision support · A risk signal is not proof of counterfeiting.")
