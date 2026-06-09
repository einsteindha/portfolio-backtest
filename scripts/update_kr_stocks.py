"""
KRX 전종목 리스트를 pykrx로 수집해 data/kr_stocks.json을 갱신한다.
GitHub Actions에서 매주 실행.
"""
import json
import os
import sys
from datetime import datetime, timedelta

def recent_trading_date():
    d = datetime.now()
    for _ in range(10):
        if d.weekday() < 5:
            return d.strftime('%Y%m%d')
        d -= timedelta(days=1)
    return datetime.now().strftime('%Y%m%d')

ETF_SECTOR_RULES = [
    ('레버리지', '레버리지'), ('인버스', '인버스'),
    ('미국S&P', '해외주식'), ('미국나스닥', '해외주식'), ('미국채', '채권'),
    ('국고채', '채권'), ('국채', '채권'), ('회사채', '채권'),
    ('CD금리', '단기채'), ('KOFR', '단기채'), ('머니마켓', '단기채'),
    ('골드', '원자재'), ('WTI', '원자재'), ('원유', '원자재'), ('금선물', '원자재'),
    ('리츠', '리츠'), ('REIT', '리츠'),
    ('배당', '배당'),
    ('코스피200', '국내주식'), ('KOSPI200', '국내주식'), ('코스닥150', '국내주식'),
    ('KODEX 200', '국내주식'), ('TIGER 200', '국내주식'), ('KBSTAR 200', '국내주식'),
    ('반도체', '섹터'), ('은행', '섹터'), ('자동차', '섹터'), ('바이오', '섹터'),
    ('헬스케어', '섹터'), ('에너지', '섹터'), ('철강', '섹터'), ('IT', '섹터'),
    ('미디어', '섹터'),
    ('차이나', '해외주식'), ('일본', '해외주식'), ('인도', '해외주식'),
    ('유로', '해외주식'), ('신흥국', '해외주식'), ('선진국', '해외주식'),
    ('MSCI', '해외주식'),
]

def etf_sector(name: str) -> str:
    for keyword, sector in ETF_SECTOR_RULES:
        if keyword in name:
            return sector
    return 'ETF'

def main():
    try:
        from pykrx import stock
    except ImportError:
        print('ERROR: pykrx not installed. Run: pip install pykrx', file=sys.stderr)
        sys.exit(1)

    date = recent_trading_date()
    print(f'Fetching KRX data for date: {date}')

    result = []
    seen = set()

    # KOSPI / KOSDAQ
    for market in ('KOSPI', 'KOSDAQ'):
        try:
            sector_df = stock.get_market_sector_classifications(date, market=market)
        except Exception as e:
            print(f'[{market}] sector fetch failed: {e}')
            sector_df = None

        try:
            tickers = stock.get_market_ticker_list(date, market=market)
        except Exception as e:
            print(f'[{market}] ticker list failed: {e}')
            continue

        for ticker in tickers:
            if ticker in seen:
                continue
            seen.add(ticker)
            try:
                name = stock.get_market_ticker_name(ticker)
            except Exception:
                name = ticker

            sector = '기타'
            if sector_df is not None and ticker in sector_df.index:
                try:
                    row = sector_df.loc[ticker]
                    sector = str(row['업종명']) if '업종명' in sector_df.columns else '기타'
                except Exception:
                    pass

            result.append({'t': f'{ticker}.KS', 'n': name, 'm': market, 's': sector})

        print(f'[{market}] {len([x for x in result if x["m"]==market])} stocks')

    # ETF
    try:
        etf_tickers = stock.get_etf_ticker_list(date)
        for ticker in etf_tickers:
            if ticker in seen:
                continue
            seen.add(ticker)
            try:
                name = stock.get_market_ticker_name(ticker)
            except Exception:
                name = ticker
            result.append({'t': f'{ticker}.KS', 'n': name, 'm': 'ETF', 's': etf_sector(name)})
        print(f'[ETF] {len([x for x in result if x["m"]=="ETF"])} ETFs')
    except Exception as e:
        print(f'[ETF] fetch failed: {e}')

    if not result:
        print('ERROR: No data fetched. Aborting to preserve existing file.', file=sys.stderr)
        sys.exit(1)

    out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'kr_stocks.json')
    out_path = os.path.normpath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

    print(f'Saved {len(result)} stocks to {out_path}')

if __name__ == '__main__':
    main()
