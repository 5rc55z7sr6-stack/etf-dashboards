import json, time, sys, re
from datetime import datetime, timezone
import yfinance as yf
import pandas as pd

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

# ── All 62 ETFs tracked on the dashboard ─────────────────────────────────────
ETF_TICKERS = [
    'XLK','XLF','XLE','XLV','XLI','XLC','XLU','XLY','XLP','XLRE','XLB',
    'IXN','IXJ','IXC','IXG','MXI','KXI',
    'SPY','QQQ','IWM','RSP','TLT','LQD','HYG','GLD','IBIT','SMH',
    'EEM','EFA','SHY','IWF','IWD','IYT',
    'ITA','XAR','SHLD','NASA','UFO','ARKX','QTUM','AIQ','CHAT','BOTZ',
    'CIBR','URA','BLOK','ICLN','TAN','LIT','ARKG','ARKK',
    'SOXX','MAGS','PAVE','XBI','IBB','INDA','COPX','SKYY','FINX','REMX','TUR',
]

# ── All unique holding stock tickers embedded in the dashboard ────────────────
# (extracted from the HOLDINGS array in ETF.html — US-listed only)
HOLDING_TICKERS = [
    'AAPL','NVDA','MSFT','AVGO','META','AMD','CRM','ADBE','AMAT','QCOM','ORCL',
    'CSCO','NOW','INTU','PANW','KLAC','LRCX','MU','MRVL','SNPS','CDNS','FTNT',
    'BRK.B','JPM','V','MA','BAC','WFC','GS','MS','BLK','SPGI','CME','ICE','AXP',
    'C','USB','PNC','TRV','COF','MET','AON',
    'XOM','CVX','COP','EOG','SLB','MPC','VLO','PSX','OXY','HAL','BKR','DVN',
    'FANG','HES','MRO','OKE','WMB','KMI','LNG',
    'UNH','LLY','JNJ','ABBV','MRK','PFE','TMO','DHR','ABT','ISRG','ELV','CVS',
    'AMGN','CI','BMY','MDT','BSX','SYK','BDX','GEHC','ZTS','VRTX',
    'GEV','RTX','CAT','HON','DE','LMT','PH','NOC','ETN','UNP','CTAS','RSG',
    'FDX','NSC','CSX','ROK','EMR','JCI','AME','PCAR','URI','PWR',
    'GOOGL','GOOG','NFLX','TMUS','CMCSA','DIS','T','CHTR','EA','VZ','WBD',
    'OMC','TTWO','LYV','FOXA','PARA','NWSA','IPG','MTCH',
    'NEE','SO','DUK','SRE','D','AEP','EXC','ED','XEL','WEC','ES','ETR','PPL',
    'FE','CNP','NI','AES','PNW','LNT','EVRG',
    'AMZN','TSLA','HD','MCD','LOW','TJX','BKNG','NKE','SBUX','TGT','GM','F',
    'CMG','YUM','HLT','MAR','GRMN','ORLY','RH','BBY',
    'PG','COST','WMT','KO','PEP','PM','MDLZ','CL','EL','GIS','STZ','HSY',
    'MKC','CHD','KHC','SJM','HRL','CAG','CPB','TAP',
    'AMT','PLD','CCI','EQIX','PSA','O','WELL','SPG','DLR','AVB','EQR','VTR',
    'ARE','BXP','WY','ESS','MAA','UDR','CPT','ELS',
    'LIN','APD','SHW','ECL','DD','PPG','NEM','FCX','NUE','DOW','ALB','CF',
    'MOS','IFF','RPM','EMN','CE','FMC','CTVA','MLM','VMC',
    'AAON','ACN','ADI','AEIS','AI','ACM','ALB','ALNY','AMBA','AMT','ANSS',
    'APH','ARKK','AZO','BAH','BLDP','BLNK','BRTX','CACI','CDNS',
    'ENPH','FSLR','RUN','SEDG','PLUG','BE','ARRY','NOVA','CSIQ','SPWR',
    'ALB','LTHM','SQM','LAC','PLL','LTUM','NOVL',
    'REGN','BIIB','ILMN','NTLA','EDIT','CRSP','BEAM','RXRX','PACB','FATE',
    'MRNA','BNTX','NVAX','SGEN','EXAS','VCYT',
    'PLTR','COIN','ROKU','TWLO','ZM','DKNG','U','RBLX','OPEN','HOOD',
    'SNOW','DDOG','NET','ZS','CRWD','OKTA','CYBR','S','TENB','VRNS',
    'GRAB','SE','MELI','ABNB','DASH','LYFT','UBER','SHOP','SQ','AFRM',
    'SOFI','UPST','PYPL','WU','MQ','PAYO',
    'MP','UUUU','DNN','URG','CCJ','NXE','PDN','BOE','YCA',
    'FREEPORT','FCX','SCCO','IVN','FM','ANTO','TECK',
    'RELIANCE','HDFCBANK','INFY','ICICIBANK','TCS','BHARTI',
    'TSM','ASML','SAP','SIEGY','SMSN',
    'VUZI','MVIS','AEVA','OUST','LAZR','LIDR',
    'IRDM','MAXR','SPCE','RKLB','PL','ASTS',
    'GEO','CXW','AXON','CACI','BAH','LDOS','SAIC','KEYW',
    'WM','RSG','CWST','SRCL',
    'EQNR','BP','TTE','SHEL','E',
]

# ── Ticker validation (US-style: 1-6 caps, optional .B/.A) ──────────────────
_TK_RE = re.compile(r'^[A-Z]{1,6}(\.[AB])?$')
def valid_tk(t): return bool(_TK_RE.match(t))

ALL_PRICE_TICKERS = sorted(set(
    t for t in ETF_TICKERS + HOLDING_TICKERS if valid_tk(t)
))

def classify(curr, s20, s50, inv=False):
    above20 = curr > s20
    s20_above_s50 = s20 > s50
    if above20 and s20_above_s50:       sig = "strong-bull"
    elif above20:                        sig = "bull"
    elif not above20 and not s20_above_s50: sig = "strong-bear"
    else:                                sig = "bear"
    if inv:
        flip = {"strong-bull":"strong-bear","bull":"bear","bear":"bull","strong-bear":"strong-bull"}
        sig = flip[sig]
    return sig

def sma(series, n):
    s = series[-min(n, len(series)):]
    return sum(s) / len(s)

# ── Step 1: Download ratio tickers (1y for SMA computation) ──────────────────
ratio_tickers = list({r["num"] for r in ALL_R} | {r["den"] for r in ALL_R})
print(f"Fetching {len(ratio_tickers)} ratio tickers (1y)...")

try:
    raw = yf.download(ratio_tickers, period="1y", interval="1d", auto_adjust=True, progress=False, threads=True)
except Exception as e:
    print(f"Download failed: {e}", file=sys.stderr)
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

# ── Step 2: Compute ratio signals ─────────────────────────────────────────────
results = []
for r in ALL_R:
    num_t, den_t = r["num"], r["den"]
    if num_t not in closes or den_t not in closes:
        results.append({**r, "error": True})
        continue
    num_s, den_s = closes[num_t], closes[den_t]
    common_idx = num_s.index.intersection(den_s.index)
    if len(common_idx) < SMA_L + 5:
        results.append({**r, "error": True})
        continue
    ratio = (num_s[common_idx] / den_s[common_idx]).values.tolist()
    curr  = ratio[-1]
    prev5 = ratio[max(0, len(ratio)-6)]
    s20   = sma(ratio, SMA_S)
    s50   = sma(ratio, SMA_L)
    cl    = classify(curr, s20, s50, r.get("inv", False))
    results.append({**r, "error": False, "curr": round(curr,6), "s20": round(s20,6), "s50": round(s50,6), "prev5": round(prev5,6), "cl": cl})
    print(f"  {r['key']:12s} → {cl}")

# ── Step 3: Download price tickers (5d, fast) ─────────────────────────────────
# Skip tickers already fetched above (reuse closes)
need_price = [t for t in ALL_PRICE_TICKERS if t not in closes]
price_closes = dict(closes)  # copy existing

if need_price:
    print(f"\nFetching {len(need_price)} price tickers (5d)...")
    try:
        raw2 = yf.download(need_price, period="5d", interval="1d",
                           auto_adjust=True, progress=False, threads=True)
        if isinstance(raw2.columns, pd.MultiIndex):
            close_df2 = raw2["Close"]
            for t in need_price:
                if t in close_df2.columns:
                    s = close_df2[t].dropna()
                    if len(s) >= 2:
                        price_closes[t] = s
        elif len(need_price) == 1:
            t = need_price[0]
            s = raw2["Close"].dropna()
            if len(s) >= 2:
                price_closes[t] = s
    except Exception as e:
        print(f"Price fetch warning: {e}", file=sys.stderr)

# Also make sure 1y-downloaded ratio tickers have at least 2 days of data
for t, s in closes.items():
    if t not in price_closes and len(s) >= 2:
        price_closes[t] = s

# ── Step 4: Compute ticker_prices {ticker: {p, c}} ───────────────────────────
ticker_prices = {}
for tk in ALL_PRICE_TICKERS:
    s = price_closes.get(tk)
    if s is None or len(s) < 2:
        continue
    try:
        price = float(s.iloc[-1])
        prev  = float(s.iloc[-2])
        if prev <= 0 or not all(map(lambda x: x == x, [price, prev])):  # NaN check
            continue
        chg = (price / prev - 1) * 100
        ticker_prices[tk] = {"p": round(price, 2), "c": round(chg, 2)}
    except Exception:
        pass

print(f"ticker_prices: {len(ticker_prices)} tickers with price data")

# ── Step 5: Write data.json ───────────────────────────────────────────────────
output = {
    "ts": int(time.time()*1000),
    "data": results,
    "ticker_prices": ticker_prices,
    "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
with open("data.json", "w") as f:
    json.dump(output, f, separators=(",",":"))

ok = sum(1 for r in results if not r.get("error"))
print(f"\n✅ data.json written — {ok}/{len(results)} ratios · {len(ticker_prices)} prices OK")
