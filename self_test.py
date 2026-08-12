
from app import calculate_risk, risk_band, price_signal

def main():
    assert calculate_risk(0,0,0,0,0) == 0.0
    assert calculate_risk(100,100,100,100,100) == 100.0
    assert risk_band(80) == "Critical"
    assert risk_band(60) == "High"
    assert risk_band(40) == "Moderate"
    assert risk_band(20) == "Low"
    assert price_signal(100,100) == 0
    assert price_signal(50,100) > 0
    print("========================================")
    print(" SupplyShield Local - Self Test")
    print("========================================")
    print("PASS  Weighted risk scoring")
    print("PASS  Risk boundaries")
    print("PASS  Risk classification")
    print("PASS  Price anomaly signal")
    print("ALL TESTS PASSED")
    print("========================================")

if __name__ == "__main__":
    main()
