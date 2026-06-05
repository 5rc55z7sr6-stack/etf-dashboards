import json, time, sys, re
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd

# ── Ratio signal config ───────────────────────────────────────────────────────
CORE_R = [
    {"key":"XLY/XLP",   "num":"XLY",  "den":"XLP",  "master":True,  "inv":False},
    {"key":"HYG/LQD",   "num":"HYG",  "den":"LQD",  "master":True,  "inv":False},
    {"key":"SPY/TLT",   "num":"SPY",  "den":"TLT",  "master":True,  "inv":False},
    {"key":"CPER/GLD",  "num":"CPER", "den":"GLD",  "master":True,  "inv":False},
    {"key":"QQQ/SPY",   "num":"QQQ",  "den":"SPY",  "master":False, "inv":False},
    {"key":"SMH/SPY",   "num":"SMH",  "den":"SPY",  "master":False, "inv":False},
    {"key":"IWM/SPY",   "num":"IWM",  "den":"SPY",  "master":False, "inv":False},
    {"key":"RSP/SPY",   "num":"RSP",  "den":"SPY",  "master":False, "inv":False},
    {"key":"GLD/SPY",   "num":"GLD",  "den":"SPY",  "master":False, "inv":True },
    {"key":"IWF/IWD",   "num":"IWF",  "den":"IWD",  "master":False, "inv":False},
    {"key":"EEM/EFA",   "num":"EEM",  "den":"EFA",  "master":False, "inv":False},
    {"key":"IYT/XLU",   "num":"IYT",  "den":"XLU",  "master":False, "inv":False},
    {"key":"XLK/SHY",   "num":"XLK",  "den":"SHY",  "master":False, "inv":False},
    {"key":"IBIT/GLD",  "num":"IBIT", "den":"GLD",  "master":False, "inv":False},
    {"key":"XLK/XLU",   "num":"XLK",  "den":"XLU",  "master":False, "inv":False},
    {"key":"KRE/SPY",   "num":"KRE",  "den":"SPY",  "master":False, "inv":False},
    {"key":"SPHB/SPLV", "num":"SPHB", "den":"SPLV", "master":False, "inv":False},
    {"key":"HYG/TLT",   "num":"HYG",  "den":"TLT",  "master":False, "inv":False},
    {"key":"GLD/TLT",   "num":"GLD",  "den":"TLT",  "master":False, "inv":False},
    {"key":"SMH/IGV",   "num":"SMH",  "den":"IGV",  "master":False, "inv":False},
    {"key":"EWJ/SPY",   "num":"EWJ",  "den":"SPY",  "master":False, "inv":False},
    {"key":"COPX/GLD",  "num":"COPX", "den":"GLD",  "master":False, "inv":False},
    {"key":"SKYY/SPY",  "num":"SKYY", "den":"SPY",  "master":False, "inv":False},
    {"key":"XBI/SPY",   "num":"XBI",  "den":"SPY",  "master":False, "inv":False},
    {"key":"INDA/SPY",  "num":"INDA", "den":"SPY",  "master":False, "inv":False},
]
THEME_R = [
    {"key":"SMH/SPY",   "num":"SMH",  "den":"SPY",  "master":False, "inv":False, "theme":True},
    {"key":"ITA/SPY",   "num":"ITA",  "den":"SPY",  "master":False, "inv":False, "theme":True},
    {"key":"ARKK/SPY",  "num":"ARKK", "den":"SPY",  "master":False, "inv":False, "theme":True},
    {"key":"QTUM/SMH",  "num":"QTUM", "den":"SMH",  "master":False, "inv":False, "theme":True},
    {"key":"SOXX/SMH",  "num":"SOXX", "den":"SMH",  "master":False, "inv":False, "theme":True},
    {"key":"XBI/SPY",   "num":"XBI",  "den":"SPY",  "master":False, "inv":False, "theme":True},
    {"key":"INDA/SPY",  "num":"INDA", "den":"SPY",  "master":False, "inv":False, "theme":True},
    {"key":"PAVE/SPY",  "num":"PAVE", "den":"SPY",  "master":False, "inv":False, "theme":True},
    {"key":"MAGS/SPY",  "num":"MAGS", "den":"SPY",  "master":False, "inv":False, "theme":True},
]
ALL_R = CORE_R + THEME_R
SMA_S, SMA_L = 20, 50

# ── All 62 ETFs on the dashboard ──────────────────────────────────────────────
ETF_TICKERS = [
    'XLK','XLF','XLE','XLV','XLI','XLC','XLU','XLY','XLP','XLRE','XLB',
    'IXN','IXJ','IXC','IXG','MXI','KXI',
    'SPY','QQQ','IWM','RSP','TLT','LQD','HYG','GLD','IBIT','SMH',
    'EEM','EFA','SHY','IWF','IWD','IYT',
    'ITA','XAR','SHLD','NASA','UFO','ARKX','QTUM','AIQ','CHAT','BOTZ',
    'CIBR','URA','BLOK','ICLN','TAN','LIT','ARKG','ARKK',
    'SOXX','MAGS','PAVE','XBI','IBB','INDA','COPX','SKYY','FINX','REMX','TUR',
]

# ── Leveraged ETFs (trade ideas in popup) ─────────────────────────────────────
LEVERAGED_TICKERS = [
    'TECL','TQQQ','FAS','DPST','ERX','NRGU','CURE','LABU','DUSL','TPOR',
    'MIDU','TNA','URTY','SPXL','UPRO','UDOW','SOXL','USD','FNGU','DFEN',
    'WANT','AMZU','INDL','EDC','TMF','UBT','BIB','BITX','BITU',
    'NAIL','DRN','ROM','RETL','BULZ','HIBL','WEBL',
    'NUGT','DUST','UCO','GUSH','DRIP','JNUG','JDST',
]

# ── Hardcoded fallback holdings (used when Yahoo Finance returns no data) ──────
# These are the tickers stored in the JS HOLDINGS array — used as last resort
HARDCODED_HOLDINGS = {
    'XLK': ['AAPL','NVDA','MSFT','AVGO','META','AMD','CRM','ADBE','AMAT','QCOM','ORCL','CSCO','NOW','INTU','PANW','KLAC','LRCX','MU','MRVL','SNPS','CDNS','FTNT'],
    'XLF': ['BRK.B','JPM','V','MA','BAC','WFC','GS','MS','BLK','SPGI','CME','ICE','AXP','C','USB','PNC','TRV','COF','MET','AON'],
    'XLE': ['XOM','CVX','COP','EOG','SLB','MPC','VLO','PSX','OXY','HAL','BKR','DVN','HES','MRO','OKE','WMB','KMI','LNG'],
    'XLV': ['UNH','LLY','JNJ','ABBV','MRK','PFE','TMO','DHR','ABT','ISRG','ELV','CVS','AMGN','CI','BMY','MDT','BSX','SYK','BDX','GEHC','ZTS','VRTX'],
    'XLI': ['GEV','RTX','CAT','HON','DE','LMT','PH','NOC','ETN','UNP','CTAS','RSG','FDX','NSC','CSX','ROK','EMR','JCI','AME','PCAR','URI','PWR'],
    'XLC': ['META','GOOGL','GOOG','NFLX','TMUS','CMCSA','DIS','T','CHTR','EA','VZ','WBD','OMC','TTWO','LYV','FOXA'],
    'XLU': ['NEE','SO','DUK','SRE','D','AEP','EXC','ED','XEL','WEC','ES','ETR','PPL','FE','CNP','NI','AES'],
    'XLY': ['AMZN','TSLA','HD','MCD','LOW','TJX','BKNG','NKE','SBUX','TGT','GM','F','CMG','YUM','HLT','MAR'],
    'XLP': ['PG','COST','WMT','KO','PEP','PM','MDLZ','CL','EL','GIS','STZ','HSY','MKC','CHD','KHC'],
    'XLRE': ['AMT','PLD','CCI','EQIX','PSA','O','WELL','SPG','DLR','AVB','EQR','VTR','ARE'],
    'XLB': ['LIN','APD','SHW','ECL','DD','PPG','NEM','FCX','NUE','DOW','ALB','CF'],
    'SPY': ['AAPL','NVDA','MSFT','AMZN','META','GOOGL','TSLA','BRK.B','AVGO','JPM','LLY','V'],
    'QQQ': ['AAPL','NVDA','MSFT','AMZN','META','GOOGL','TSLA','AVGO','COST','NFLX','AMD'],
    'IWM': ['SMCI','PLTR','AVAV','ESAB','ENSG','SFM','SAIA','BRBR','COOP','FN'],
    'SMH': ['NVDA','AVGO','TSM','AMAT','ASML','AMD','QCOM','KLAC','LRCX','MU','ADI','MRVL','MCHP','ON','TXN'],
    'SOXX': ['NVDA','AVGO','AMD','QCOM','AMAT','KLAC','LRCX','MU','ADI','MRVL','MCHP','ON','TXN','INTC','MPWR'],
    'ITA': ['GEV','LMT','RTX','NOC','BA','GD','HII','TDG','TXT','L3HT','MOOG','HEI'],
    'XAR': ['KTOS','RKLB','AVAV','HEI','TGI','DRS','CW','AXON','GEV','LMT','RTX'],
    'ARKK': ['TSLA','COIN','ROKU','SQ','TWLO','EXAS','BEAM','CRISPR','RXRX','PATH'],
    'ARKG': ['RXRX','PACB','CRSP','BEAM','NTLA','TDOC','VCYT','EXAS','FATE','SEER'],
    'CIBR': ['CRWD','PANW','OKTA','ZS','CYBR','S','TENB','VRNS','NET','FTNT','CSCO'],
    'BOTZ': ['NVDA','ISRG','ABB','FANUY','IRBT','AeroV','KLAC'],
    'AIQ':  ['NVDA','MSFT','GOOGL','META','AMZN','ORCL','CRM','BAIDU','SAP'],
    'QTUM': ['IONQ','RGTI','QUBT','QBTS','IBMQ','MSFT','GOOGL','NVDA','HONEYWELL'],
    'MAGS': ['AAPL','NVDA','MSFT','AMZN','META','GOOGL','TSLA'],
    'PAVE': ['VMC','MLM','ETN','PWR','FAST','GWW','NVR','PHM','URI','FERG'],
    'XBI':  ['RXRX','BEAM','CRSP','NTLA','ALNY','MRNA','VRTX','REGN','BIIB','SGEN'],
    'IBB':  ['ABBV','AMGN','GILD','REGN','VRTX','MRNA','BIIB','ILMN','ALNY'],
    'INDA': ['INFY','HDB','IBN','WIT','VEDL','SIFY','VNET'],
    'SKYY': ['AMZN','MSFT','GOOGL','CRM','ORCL','SNOW','DDOG','NET','CFLT','TWLO'],
    'ICLN': ['ENPH','FSLR','RUN','SEDG','PLUG','BE','ARRY','NOVA'],
    'TAN':  ['ENPH','FSLR','RUN','SEDG','ARRY','NOVA','SPWR','CSIQ'],
    'LIT':  ['ALB','SQM','LAC','LTHM','PLL','SGML'],
    'URA':  ['CCJ','NXE','DNN','UUUU','URG','PDN'],
    'COPX': ['FCX','SCCO','TECK','FM','IVN','ANTO'],
    'BLOK': ['COIN','MARA','RIOT','CLSK','HUT','BTBT','CIFR'],
    'FINX': ['V','MA','PYPL','SQ','AFRM','SOFI','UPST','HOOD','COIN','MQ'],
    'REMX': ['MP','LTHM','ALB','SQM','UUUU','SGML','NOVL'],
    'TUR':  ['AKBNK','GARAN','THYAO','TCELL','EREGL'],
    'NASA': ['RKLB','MNTS','ASTS','SPCE','MAXR','PL'],
    'UFO':  ['RKLB','PL','ASTS','SPCE','GSAT','VSAT'],
    'ARKX': ['RKLB','KTOS','IRDM','AVAV','AJRD','MAXR'],
    'CHAT': ['NVDA','MSFT','GOOGL','META','AMZN','ORCL','CRM','BAIDU'],
    'SHLD': ['LMT','RTX','PLTR','NOC','GD','KTOS','CACI','AXON','DFEN'],
    'IXN':  ['AAPL','NVDA','MSFT','AVGO','TSM','ASML','AMD','CRM'],
    'IXJ':  ['UNH','LLY','JNJ','ABBV','NVO','AZN','ROG'],
    'IXC':  ['XOM','CVX','SHEL','TTE','BP','EQNR'],
    'IXG':  ['JPM','BRK.B','BAC','WFC','GS','MS','HSBC'],
    'EEM':  ['TSM','BABA','TCEHY','SMSN','HDB','RELIANCE'],
    'EFA':  ['ASML','NVO','NESN','ROG','NOVN','SAP','LVMH','SONY'],
    'IWF':  ['AAPL','NVDA','MSFT','AMZN','META','GOOGL','LLY','AVGO'],
    'IWD':  ['BRK.B','JPM','XOM','JNJ','WMT','PG','BAC','CVX'],
    'TLT':  ['US30Y','TLH','GOVT'],  # bond ETF — no equity holdings
    'LQD':  [],  # bond ETF
    'HYG':  [],  # bond ETF
    'GLD':  [],  # gold ETF
    'IBIT': [],  # bitcoin ETF
    'SHY':  [],  # short treasury ETF
    'RSP':  ['AAPL','NVDA','MSFT','AMZN','META','GOOGL','JPM','V','UNH','XOM'],
    'IYT':  ['UPS','FDX','UNP','CSX','NSC','JBHT','ODFL','SAIA'],
    'MXI':  ['LIN','BHP','RIO','NEM','FCX','APD'],
    'KXI':  ['PG','NESN','NVO','MDLZ','KO','PEP','WMT'],
    'FINX': ['V','MA','PYPL','SQ','AFRM','SOFI','UPST'],
}

# ── Ticker validation ─────────────────────────────────────────────────────────
_TK_RE = re.compile(r'^[A-Z]{1,6}(\.[AB])?$')
def valid_tk(t):
    return bool(_TK_RE.match(str(t).strip()))

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Fetch real ETF holdings from Yahoo Finance (funds_data.top_holdings)
# ──────────────────────────────────────────────────────────────────────────────
print("Fetching real ETF holdings from Yahoo Finance...")
etf_holdings_map = {}   # etf -> [{t, n, w}, ...]
all_holding_tks  = set()

for etf in ETF_TICKERS:
    got_live = False
    try:
        fd = yf.Ticker(etf).funds_data
        if fd is not None:
            th = fd.top_holdings          # DataFrame: index=symbol, cols include holdingName, holdingPercent
            if th is not None and not th.empty:
                rows = []
                for sym, row in th.iterrows():
                    sym = str(sym).strip().upper()
                    if not valid_tk(sym) or sym == etf:
                        continue
                    name = str(row.get('holdingName', sym))
                    pct  = float(row.get('holdingPercent', 0)) * 100  # Yahoo gives 0-1 fraction
                    rows.append({'t': sym, 'n': name, 'w': round(pct, 2)})
                    all_holding_tks.add(sym)
                if rows:
                    etf_holdings_map[etf] = rows
                    got_live = True
                    print(f"  {etf}: {len(rows)} holdings from Yahoo Finance ✓")
    except Exception as ex:
        pass  # fall through to hardcoded

    if not got_live:
        # Use hardcoded fallback tickers
        fallback_tks = HARDCODED_HOLDINGS.get(etf, [])
        etf_holdings_map[etf] = [{'t': t, 'n': t, 'w': 0} for t in fallback_tks if valid_tk(t)]
        all_holding_tks.update(fallback_tks)
        src = 'hardcoded fallback' if fallback_tks else 'no equity holdings'
        print(f"  {etf}: {len(fallback_tks)} tickers ({src})")

    time.sleep(0.15)  # gentle rate limiting — Yahoo is free but don't hammer it

print(f"\nTotal unique holding tickers discovered: {len(all_holding_tks)}")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Ratio signal computation (1-year data for SMA-20 / SMA-50)
# ──────────────────────────────────────────────────────────────────────────────
def classify(curr, s20, s50, inv=False):
    above20 = curr > s20
    s20_above_s50 = s20 > s50
    if above20 and s20_above_s50:            sig = "strong-bull"
    elif above20:                             sig = "bull"
    elif not above20 and not s20_above_s50:  sig = "strong-bear"
    else:                                     sig = "bear"
    if inv:
        flip = {"strong-bull":"strong-bear","bull":"bear","bear":"bull","strong-bear":"strong-bull"}
        sig = flip[sig]
    return sig

def sma(series, n):
    s = series[-min(n, len(series)):]
    return sum(s) / len(s)

ratio_tickers = list({r["num"] for r in ALL_R} | {r["den"] for r in ALL_R})
print(f"\nFetching {len(ratio_tickers)} ratio tickers (1y for SMA)...")

try:
    raw = yf.download(ratio_tickers, period="1y", interval="1d",
                      auto_adjust=True, progress=False, threads=True)
except Exception as e:
    print(f"Ratio download failed: {e}", file=sys.stderr)
    sys.exit(1)

closes = {}
if isinstance(raw.columns, pd.MultiIndex):
    close_df = raw["Close"]
    for t in ratio_tickers:
        if t in close_df.columns:
            s = close_df[t].dropna()
            if len(s) >= SMA_L + 5:
                closes[t] = s
else:
    t = ratio_tickers[0]
    s = raw["Close"].dropna()
    if len(s) >= SMA_L + 5:
        closes[t] = s

print(f"Got ratio data for {len(closes)}/{len(ratio_tickers)} tickers")

results = []
for r in ALL_R:
    num_t, den_t = r["num"], r["den"]
    if num_t not in closes or den_t not in closes:
        results.append({**r, "error": True}); continue
    num_s, den_s = closes[num_t], closes[den_t]
    common_idx = num_s.index.intersection(den_s.index)
    if len(common_idx) < SMA_L + 5:
        results.append({**r, "error": True}); continue
    ratio  = (num_s[common_idx] / den_s[common_idx]).values.tolist()
    curr   = ratio[-1]
    prev5  = ratio[max(0, len(ratio)-6)]
    s20    = sma(ratio, SMA_S)
    s50    = sma(ratio, SMA_L)
    cl     = classify(curr, s20, s50, r.get("inv", False))
    results.append({**r, "error": False, "curr": round(curr,6), "s20": round(s20,6),
                    "s50": round(s50,6), "prev5": round(prev5,6), "cl": cl})
    print(f"  {r['key']:12s} → {cl}")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — Price download for all ETFs + holdings + leveraged ETFs (5d, fast)
# ──────────────────────────────────────────────────────────────────────────────
all_price_tks = sorted(set(
    t for t in list(all_holding_tks) + ETF_TICKERS + LEVERAGED_TICKERS
    if valid_tk(t)
))
# Skip tickers already in closes (1y data → reuse)
need_5d = [t for t in all_price_tks if t not in closes]
price_closes = dict(closes)

if need_5d:
    print(f"\nFetching prices for {len(need_5d)} tickers (5d)...")
    try:
        raw2 = yf.download(need_5d, period="5d", interval="1d",
                           auto_adjust=True, progress=False, threads=True)
        if isinstance(raw2.columns, pd.MultiIndex):
            c2 = raw2["Close"]
            for t in need_5d:
                if t in c2.columns:
                    s = c2[t].dropna()
                    if len(s) >= 2:
                        price_closes[t] = s
        elif len(need_5d) == 1:
            s = raw2["Close"].dropna()
            if len(s) >= 2:
                price_closes[need_5d[0]] = s
    except Exception as e:
        print(f"5d price fetch warning: {e}", file=sys.stderr)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — Compute ticker_prices {ticker: {p, c}}
# ──────────────────────────────────────────────────────────────────────────────
ticker_prices = {}
for tk in all_price_tks:
    s = price_closes.get(tk)
    if s is None or len(s) < 2:
        continue
    try:
        price = float(s.iloc[-1])
        prev  = float(s.iloc[-2])
        if prev <= 0 or price != price or prev != prev:   # NaN guard
            continue
        ticker_prices[tk] = {"p": round(price, 2), "c": round((price/prev - 1)*100, 2)}
    except Exception:
        pass

print(f"ticker_prices: {len(ticker_prices)} tickers with price data")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Write data.json
# ──────────────────────────────────────────────────────────────────────────────
output = {
    "ts":            int(time.time()*1000),
    "generated":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "data":          results,
    "ticker_prices": ticker_prices,
    "etf_holdings":  etf_holdings_map,   # real full holdings per ETF from Yahoo
}
with open("data.json", "w") as f:
    json.dump(output, f, separators=(",",":"))

ok = sum(1 for r in results if not r.get("error"))
live_h = sum(1 for v in etf_holdings_map.values() if v and v[0].get('w',0) > 0)
print(f"\n✅ data.json written")
print(f"   Ratios:        {ok}/{len(results)} OK")
print(f"   ETF holdings:  {live_h}/{len(ETF_TICKERS)} from Yahoo Finance live")
print(f"   Ticker prices: {len(ticker_prices)} tickers")
