# -*- coding: utf-8 -*-
import csv
import time
import requests

API_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bond-md/BondMarketInfoListEN"

BOND_TYPE_CODE = "100001"
ISSUE_YEAR = "2023"

OUT_CSV = "treasury_bond_2023.csv"
COLUMNS = ["ISIN", "Bond Code", "Issuer", "Bond Type", "Issue Date", "Latest Rating"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://www.chinamoney.com.cn",
    "Referer": "https://www.chinamoney.com.cn/english/bdInfo/",
}

def fetch_page(sess: requests.Session, page_no: int, page_size: int) -> list[dict]:
    payload = {
        "bondType": BOND_TYPE_CODE,
        "issueYear": ISSUE_YEAR,
        "pageNo": str(page_no),
        "pageSize": str(page_size),
    }
    r = sess.post(API_URL, data=payload, timeout=30)
    r.raise_for_status()
    data = (r.json() or {}).get("data", {}) or {}
    return data.get("resultList", []) or []

def main():
    page_size = 15  # 页个数
    sess = requests.Session()
    sess.trust_env = False
    sess.headers.update(HEADERS)

    rows = []
    page_no = 1

    while True:
        result_list = fetch_page(sess, page_no, page_size)


        if not result_list:
            break

        for item in result_list:
            rows.append({
                "ISIN": item.get("isin", "") or "",
                "Bond Code": item.get("bondCode", "") or "",
                "Issuer": item.get("entyFullName", "") or "",
                "Bond Type": "Treasury Bond",
                "Issue Date": item.get("issueStartDate", "") or "",
                "Latest Rating": item.get("debtRtng", "") or "",
            })

        print(f"page {page_no}: +{len(result_list)}")
        page_no += 1
        time.sleep(0.15)

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"✅ Saved: {OUT_CSV} | rows={len(rows)} | pages={page_no-1}")

if __name__ == "__main__":
    main()
