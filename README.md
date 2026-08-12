# SupplyShield Local

Local-first supply-chain counterfeit-risk screening using transparent pricing, shipment, seller, supplier and product-metadata signals.

## Features
- Product and supplier register
- 0–100 explainable counterfeit-risk screening score
- Low / Moderate / High / Critical classification
- Pricing anomaly analysis
- Shipment anomaly analysis
- Seller behavior/reliability signal
- Product metadata quality signal
- Supplier risk signal
- Factor-level explanations
- Batch CSV analysis
- Plotly analytics
- SQLite local storage
- Synthetic testing data
- No external APIs

## Safety boundary
SupplyShield is a screening and decision-support tool. A high score does not prove a product is counterfeit. Final decisions should use authorized inspections, documentation, serial/traceability checks and applicable organizational controls.

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 self_test.py
python3 -m streamlit run app.py --server.port 8505
```
