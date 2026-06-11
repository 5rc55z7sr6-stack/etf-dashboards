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

# ── Best Performers groups (must match JS BP_GROUPS exactly) ──────────────────
BP_GROUPS = {
    'US Sectors':      ['XLK','XLF','XLE','XLV','XLI','XLC','XLU','XLY','XLP','XLRE','XLB'],
    'Global Sectors':  ['IXN','IXJ','IXC','IXG','MXI','KXI'],
    'Macro / Asset':   ['QQQ','IWM','SMH','SOXX','IBIT','GLD','EEM','EFA','RSP','HYG','TLT','MAGS','SKYY','FINX','INDA'],
    'Trending Themes': ['ITA','XAR','SHLD','NASA','UFO','QTUM','AIQ','CHAT','BOTZ','CIBR','URA','ARKK','ARKG','XBI','COPX','PAVE','BLOK','ICLN','TAN','LIT','REMX'],
}
ALL_BP_TICKERS = list({t for g in BP_GROUPS.values() for t in g} | {'SPY'})

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

# ── Leveraged ETFs (trade ideas in popup) — BULL + BEAR ───────────────────────
LEVERAGED_TICKERS = [
    # Bull leveraged
    'TECL','TQQQ','FAS','DPST','ERX','NRGU','CURE','LABU','DUSL','TPOR',
    'MIDU','TNA','URTY','SPXL','UPRO','UDOW','SOXL','USD','FNGU','DFEN',
    'WANT','INDL','EDC','TMF','UBT','BIB','BITX','BITU',
    'NAIL','DRN','HIBL','WEBL','UGL','NUGT','KLNE','EURL','EFO','EET',
    # Bear / inverse leveraged
    'TECS','SQQQ','FAZ','SKF','ERY','DRIP','LABD','SPXS','SPXU',
    'TZA','SRTY','TMV','TBT','TBF','GLL','DUST','SOXS','DRV','REK',
    'EDZ','EEV','HIBS','WEBS','FNGD','SBIT','QID',
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
                    # yfinance column names vary by version: 'Name'/'Holding Percent'
                    # (current) vs 'holdingName'/'holdingPercent' (older)
                    name = str(row.get('Name') or row.get('holdingName') or sym)
                    raw_pct = float(row.get('Holding Percent') or row.get('holdingPercent') or 0)
                    # Yahoo sometimes returns 0-1 fraction, sometimes 0-100 percentage
                    pct = raw_pct if raw_pct > 1 else raw_pct * 100
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
    # Save last 22 ratio values for sparkline rendering in the frontend
    vals = [round(v, 6) for v in ratio[-22:]]
    results.append({**r, "error": False, "curr": round(curr,6), "s20": round(s20,6),
                    "s50": round(s50,6), "prev5": round(prev5,6), "cl": cl, "vals": vals})
    print(f"  {r['key']:12s} → {cl}")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2.5 — Download 1y closes for BP tickers not already fetched
# ──────────────────────────────────────────────────────────────────────────────
bp_need_1y = [t for t in ALL_BP_TICKERS if valid_tk(t) and t not in closes]
if bp_need_1y:
    print(f"\nFetching 1y closes for {len(bp_need_1y)} Best Performer tickers...")
    try:
        raw_bp = yf.download(bp_need_1y, period="1y", interval="1d",
                             auto_adjust=True, progress=False, threads=True)
        if isinstance(raw_bp.columns, pd.MultiIndex):
            bp_df = raw_bp["Close"]
            for t in bp_need_1y:
                if t in bp_df.columns:
                    s = bp_df[t].dropna()
                    if len(s) >= 25:
                        closes[t] = s
        elif len(bp_need_1y) == 1:
            s = raw_bp["Close"].dropna()
            if len(s) >= 25:
                closes[bp_need_1y[0]] = s
    except Exception as e:
        print(f"BP 1y fetch warning: {e}", file=sys.stderr)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2.6 — Compute BP scores: ETF/SPY relative strength + SMA20/50
# ──────────────────────────────────────────────────────────────────────────────
def compute_bp(ticker, spy_s):
    etf_s = closes.get(ticker)
    if etf_s is None or spy_s is None or len(etf_s) < 25:
        return None
    common = etf_s.index.intersection(spy_s.index)
    if len(common) < 25:
        return None
    ratio = (etf_s[common] / spy_s[common]).values.tolist()
    curr  = ratio[-1]
    s20   = sma(ratio, 20)
    s50   = sma(ratio, min(50, len(ratio)))
    pct   = (curr - s20) / s20 * 100
    prev5 = ratio[max(0, len(ratio) - 6)]
    chg5  = (curr - prev5) / prev5 * 100
    bullish = curr > s20
    if   curr > s20 and s20 > s50: sig = "strong-bull"
    elif curr > s20:                sig = "bull"
    elif s20 < s50:                 sig = "strong-bear"
    else:                           sig = "bear"
    etf_price = float(etf_s.iloc[-1])
    return {
        "curr":     round(curr, 6),
        "s20":      round(s20, 6),
        "s50":      round(s50, 6),
        "pct":      round(pct, 3),
        "chg5":     round(chg5, 3),
        "sig":      sig,
        "bullish":  bullish,
        "closes":   [round(v, 6) for v in ratio[-20:]],
        "etfPrice": round(etf_price, 2),
    }

spy_s = closes.get('SPY')
bp_scores = {}
if spy_s is not None:
    for grp, tickers in BP_GROUPS.items():
        for tk in tickers:
            score = compute_bp(tk, spy_s)
            if score:
                bp_scores[tk] = score
    print(f"BP scores: {len(bp_scores)}/{sum(len(v) for v in BP_GROUPS.values())} ETFs computed")
else:
    print("WARNING: SPY closes not available — BP scores skipped")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — Price download for all ETFs + holdings + leveraged ETFs (5d, fast)
# ──────────────────────────────────────────────────────────────────────────────
# Tickers shown in the dashboard's static top-10 holdings tables that may not
# appear in Yahoo's live topHoldings (so they'd otherwise have no price).
STATIC_PAGE_TICKERS = [
 'AAON','ABB','ABT','ACM','ACN','ADBE','ADI','AEIS','AES','AI','AIR','AMBA','AMC','AME','AON','APOG',
 'ARE','ARQT','ARRY','ATEN','AVB','AXON','AZN','BAH','BAKKT','BALL','BBY','BDX','BEP','BHP','BIDU','BLK',
 'BMY','BNTX','BOX','BP','BRK.B','BSX','BTBT','CACI','CAG','CC','CCJ','CCO','CDNA','CDNS','CE','CELH',
 'CEVA','CF','CFLT','CGNX','CHD','CHKP','CHTR','CI','CMCSA','CME','CMG','CNP','COF','COHU','CPB','CRM',
 'CSIQ','CSWI','CTAS','CVS','CYBR','DCO','DD','DECK','DGHI','DHR','DKNG','DNN','DOW','DQ','DRS','DVN',
 'EB','ECL','ED','EFR','EL','ELV','EME','EMR','ENTG','EQNR','EQR','ES','ESLT','ESTC','EU','EVRG','EWJ',
 'EXAS','EXC','EXR','F','FANG','FATE','FE','FI','FIX','FORM','FOXA','FSLY','GEHC','GEN','GIS','GOLD',
 'GRMN','GTLB','GVA','HAL','HBM','HES','HLT','HRL','HSBC','HSY','HUBS','HWC','ICE','IDCC','IESC','IFF',
 'INFY','INVH','IP','IPG','IRM','IVN','J','JBHT','JCI','JOBY','KFRC','KHC','KMI','KRE','LDOS','LNG',
 'LNT','LUV','LYB','MAA','MARA','MDB','MDT','MDU','MET','MKC','MKSI','MLM','MPWR','MRCY','MRNA','MSTR',
 'MTCH','MYRG','NEO','NFLX','NI','NKE','NNN','NOW','NRG','NTLA','NVR','NVS','NWSA','NXE','OKE','ONTO',
 'OXY','PACB','PARA','PATH','PCAR','PDN','PH','PKG','PLS','PLXS','PNC','PNW','PPG','PPL','PRCT','QBTS',
 'QLYS','QUBT','RARE','RCUS','RGEN','RGTI','RH','RIOT','RMBS','ROAD','ROP','RPD','RPM','RSG','RXRX','S',
 'SAIA','SAIC','SAIL','SAN','SBAC','SHEL','SJM','SLAB','SMCI','SMPL','SNOW','SNPS','SOUN','SPCE','SPGI',
 'SPHB','SPIR','SPOT','SPR','SPSC','SQ','SRRK','STZ','SWKS','SYK','T','TAP','TEAM','TENB','TGT','TKO',
 'TMUS','TREX','TRGP','TRMB','TRV','TTE','TWLO','TXT','UDR','UFPI','UL','USB','UUUU','VALE','VCYT',
 'VRNS','VRRM','VZ','WEC','WOLF','YUM','ZBRA','ZM','ZS','ZTS','EFZ','QLD','UTSL',
]

all_price_tks = sorted(set(
    t for t in list(all_holding_tks) + ETF_TICKERS + LEVERAGED_TICKERS + STATIC_PAGE_TICKERS
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
# STEP 4.5 — Correct prices via Yahoo spark quote meta (authoritative).
# The daily-bar download sometimes has a null close for the latest session
# (e.g. DAL 2026-06-10), which silently falls back to a stale bar. The spark
# meta carries regularMarketPrice + chartPreviousClose and is always current.
# ──────────────────────────────────────────────────────────────────────────────
import urllib.request as _ur
import json as _json

def _spark_chunk(symbols):
    url = ("https://query1.finance.yahoo.com/v7/finance/spark?symbols="
           + ",".join(symbols) + "&range=1d&interval=1d")
    req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _ur.urlopen(req, timeout=20) as r:
        return _json.load(r)

corrected = 0
spark_fail = 0
for i in range(0, len(all_price_tks), 20):
    chunk = all_price_tks[i:i+20]
    try:
        js = _spark_chunk(chunk)
        for res in (js.get("spark", {}).get("result") or []):
            try:
                meta = res["response"][0]["meta"]
                tk = meta["symbol"]
                p = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose")
                if not p or not prev or prev <= 0:
                    continue
                new = {"p": round(float(p), 2), "c": round((float(p)/float(prev) - 1)*100, 2)}
                if ticker_prices.get(tk) != new:
                    corrected += 1
                ticker_prices[tk] = new
            except Exception:
                pass
    except Exception as e:
        spark_fail += 1
        if spark_fail <= 3:
            print(f"spark chunk warning: {e}", file=sys.stderr)

print(f"spark correction: {corrected} prices updated, {spark_fail} chunks failed")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4.7 — Today's Setups scan: SMA/ATR/volume/RS analytics for every stock,
# market internals, and pre-classified swing-trade candidates.
# ──────────────────────────────────────────────────────────────────────────────
SECTOR_ETFS = ['XLK','XLF','XLE','XLV','XLI','XLC','XLU','XLY','XLP','XLRE','XLB']
THEME_ETFS  = [e for e in ETF_TICKERS if e not in SECTOR_ETFS and e not in
               ('SPY','RSP','SHY','TLT','LQD','HYG','GLD','IWF','IWD')]

# stock → parent ETF (sectors take priority over themes)
stock_parent = {}
for etf in SECTOR_ETFS + THEME_ETFS:
    for h in etf_holdings_map.get(etf, []):
        stock_parent.setdefault(h['t'], etf)

stock_tks = sorted(set(stock_parent) - set(ETF_TICKERS) - set(LEVERAGED_TICKERS))
print(f"\nSetups scan: {len(stock_tks)} stocks across {len(set(stock_parent.values()))} parent ETFs")

setups_out = {"internals": {}, "list": [], "scanned": 0}
try:
    raw3 = yf.download(stock_tks + ETF_TICKERS, period="3mo", interval="1d",
                       auto_adjust=True, progress=False, threads=True)
    cl3, hi3, lo3, vo3 = raw3["Close"], raw3["High"], raw3["Low"], raw3["Volume"]

    def series_of(frame, t):
        try:
            s = frame[t].dropna()
            return s if len(s) >= 25 else None
        except Exception:
            return None

    def ret20(t):
        s = series_of(cl3, t)
        if s is None or len(s) < 21: return None
        return (float(s.iloc[-1]) / float(s.iloc[-21]) - 1) * 100

    etf_ret20 = {e: ret20(e) for e in ETF_TICKERS}
    spy_r20 = etf_ret20.get('SPY')

    stocks_above_s20 = 0; stocks_total = 0; new_highs = 0; new_lows = 0
    candidates = []
    for t in stock_tks:
        s = series_of(cl3, t)
        if s is None: continue
        closes = [float(x) for x in s]
        price = ticker_prices.get(t, {}).get('p') or closes[-1]
        chg   = ticker_prices.get(t, {}).get('c', 0)
        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        if sma50 is None: continue
        hi = series_of(hi3, t); lo = series_of(lo3, t); vo = series_of(vo3, t)
        # ATR14 (true range needs aligned H/L/C)
        atr_pct = None
        if hi is not None and lo is not None:
            h = [float(x) for x in hi[-15:]]; l = [float(x) for x in lo[-15:]]
            c = closes[-16:]
            if len(h) >= 14 and len(l) >= 14 and len(c) >= 15:
                trs = [max(h[i]-l[i], abs(h[i]-c[i]), abs(l[i]-c[i])) for i in range(1, min(len(h), len(l), len(c)-1))]
                if trs: atr_pct = round(sum(trs[-14:]) / len(trs[-14:]) / price * 100, 2)
        vol_ratio = None
        if vo is not None and len(vo) >= 21:
            v = [float(x) for x in vo]
            avg20 = sum(v[-21:-1]) / 20
            if avg20 > 0: vol_ratio = round(v[-1] / avg20, 2)
        hi3m = max(closes); lo3m = min(closes)
        near_high = price >= hi3m * 0.98
        near_low  = price <= lo3m * 1.02
        d20 = (price / sma20 - 1) * 100
        d50 = (price / sma50 - 1) * 100
        stocks_total += 1
        if price > sma20: stocks_above_s20 += 1
        if near_high: new_highs += 1
        if near_low: new_lows += 1

        parent = stock_parent.get(t)
        bp = bp_scores.get(parent) or {}
        p_r20 = etf_ret20.get(parent)
        s_r20 = ret20(t)
        if s_r20 is None or p_r20 is None: continue
        rs_sector  = round(s_r20 - p_r20, 2)            # stock vs own ETF, 20d
        sector_rs  = round(p_r20 - spy_r20, 2) if spy_r20 is not None else 0  # ETF vs SPY

        sec_bull = bool(bp.get('bullish'))
        up = sma20 > sma50; down = sma20 < sma50
        typ = None
        if sec_bull and up and rs_sector > 0 and -4 <= d20 <= 1 and price > sma50:
            typ = 'pullback_long'
        elif (not sec_bull) and down and rs_sector < 0 and -1 <= d20 <= 4 and price < sma50:
            typ = 'rip_short'
        elif sec_bull and rs_sector > 3 and near_high and up:
            typ = 'rs_leader'
        elif (not sec_bull) and rs_sector < -3 and near_low and down:
            typ = 'rs_laggard'
        if not typ: continue
        score = abs(rs_sector) + abs(sector_rs) * 0.5 + (1.5 if (vol_ratio or 0) >= 1.5 else 0)
        candidates.append({
            "t": t, "etf": parent, "type": typ, "p": round(price, 2), "c": chg,
            "s20": round(sma20, 2), "s50": round(sma50, 2),
            "d20": round(d20, 2), "d50": round(d50, 2),
            "atr": atr_pct, "vr": vol_ratio,
            "rsS": rs_sector, "rsE": sector_rs,
            "hi3m": round(hi3m, 2), "lo3m": round(lo3m, 2),
            "score": round(score, 2),
        })

    candidates.sort(key=lambda x: -x["score"])
    # max 4 per type so one regime doesn't drown the list
    per_type = {}
    final = []
    for cnd in candidates:
        if per_type.get(cnd["type"], 0) >= 4: continue
        per_type[cnd["type"]] = per_type.get(cnd["type"], 0) + 1
        final.append(cnd)

    sec_bull_n = sum(1 for e in SECTOR_ETFS if (bp_scores.get(e) or {}).get('bullish'))
    rsp = bp_scores.get('RSP') or {}
    setups_out = {
        "internals": {
            "sectorsBull": sec_bull_n, "sectorsTotal": len(SECTOR_ETFS),
            "pctAboveS20": round(stocks_above_s20 / stocks_total * 100, 1) if stocks_total else None,
            "newHighs": new_highs, "newLows": new_lows, "universe": stocks_total,
            "rspBull": bool(rsp.get('bullish')), "rspPct": rsp.get('pct'),
        },
        "list": final[:16],
        "scanned": stocks_total,
    }
    print(f"Setups: {len(final[:16])} candidates from {stocks_total} stocks "
          f"({', '.join(f'{k}:{v}' for k,v in per_type.items())})")
except Exception as e:
    print(f"Setups scan failed (non-fatal): {e}", file=sys.stderr)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Write data.json
# ──────────────────────────────────────────────────────────────────────────────
output = {
    "ts":            int(time.time()*1000),
    "generated":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "data":          results,
    "ticker_prices": ticker_prices,
    "etf_holdings":  etf_holdings_map,
    "bp_scores":     bp_scores,          # pre-computed ETF/SPY relative strength — no CORS needed
    "setups":        setups_out,         # Today's Setups: internals + swing candidates
}
with open("data.json", "w") as f:
    json.dump(output, f, separators=(",",":"))

ok = sum(1 for r in results if not r.get("error"))
live_h = sum(1 for v in etf_holdings_map.values() if v and v[0].get('w',0) > 0)
print(f"\n✅ data.json written")
print(f"   Ratios:        {ok}/{len(results)} OK")
print(f"   ETF holdings:  {live_h}/{len(ETF_TICKERS)} from Yahoo Finance live")
print(f"   Ticker prices: {len(ticker_prices)} tickers")
