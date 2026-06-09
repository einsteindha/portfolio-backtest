"""
KRX 데이터 포털 HTTP API로 KOSPI·KOSDAQ·ETF 전종목을 수집해
data/kr_stocks.json을 갱신합니다. 로그인 불필요.
"""

import json
import os
import sys
from datetime import datetime, timedelta

import requests

_BASE = 'https://data.krx.co.kr'
_SESSION = requests.Session()
_SESSION.headers.update({
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Referer': _BASE + '/',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
})


def _last_business_day() -> str:
    d = datetime.now()
    for _ in range(10):
        if d.weekday() < 5:
            return d.strftime('%Y%m%d')
        d -= timedelta(days=1)
    return datetime.now().strftime('%Y%m%d')


def _fetch(bld: str, extra: dict) -> list:
    """KRX getJsonData.cmd 호출 → 레코드 리스트 반환."""
    r = _SESSION.post(
        f'{_BASE}/comm/bldAttendant/getJsonData.cmd',
        data={'bld': bld, 'csvxls_isNo': 'false', **extra},
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    # KRX 응답의 데이터 키는 버전마다 다를 수 있으므로 방어적으로 탐색
    for key in ('OutBlock_1', 'output', 'block1'):
        if isinstance(body.get(key), list):
            return body[key]
    if isinstance(body, list):
        return body
    return []


def _get_market(date: str, mkt_id: str, mkt_name: str) -> list:
    """KOSPI(STK) 또는 KOSDAQ(KSQ) 전종목."""
    rows = _fetch('dbms/MDC/STAT/standard/MDCSTAT01901', {
        'mktId': mkt_id,
        'trdDd': date,
        'money': '1',
    })
    out = []
    for row in rows:
        ticker = (row.get('ISU_SRT_CD') or row.get('종목코드') or '').strip()
        name   = (row.get('ISU_ABBRV') or row.get('ISU_NM') or row.get('종목명') or '').strip()
        sector = (row.get('SECT_TP_NM') or row.get('업종명') or '기타').strip() or '기타'
        if ticker and name:
            out.append({'t': f'{ticker}.KS', 'n': name, 'm': mkt_name, 's': sector})
    return out


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


def _get_etfs(date: str) -> list:
    rows = _fetch('dbms/MDC/STAT/standard/MDCSTAT04601', {'trdDd': date})
    out = []
    for row in rows:
        ticker = (row.get('ISU_SRT_CD') or row.get('단축코드') or '').strip()
        name   = (row.get('ISU_ABBRV') or row.get('한글종목약명') or row.get('종목명') or '').strip()
        # API가 ETF_SECT_NM을 주면 그대로, 없으면 이름 기반 분류
        sector = (row.get('ETF_SECT_NM') or '').strip() or _etf_sector(name)
        if ticker and name:
            out.append({'t': f'{ticker}.KS', 'n': name, 'm': 'ETF', 's': sector})
    return out


def main():
    date = _last_business_day()
    print(f'KRX fetch date: {date}')

    result = []

    for mkt_id, mkt_name in (('STK', 'KOSPI'), ('KSQ', 'KOSDAQ')):
        try:
            stocks = _get_market(date, mkt_id, mkt_name)
            print(f'[{mkt_name}] {len(stocks)} stocks')
            result.extend(stocks)
        except Exception as exc:
            print(f'[{mkt_name}] ERROR: {exc}', file=sys.stderr)

    try:
        etfs = _get_etfs(date)
        print(f'[ETF] {len(etfs)} ETFs')
        result.extend(etfs)
    except Exception as exc:
        print(f'[ETF] ERROR: {exc}', file=sys.stderr)

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
