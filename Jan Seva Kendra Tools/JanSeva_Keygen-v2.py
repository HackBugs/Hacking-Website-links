"""
License key generator for Jan Seva Pro  -  KEEP THIS FILE PRIVATE (do not give it to customers).
Usage:  python JanSeva_Keygen.py
Customer clicks 'Activate PRO' in the app, sends you their Machine ID, you send back the key.
"""
import hmac, hashlib

LICENSE_SECRET = "CHANGE-THIS-SECRET-BEFORE-SELLING"   # must be identical to JanSeva_Pro.py

def license_key(mid):
    d = hmac.new(LICENSE_SECRET.encode(), mid.strip().encode(), hashlib.sha256).hexdigest()[:16].upper()
    return "-".join(d[i:i + 4] for i in range(0, 16, 4))

if __name__ == "__main__":
    mid = input("Customer Machine ID: ")
    print("License key:", license_key(mid))
