from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "seoul_metro_daily_2025.csv"
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)

if not DATA.exists():
    raise FileNotFoundError(
        "처리 데이터가 없습니다. 먼저 `python scripts/prepare_data.py`를 실행하세요."
    )

df = pd.read_csv(DATA, parse_dates=["date"])
expected_dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
if not pd.DatetimeIndex(df["date"]).equals(expected_dates):
    raise ValueError("처리 데이터의 날짜가 2025년 365일 순서와 일치하지 않습니다.")
if df["passengers"].isna().any() or (df["passengers"] <= 0).any():
    raise ValueError("처리 데이터의 일별 승하차 합계가 비어 있거나 0 이하입니다.")
df["ma7"] = df["passengers"].rolling(7).mean()
df["ma30"] = df["passengers"].rolling(30).mean()
df["change_rate_pct"] = df["passengers"].pct_change() * 100

weekday_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
weekday_mean = df.groupby("weekday")["passengers"].mean().reindex(weekday_order)
monthly = df.groupby("month")["passengers"].mean()

plt.figure(figsize=(12,5))
plt.plot(df["date"], df["passengers"]/1e6, alpha=.4, linewidth=1, label="Daily")
plt.plot(df["date"], df["ma7"]/1e6, linewidth=1.6, label="7-day MA")
plt.plot(df["date"], df["ma30"]/1e6, linewidth=2.1, label="30-day MA")
plt.title("Seoul Metro Daily Ridership, 2025")
plt.ylabel("Passengers (millions)")
plt.xlabel("Date")
plt.legend()
plt.tight_layout()
plt.savefig(IMG/"01_daily_trend.png", dpi=180)
plt.close()

plt.figure(figsize=(8,5))
plt.bar(weekday_mean.index, weekday_mean.values/1e6)
plt.title("Average Ridership by Day of Week, 2025")
plt.ylabel("Passengers (millions)")
plt.xlabel("Day of week")
plt.tight_layout()
plt.savefig(IMG/"02_weekday_pattern.png", dpi=180)
plt.close()

plt.figure(figsize=(12,5))
plt.plot(df["date"], df["change_rate_pct"], linewidth=.9)
plt.axhline(0, linewidth=.8)
plt.title("Day-over-Day Ridership Change, 2025")
plt.ylabel("Change (%)")
plt.xlabel("Date")
plt.tight_layout()
plt.savefig(IMG/"03_change_rate.png", dpi=180)
plt.close()

plt.figure(figsize=(9,5))
plt.bar(monthly.index.astype(str), monthly.values/1e6)
plt.title("Average Daily Ridership by Month, 2025")
plt.ylabel("Passengers (millions)")
plt.xlabel("Month")
plt.tight_layout()
plt.savefig(IMG/"04_monthly_average.png", dpi=180)
plt.close()

weekday_avg = df[df["weekday_num"] < 5]["passengers"].mean()
weekend_avg = df[df["weekday_num"] >= 5]["passengers"].mean()
peak = df.loc[df["passengers"].idxmax()]
low = df.loc[df["passengers"].idxmin()]

print("=== 분석 요약 ===")
print(f"일평균: {df['passengers'].mean():,.0f}명")
print(f"중앙값: {df['passengers'].median():,.0f}명")
print(f"표준편차(365일 모집단): {df['passengers'].std(ddof=0):,.0f}명")
print(f"평일 평균: {weekday_avg:,.0f}명")
print(f"주말 평균: {weekend_avg:,.0f}명")
print(f"평일/주말 차이: {(weekday_avg/weekend_avg-1)*100:.1f}%")
print(f"최대: {peak['date'].date()} {int(peak['passengers']):,}명")
print(f"최소: {low['date'].date()} {int(low['passengers']):,}명")
print("요일별 평균:")
for day, value in weekday_mean.items():
    print(f"  {day}: {value:,.0f}명")
print("월별 평균:")
for month, value in monthly.items():
    print(f"  {month:02d}월: {value:,.0f}명")
print("절대 변화율 상위 5일:")
for _, row in df.dropna(subset=["change_rate_pct"]).assign(
    abs_change=lambda data: data["change_rate_pct"].abs()
).nlargest(5, "abs_change").iterrows():
    print(f"  {row['date'].date()}: {row['change_rate_pct']:+.1f}% ({int(row['passengers']):,}명)")
