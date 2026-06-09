"""
S&P 500 전종목을 Wikipedia에서 pandas로 파싱하고
주요 미국 ETF 100개를 합쳐 data/us_stocks.json으로 저장합니다.
ETF는 항상 포함되며, S&P 500 파싱 실패 시에도 ETF만으로 저장합니다.
"""

import json
import os
import sys

import pandas as pd

# ── 주요 ETF 100개 (하드코딩) ──────────────────────────────────────
_ETF_LIST = [
    # Broad US Market
    {"t":"SPY","n":"SPDR S&P 500 ETF Trust","m":"ETF","s":"Broad Market"},
    {"t":"VOO","n":"Vanguard S&P 500 ETF","m":"ETF","s":"Broad Market"},
    {"t":"IVV","n":"iShares Core S&P 500 ETF","m":"ETF","s":"Broad Market"},
    {"t":"VTI","n":"Vanguard Total Stock Market ETF","m":"ETF","s":"Broad Market"},
    {"t":"QQQ","n":"Invesco QQQ Trust (Nasdaq-100)","m":"ETF","s":"Nasdaq-100"},
    {"t":"QQQM","n":"Invesco Nasdaq-100 ETF","m":"ETF","s":"Nasdaq-100"},
    {"t":"DIA","n":"SPDR Dow Jones Industrial Average ETF","m":"ETF","s":"Broad Market"},
    {"t":"IWM","n":"iShares Russell 2000 ETF","m":"ETF","s":"Small Cap"},
    {"t":"IJH","n":"iShares Core S&P Mid-Cap ETF","m":"ETF","s":"Mid Cap"},
    {"t":"VB","n":"Vanguard Small-Cap ETF","m":"ETF","s":"Small Cap"},
    # International
    {"t":"VEA","n":"Vanguard FTSE Developed Markets ETF","m":"ETF","s":"International"},
    {"t":"VWO","n":"Vanguard FTSE Emerging Markets ETF","m":"ETF","s":"Emerging Markets"},
    {"t":"EFA","n":"iShares MSCI EAFE ETF","m":"ETF","s":"International"},
    {"t":"EEM","n":"iShares MSCI Emerging Markets ETF","m":"ETF","s":"Emerging Markets"},
    {"t":"VXUS","n":"Vanguard Total International Stock ETF","m":"ETF","s":"International"},
    {"t":"IEFA","n":"iShares Core MSCI EAFE ETF","m":"ETF","s":"International"},
    {"t":"IEMG","n":"iShares Core MSCI Emerging Markets ETF","m":"ETF","s":"Emerging Markets"},
    {"t":"EWJ","n":"iShares MSCI Japan ETF","m":"ETF","s":"Japan"},
    {"t":"FXI","n":"iShares China Large-Cap ETF","m":"ETF","s":"China"},
    {"t":"INDA","n":"iShares MSCI India ETF","m":"ETF","s":"India"},
    {"t":"EWY","n":"iShares MSCI South Korea ETF","m":"ETF","s":"South Korea"},
    {"t":"VEU","n":"Vanguard FTSE All-World ex-US ETF","m":"ETF","s":"International"},
    # Sector (SPDR)
    {"t":"XLK","n":"Technology Select Sector SPDR Fund","m":"ETF","s":"Technology"},
    {"t":"XLF","n":"Financial Select Sector SPDR Fund","m":"ETF","s":"Financials"},
    {"t":"XLE","n":"Energy Select Sector SPDR Fund","m":"ETF","s":"Energy"},
    {"t":"XLV","n":"Health Care Select Sector SPDR Fund","m":"ETF","s":"Health Care"},
    {"t":"XLY","n":"Consumer Discretionary Select Sector SPDR Fund","m":"ETF","s":"Consumer Discretionary"},
    {"t":"XLI","n":"Industrial Select Sector SPDR Fund","m":"ETF","s":"Industrials"},
    {"t":"XLB","n":"Materials Select Sector SPDR Fund","m":"ETF","s":"Materials"},
    {"t":"XLP","n":"Consumer Staples Select Sector SPDR Fund","m":"ETF","s":"Consumer Staples"},
    {"t":"XLU","n":"Utilities Select Sector SPDR Fund","m":"ETF","s":"Utilities"},
    {"t":"XLRE","n":"Real Estate Select Sector SPDR Fund","m":"ETF","s":"Real Estate"},
    {"t":"XLC","n":"Communication Services Select Sector SPDR Fund","m":"ETF","s":"Communication Services"},
    # Bonds
    {"t":"AGG","n":"iShares Core U.S. Aggregate Bond ETF","m":"ETF","s":"Bond"},
    {"t":"BND","n":"Vanguard Total Bond Market ETF","m":"ETF","s":"Bond"},
    {"t":"TLT","n":"iShares 20+ Year Treasury Bond ETF","m":"ETF","s":"Bond"},
    {"t":"IEF","n":"iShares 7-10 Year Treasury Bond ETF","m":"ETF","s":"Bond"},
    {"t":"SHY","n":"iShares 1-3 Year Treasury Bond ETF","m":"ETF","s":"Bond"},
    {"t":"LQD","n":"iShares iBoxx $ Inv. Grade Corporate Bond ETF","m":"ETF","s":"Bond"},
    {"t":"HYG","n":"iShares iBoxx $ High Yield Corporate Bond ETF","m":"ETF","s":"Bond"},
    {"t":"JNK","n":"SPDR Bloomberg High Yield Bond ETF","m":"ETF","s":"Bond"},
    {"t":"BNDX","n":"Vanguard Total International Bond ETF","m":"ETF","s":"Bond"},
    {"t":"TIP","n":"iShares TIPS Bond ETF","m":"ETF","s":"Inflation-Protected"},
    {"t":"VCSH","n":"Vanguard Short-Term Corporate Bond ETF","m":"ETF","s":"Bond"},
    {"t":"VGLT","n":"Vanguard Long-Term Treasury ETF","m":"ETF","s":"Bond"},
    {"t":"SHV","n":"iShares Short Treasury Bond ETF","m":"ETF","s":"Bond"},
    # Dividend
    {"t":"VYM","n":"Vanguard High Dividend Yield ETF","m":"ETF","s":"Dividend"},
    {"t":"SCHD","n":"Schwab U.S. Dividend Equity ETF","m":"ETF","s":"Dividend"},
    {"t":"DVY","n":"iShares Select Dividend ETF","m":"ETF","s":"Dividend"},
    {"t":"HDV","n":"iShares Core High Dividend ETF","m":"ETF","s":"Dividend"},
    {"t":"DGRO","n":"iShares Core Dividend Growth ETF","m":"ETF","s":"Dividend"},
    {"t":"VIG","n":"Vanguard Dividend Appreciation ETF","m":"ETF","s":"Dividend"},
    {"t":"DGRW","n":"WisdomTree U.S. Quality Dividend Growth ETF","m":"ETF","s":"Dividend"},
    # Factor / Smart Beta
    {"t":"VTV","n":"Vanguard Value ETF","m":"ETF","s":"Factor"},
    {"t":"VUG","n":"Vanguard Growth ETF","m":"ETF","s":"Factor"},
    {"t":"MTUM","n":"iShares MSCI USA Momentum Factor ETF","m":"ETF","s":"Factor"},
    {"t":"QUAL","n":"iShares MSCI USA Quality Factor ETF","m":"ETF","s":"Factor"},
    {"t":"VLUE","n":"iShares MSCI USA Value Factor ETF","m":"ETF","s":"Factor"},
    {"t":"USMV","n":"iShares MSCI USA Min Vol Factor ETF","m":"ETF","s":"Factor"},
    {"t":"IWF","n":"iShares Russell 1000 Growth ETF","m":"ETF","s":"Factor"},
    # Technology / Semiconductors
    {"t":"SOXX","n":"iShares Semiconductor ETF","m":"ETF","s":"Semiconductor"},
    {"t":"SMH","n":"VanEck Semiconductor ETF","m":"ETF","s":"Semiconductor"},
    {"t":"VGT","n":"Vanguard Information Technology ETF","m":"ETF","s":"Technology"},
    {"t":"IGV","n":"iShares Expanded Tech-Software Sector ETF","m":"ETF","s":"Technology"},
    {"t":"FTEC","n":"Fidelity MSCI Information Technology ETF","m":"ETF","s":"Technology"},
    {"t":"CIBR","n":"First Trust NASDAQ Cybersecurity ETF","m":"ETF","s":"Technology"},
    {"t":"BUG","n":"Global X Cybersecurity ETF","m":"ETF","s":"Technology"},
    # Thematic / Innovation
    {"t":"ARKK","n":"ARK Innovation ETF","m":"ETF","s":"Innovation"},
    {"t":"ARKG","n":"ARK Genomic Revolution ETF","m":"ETF","s":"Genomics"},
    {"t":"ARKW","n":"ARK Next Generation Internet ETF","m":"ETF","s":"Innovation"},
    {"t":"ARKF","n":"ARK Fintech Innovation ETF","m":"ETF","s":"Fintech"},
    {"t":"BOTZ","n":"Global X Robotics & Artificial Intelligence ETF","m":"ETF","s":"AI/Robotics"},
    {"t":"ROBO","n":"ROBO Global Robotics and Automation ETF","m":"ETF","s":"AI/Robotics"},
    {"t":"ICLN","n":"iShares Global Clean Energy ETF","m":"ETF","s":"Clean Energy"},
    {"t":"TAN","n":"Invesco Solar ETF","m":"ETF","s":"Clean Energy"},
    {"t":"LIT","n":"Global X Lithium & Battery Tech ETF","m":"ETF","s":"Battery"},
    # Real Estate
    {"t":"VNQ","n":"Vanguard Real Estate ETF","m":"ETF","s":"Real Estate"},
    {"t":"IYR","n":"iShares U.S. Real Estate ETF","m":"ETF","s":"Real Estate"},
    {"t":"SCHH","n":"Schwab U.S. REIT ETF","m":"ETF","s":"Real Estate"},
    {"t":"REM","n":"iShares Mortgage Real Estate ETF","m":"ETF","s":"Real Estate"},
    # Commodities
    {"t":"GLD","n":"SPDR Gold Shares","m":"ETF","s":"Gold"},
    {"t":"IAU","n":"iShares Gold Trust","m":"ETF","s":"Gold"},
    {"t":"GDX","n":"VanEck Gold Miners ETF","m":"ETF","s":"Gold Miners"},
    {"t":"GDXJ","n":"VanEck Junior Gold Miners ETF","m":"ETF","s":"Gold Miners"},
    {"t":"SLV","n":"iShares Silver Trust","m":"ETF","s":"Silver"},
    {"t":"USO","n":"United States Oil Fund","m":"ETF","s":"Oil"},
    {"t":"UNG","n":"United States Natural Gas Fund","m":"ETF","s":"Natural Gas"},
    {"t":"DBC","n":"Invesco DB Commodity Index Tracking Fund","m":"ETF","s":"Commodity"},
    {"t":"PDBC","n":"Invesco Optimum Yield Diversified Commodity Strategy ETF","m":"ETF","s":"Commodity"},
    {"t":"CPER","n":"United States Copper Index Fund","m":"ETF","s":"Copper"},
    # Leveraged
    {"t":"TQQQ","n":"ProShares UltraPro QQQ (3x)","m":"ETF","s":"Leveraged"},
    {"t":"SOXL","n":"Direxion Daily Semiconductor Bull 3X Shares","m":"ETF","s":"Leveraged"},
    {"t":"SPXL","n":"Direxion Daily S&P 500 Bull 3X Shares","m":"ETF","s":"Leveraged"},
    {"t":"UPRO","n":"ProShares UltraPro S&P500 (3x)","m":"ETF","s":"Leveraged"},
    {"t":"TNA","n":"Direxion Daily Small Cap Bull 3X Shares","m":"ETF","s":"Leveraged"},
    # Inverse
    {"t":"SQQQ","n":"ProShares UltraPro Short QQQ (-3x)","m":"ETF","s":"Inverse"},
    {"t":"SOXS","n":"Direxion Daily Semiconductor Bear 3X Shares","m":"ETF","s":"Inverse"},
    {"t":"SPXS","n":"Direxion Daily S&P 500 Bear 3X Shares","m":"ETF","s":"Inverse"},
    {"t":"SH","n":"ProShares Short S&P500","m":"ETF","s":"Inverse"},
    {"t":"PSQ","n":"ProShares Short QQQ","m":"ETF","s":"Inverse"},
]


def _fetch_sp500() -> list:
    """Wikipedia에서 S&P 500 전종목 파싱."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url, flavor="lxml")
    df = tables[0]
    result = []
    for _, row in df.iterrows():
        ticker = str(row.get("Symbol", "") or "").strip()
        name   = str(row.get("Security", "") or "").strip()
        sector = str(row.get("GICS Sector", "") or "").strip() or "기타"
        if ticker and name:
            result.append({"t": ticker, "n": name, "m": "S&P500", "s": sector})
    return result


def main():
    result = list(_ETF_LIST)
    print(f"[ETF] {len(result)} ETFs (hardcoded)")

    try:
        sp500 = _fetch_sp500()
        print(f"[S&P500] {len(sp500)} stocks")
        result.extend(sp500)
    except Exception as exc:
        print(f"[S&P500] ERROR: {exc} — ETF 목록만 저장합니다", file=sys.stderr)

    out_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "us_stocks.json")
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Saved {len(result)} records → {out_path}")


if __name__ == "__main__":
    main()
