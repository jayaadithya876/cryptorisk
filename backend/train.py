import pandas as pd
import numpy as np
import pickle

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, classification_report
from sklearn.model_selection import train_test_split

from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

# =========================================================
# 1️⃣ LOAD DATA
# =========================================================

df = pd.read_csv("btcusd_1-min_data.csv")

df["date"] = pd.to_datetime(df["Timestamp"], unit="s").dt.floor("D")

df = df.rename(columns={
    "Open":"open","High":"high","Low":"low",
    "Close":"close","Volume":"volume"
})

df = df.groupby("date").agg({
    "open":"first",
    "high":"max",
    "low":"min",
    "close":"last",
    "volume":"sum"
}).dropna().reset_index()

# =========================================================
# 2️⃣ FEATURES (STRONG)
# =========================================================

def add_features(df):
    df = df.copy()

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

    # 🔥 STRONG FEATURES
    df["price_range"] = df["high"] - df["low"]
    df["body"] = abs(df["close"] - df["open"])

    df["momentum_3"] = df["close"].pct_change(3)
    df["momentum_7"] = df["close"].pct_change(7)

    df["volatility_7"] = df["ret"].rolling(7).std()
    df["volatility_21"] = df["ret"].rolling(21).std()

    # 🔥 EXTRA FEATURES (IMPORTANT)
    df["trend"] = df["close"] - df["ema_12"]
    df["range_ratio"] = df["price_range"] / df["close"]
    df["volatility_ratio"] = df["volatility_7"] / df["volatility_21"]

    return df

df = add_features(df)

# =========================================================
# 3️⃣ LABELS (BETTER)
# =========================================================

df["future_rv"] = df["ret"].rolling(14).std().shift(-14)
df = df.dropna()

low = df["future_rv"].quantile(0.25)
high = df["future_rv"].quantile(0.75)

def label(x):
    if x <= low:
        return 0   # LOW
    elif x >= high:
        return 2   # HIGH
    else:
        return 1   # MED

df["risk"] = df["future_rv"].apply(label)

print("\nLabel Distribution:")
print(df["risk"].value_counts())

# =========================================================
# 4️⃣ CLEAN DATA (CRITICAL FIX)
# =========================================================

df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna()

# =========================================================
# 5️⃣ SPLIT (STRATIFIED)
# =========================================================

drop_cols = ["date","ret","future_rv","risk"]
X_cols = [c for c in df.columns if c not in drop_cols]

X = df[X_cols]
y = df["risk"]

X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
)

# =========================================================
# 6️⃣ BALANCE DATA
# =========================================================

smote = SMOTE(random_state=42)
X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)

print("\nBalanced Distribution:")
print(pd.Series(y_train_bal).value_counts())

# =========================================================
# 7️⃣ TRAIN (XGBOOST 🔥)
# =========================================================

print("\nTraining XGBoost...")

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="mlogloss",
    random_state=42
)

model.fit(X_train_bal, y_train_bal)

# =========================================================
# 8️⃣ EVALUATION
# =========================================================

y_val_pred = model.predict(X_val)

print("\nValidation F1:", f1_score(y_val, y_val_pred, average="macro"))

y_test_pred = model.predict(X_test)

print("\nTEST F1:", f1_score(y_test, y_test_pred, average="macro"))
print(classification_report(y_test, y_test_pred))

# =========================================================
# 9️⃣ SAVE
# =========================================================

pickle.dump(model, open("best_model.pkl","wb"))
pickle.dump(StandardScaler().fit(X_train_bal), open("scaler.pkl","wb"))
pickle.dump(X_cols, open("features.pkl","wb"))
pickle.dump(False, open("use_scaler.pkl","wb"))  # XGB doesn't need scaling

print("\n✅ Model Saved Successfully!")