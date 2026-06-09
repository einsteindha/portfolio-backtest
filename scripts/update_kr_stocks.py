"""
FinanceDataReader로 KOSPI·KOSDAQ·ETF(KR) 전종목을 수집해
data/kr_stocks.json을 갱신합니다.
"""

import json
import os
import sys

import FinanceDataReader as fdr


_ETF_RULES = [
    ('레버리지', '레버리지'), ('인버스', '인버스'),
    ('미국S&P', '해외주식'), ('미국나스닥', '해외주식'), ('미국채', '채권'),
    ('국고채', '채권'), ('국채', '채권'), ('회사채', '채권'),
    ('CD금리', '단기채'), ('KOFR', '단기채'),
    ('골드', '원자재'), ('WTI', '원자재'), ('원유', '원자재'),
    ('리츠', '리츠'), ('REIT', '리츠'),
    ('배당', '배당'),
    ('코스피200', '국내주식'), ('코스닥150', '국내주식'),
    ('KODEX 200', '국내주식'), ('TIGER 200', '국내주식'), ('KBSTAR 200', '국내주식'),
    ('반도체', '섹터'), ('은행', '섹터'), ('자동차', '섹터'),
    ('바이오', '섹터'), ('헬스케어', '섹터'), ('철강', '섹터'), ('IT', '섹터'),
    ('차이나', '해외주식'), ('일본', '해외주식'), ('인도', '해외주식'),
    ('유로', '해외주식'), ('신흥국', '해외주식'), ('선진국', '해외주식'),
    ('MSCI', '해외주식'),
]


def _etf_sector(name: str) -> str:
    for kw, sec in _ETF_RULES:
        if kw in name:
            return sec
    return 'ETF'


def _str(val) -> str:
    s = str(val).strip()
    return '' if s in ('', 'nan', 'None') else s


def _collect_market(market: str) -> list:
    df = fdr.StockListing(market)
    out = []
    for _, row in df.iterrows():
        ticker = _str(row.get('Symbol') or row.get('Code') or '')
        name   = _str(row.get('Name') or '')
        sector = _str(row.get('Sector') or row.get('Industry') or '') or '기타'
        if ticker and name:
            out.append({'t': f'{ticker}.KS', 'n': name, 'm': market, 's': sector})
    return out


def _collect_etf() -> list:
    df = fdr.StockListing('ETF/KR')
    out = []
    for _, row in df.iterrows():
        ticker = _str(row.get('Symbol') or row.get('Code') or '')
        name   = _str(row.get('Name') or '')
        if ticker and name:
            out.append({'t': f'{ticker}.KS', 'n': name, 'm': 'ETF', 's': _etf_sector(name)})
    return out


def main():
    result = []

    for market in ('KOSPI', 'KOSDAQ'):
        try:
            stocks = _collect_market(market)
            print(f'[{market}] {len(stocks)} stocks')
            result.extend(stocks)
        except Exception as exc:
            print(f'[{market}] ERROR: {exc}', file=sys.stderr)

    try:
        etfs = _collect_etf()
        print(f'[ETF/KR] {len(etfs)} ETFs')
        result.extend(etfs)
    except Exception as exc:
        print(f'[ETF/KR] ERROR: {exc}', file=sys.stderr)

    if not result:
        print('No data fetched — aborting to preserve existing file.', file=sys.stderr)
        sys.exit(1)

    out_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'kr_stocks.json')
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
    print(f'Saved {len(result)} records → {out_path}')


if __name__ == '__main__':
    main()
