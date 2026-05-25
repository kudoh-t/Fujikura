import os
import requests
import datetime as dt
import pandas as pd
import yfinance as yf
import ta

TOKEN = os.getenv("LINE_NOTIFY_TOKEN")
LOOKBACK = 120

def line_notify(msg):
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    data = {"message": msg}
    requests.post(url, headers=headers, data=data)

def fetch(ticker):
    end = dt.date.today()
    start = end - dt.timedelta(days=LOOKBACK)
    return yf.download(ticker, start=start, end=end)

def add_indicators(df):
    df["MA25"] = df["Close"].rolling(25).mean()
    df["VOL5"] = df["Volume"].rolling(5).mean()
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], 14).rsi()

    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()
    return df

# ============================
# フジクラ（底打ち）
# ============================
def check_fujikura(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    signals = []

    # 25日線上抜け
    if prev["Close"] < prev["MA25"] and last["Close"] > last["MA25"]:
        signals.append("25日線上抜け")

    # RSI反転
    if prev["RSI"] < 40 < last["RSI"]:
        signals.append("RSI反転")

    # 出来高急増
    if last["Volume"] > 1.5 * last["VOL5"]:
        signals.append("出来高急増")

    # MACD GC
    if prev["MACD"] < prev["MACD_SIGNAL"] and last["MACD"] > last["MACD_SIGNAL"]:
        signals.append("MACDゴールデンクロス")

    if signals:
        return "【フジクラ 反転シグナル】\n- " + "\n- ".join(signals)
    return None

# ============================
# 浜ホト（押し目）
# ============================
def check_hamahoto(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    signals = []

    if 1650 <= last["Close"] <= 1700:
        signals.append("押し目価格帯（1650〜1700）")

    if last["RSI"] < 40:
        signals.append("RSI売られすぎ")

    if last["Volume"] < last["VOL5"] * 0.8:
        signals.append("出来高減少（売り枯れ）")

    if last["Low"] < prev["Low"] and last["Close"] > last["Open"]:
        signals.append("下ヒゲ陽線（反転初期）")

    if signals:
        return "【浜松ホトニクス 押し目】\n- " + "\n- ".join(signals)
    return None

# ============================
# 村田（反転）
# ============================
def check_murata(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    signals = []

    if prev["Close"] < prev["MA25"] and last["Close"] > last["MA25"]:
        signals.append("25日線上抜け")

    if prev["RSI"] < 40 < last["RSI"]:
        signals.append("RSI反転")

    if last["Volume"] > 1.5 * last["VOL5"]:
        signals.append("出来高急増")

    if prev["MACD"] < prev["MACD_SIGNAL"] and last["MACD"] > last["MACD_SIGNAL"]:
        signals.append("MACDゴールデンクロス")

    if signals:
        return "【村田製作所 反転】\n- " + "\n- ".join(signals)
    return None

# ============================
# メイン処理
# ============================
def main():
    messages = []

    # フジクラ
    df_f = add_indicators(fetch("5803.T"))
    msg_f = check_fujikura(df_f)
    if msg_f:
        messages.append(msg_f)

    # 浜ホト
    df_h = add_indicators(fetch("6965.T"))
    msg_h = check_hamahoto(df_h)
    if msg_h:
        messages.append(msg_h)

    # 村田
    df_m = add_indicators(fetch("6981.T"))
    msg_m = check_murata(df_m)
    if msg_m:
        messages.append(msg_m)

    # まとめて通知
    if messages:
        line_notify("\n\n".join(messages))

if __name__ == "__main__":
    main()
