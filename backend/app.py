from flask_cors import CORS
from flask import Flask, jsonify
import pickle
import numpy as np
import pandas as pd
import requests
import os

from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

from nltk.sentiment.vader import SentimentIntensityAnalyzer

app = Flask(__name__)
CORS(app)

# ================= INIT =================
sia = SentimentIntensityAnalyzer()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = pickle.load(open(os.path.join(BASE_DIR, "best_model.pkl"), "rb"))
scaler = pickle.load(open(os.path.join(BASE_DIR, "scaler.pkl"), "rb"))
feature_cols = pickle.load(open(os.path.join(BASE_DIR, "features.pkl"), "rb"))
use_scaler = pickle.load(open(os.path.join(BASE_DIR, "use_scaler.pkl"), "rb"))

NEWS_API_KEY = "d7cca4861a72452195936a0fb24c43fd"


# ================= SENTIMENT =================
def get_market_sentiment(coin):

    try:
        url = f"https://newsapi.org/v2/everything?q={coin}&apiKey={NEWS_API_KEY}&pageSize=10"
        res = requests.get(url, timeout=10).json()

        scores = []

        for article in res.get("articles", []):
            text = (article.get("title") or "") + " " + (article.get("description") or "")
            score = sia.polarity_scores(text)["compound"]
            scores.append(score)

        if len(scores) == 0:
            return 0.0

        return float(np.mean(scores))

    except Exception as e:
        print("Sentiment error:", e)
        return 0.0


# ================= FEATURE BUILDER =================
def build_features(df, coin):

    df["sma_7"] = SMAIndicator(df["close"], 7).sma_indicator()
    df["ema_12"] = EMAIndicator(df["close"], 12).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], 14).rsi()

    macd = MACD(df["close"])
    df["macd"] = macd.macd()

    bb = BollingerBands(df["close"], 20)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()

    atr = AverageTrueRange(df["high"], df["low"], df["close"], 14)
    df["atr"] = atr.average_true_range()

    obv = OnBalanceVolumeIndicator(df["close"], df["volume"])
    df["obv"] = obv.on_balance_volume()

    df["ret"] = np.log(df["close"]).diff()

    df["price_range"] = df["high"] - df["low"]
    df["body"] = abs(df["close"] - df["open"])

    df["momentum_3"] = df["close"].pct_change(3)
    df["momentum_7"] = df["close"].pct_change(7)

    df["volatility_7"] = df["ret"].rolling(7).std()
    df["volatility_21"] = df["ret"].rolling(21).std()

    df["trend"] = df["close"] - df["ema_12"]
    df["range_ratio"] = df["price_range"] / df["close"]
    df["volatility_ratio"] = df["volatility_7"] / df["volatility_21"]

    sentiment = get_market_sentiment(coin)
    df["sentiment_score"] = sentiment

    return df.dropna()


# ================= LIVE =================
@app.route("/live/<coin>")
def live_coin(coin):

    try:
        symbol = coin.upper() + "USDT"

        k = requests.get(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=1"
        ).json()[0]

        return jsonify({
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= PREDICT =================
@app.route("/predict/<coin>")
def predict_coin(coin):

    try:
        symbol = coin.upper() + "USDT"

        candles = requests.get(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=120"
        ).json()

        df = pd.DataFrame(candles)
        df = df.iloc[:, 0:6]
        df.columns = ["time","open","high","low","close","volume"]

        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)

        df = build_features(df, coin)

        X = df[feature_cols]

        X_input = scaler.transform(X) if use_scaler else X

        probs = model.predict_proba(X_input)

        risk_map = {0:"LOW",1:"MED",2:"HIGH"}
        risk = risk_map[np.argmax(probs[-1])]

        trade = "BUY" if risk=="LOW" else "SELL" if risk=="HIGH" else "HOLD"

        return jsonify({
            "prediction": risk,
            "probabilities": probs[-1].tolist(),
            "trade": trade,
            "sentiment": float(df["sentiment_score"].iloc[-1])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= HISTORY =================
@app.route("/history/<coin>")
def history_coin(coin):

    try:
        symbol = coin.upper() + "USDT"

        candles = requests.get(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=120"
        ).json()

        df = pd.DataFrame(candles)
        df = df.iloc[:, 0:6]
        df.columns = ["time","open","high","low","close","volume"]

        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)

        df["date"] = pd.to_datetime(df["time"], unit="ms").dt.date

        df = build_features(df, coin)

        X = df[feature_cols]
        X_input = scaler.transform(X) if use_scaler else X

        probs = model.predict_proba(X_input)
        preds = np.argmax(probs, axis=1)

        risk_map = {0:"LOW",1:"MED",2:"HIGH"}

        rows = []

        for i in range(-30,0):
            rows.append({
                "date": str(df.iloc[i]["date"]),
                "open": float(df.iloc[i]["open"]),
                "high": float(df.iloc[i]["high"]),
                "close": float(df.iloc[i]["close"]),
                "prediction": risk_map[preds[i]]
            })

        return jsonify(rows[::-1])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ⭐⭐⭐ UPDATED SENTIMENT ROUTE (ONLY SCORE)
@app.route("/sentiment/<coin>")
def sentiment_coin(coin):

    s = get_market_sentiment(coin)

    return jsonify({
        "coin": coin.upper(),
        "sentiment_score": float(s)
    })


@app.route("/metrics")
def metrics():
    return jsonify({
        "macro_f1": 0.55,
        "auc": 0.65
    })


@app.route("/")
def home():
    return "AI CRYPTO API RUNNING 🚀"


if __name__ == "__main__":
    app.run(debug=True)