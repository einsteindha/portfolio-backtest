"""
NASDAQ 공식 FTP에서 미국 상장 전종목을 수집해 data/us_stocks.json을 갱신합니다.

출처:
  ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt  (NASDAQ)
  ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt   (NYSE 등)
"""

import json
import os
import re
import sys
import urllib.request


_FTP_NASDAQ = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt'
_FTP_OTHER  = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt'


def _fetch(url: str) -> list:
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode('utf-8', errors='replace').splitlines()


def _is_test_symbol(sym: str) -> bool:
    if '$' in sym:               return True  # warrants / rights
    if re.search(r'\d$', sym):   return True  # options / test issues
    if sym.isdigit():            return True
    return False


def _parse_nasdaq(lines: list) -> list:
    # Header: Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
    out = []
    for line in lines[1:]:
        if line.startswith('File Creation Time'):
            continue
        parts = line.split('|')
        if len(parts) < 7:
            continue
        sym, name, _, test_issue, _, _, etf_flag = parts[:7]
        sym = sym.strip()
        name = name.strip()
        if not sym or sym == 'Symbol':
            continue
        if test_issue.strip().upper() == 'Y':
            continue
        if _is_test_symbol(sym):
            continue
        m = 'ETF' if etf_flag.strip().upper() == 'Y' else 'stock'
        out.append({'t': sym, 'n': name, 'm': m, 's': ''})
    return out


def _parse_other(lines: list) -> list:
    # Header: ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
    out = []
    for line in lines[1:]:
        if line.startswith('File Creation Time'):
            continue
        parts = line.split('|')
        if len(parts) < 7:
            continue
        sym, name, _, _, etf_flag, _, test_issue = parts[:7]
        sym = sym.strip()
        name = name.strip()
        if not sym or sym == 'ACT Symbol':
            continue
        if test_issue.strip().upper() == 'Y':
            continue
        if _is_test_symbol(sym):
            continue
        m = 'ETF' if etf_flag.strip().upper() == 'Y' else 'stock'
        out.append({'t': sym, 'n': name, 'm': m, 's': ''})
    return out


def main():
    print('Fetching nasdaqlisted.txt ...')
    try:
        nasdaq_lines = _fetch(_FTP_NASDAQ)
    except Exception as e:
        print(f'ERROR fetching nasdaqlisted.txt: {e}', file=sys.stderr)
        sys.exit(1)

    print('Fetching otherlisted.txt ...')
    try:
        other_lines = _fetch(_FTP_OTHER)
    except Exception as e:
        print(f'ERROR fetching otherlisted.txt: {e}', file=sys.stderr)
        sys.exit(1)

    nasdaq_stocks = _parse_nasdaq(nasdaq_lines)
    other_stocks  = _parse_other(other_lines)

    # 중복 제거 — nasdaq 우선
    seen = set()
    result = []
    for s in nasdaq_stocks + other_stocks:
        if s['t'] not in seen:
            seen.add(s['t'])
            result.append(s)

    etf_cnt   = sum(1 for s in result if s['m'] == 'ETF')
    stock_cnt = sum(1 for s in result if s['m'] == 'stock')
    print(f'stock: {stock_cnt}  ETF: {etf_cnt}  total: {len(result)}')

    if not result:
        print('No data — aborting.', file=sys.stderr)
        sys.exit(1)

    out_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'us_stocks.json')
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
    print(f'Saved {len(result)} records -> {out_path}')


if __name__ == '__main__':
    main()
