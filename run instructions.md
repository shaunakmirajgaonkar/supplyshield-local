# Run Instructions

## macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 self_test.py
python3 -m streamlit run app.py --server.port 8505
```

Open `http://localhost:8505` in a browser.

## Windows

```powershell
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python self_test.py
python -m streamlit run app.py --server.port 8505
```

The application uses only local SQLite storage and local processing. Do not commit generated `.db` files or confidential data.
