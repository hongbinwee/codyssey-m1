import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title="서울 지하철 2025 트렌드", layout="wide")
st.title("서울 지하철 2025 이용량 트렌드 분석")
st.caption("서울교통공사 관할 1~8호선 · 공식 OA-12921 원본 기반")

DATA = Path(__file__).resolve().parent / "data" / "processed" / "seoul_metro_daily_2025.csv"
if not DATA.exists():
    st.error("처리 데이터가 없습니다.")
    st.code("python scripts/prepare_data.py")
    st.info("공식 원본 CSV를 data/raw/ 폴더에 넣은 뒤 위 명령을 실행하세요.")
    st.stop()

df = pd.read_csv(DATA, parse_dates=["date"])

selected = st.date_input(
    "분석 기간",
    value=(df["date"].min().date(), df["date"].max().date()),
    min_value=df["date"].min().date(),
    max_value=df["date"].max().date(),
)
if not isinstance(selected, (tuple, list)) or len(selected) != 2:
    st.info("시작일과 종료일을 모두 선택하세요.")
    st.stop()
start, end = selected
view = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)].copy()
view["ma7"] = view["passengers"].rolling(7).mean()
view["ma30"] = view["passengers"].rolling(30).mean()
view["change_rate_pct"] = view["passengers"].pct_change() * 100
st.caption("이동평균과 전일 대비 변화율은 선택한 기간 안에서 다시 계산합니다.")

c1, c2, c3 = st.columns(3)
c1.metric("평균 일 이용량", f"{view['passengers'].mean():,.0f}명")
c2.metric("최대 일 이용량", f"{view['passengers'].max():,}명")
c3.metric("데이터 포인트", f"{len(view)}일")

st.subheader("일별 이용량과 이동평균")
fig, ax = plt.subplots(figsize=(12,4))
ax.plot(view["date"], view["passengers"]/1e6, alpha=.4, label="Daily")
ax.plot(view["date"], view["ma7"]/1e6, label="7-day MA")
ax.plot(view["date"], view["ma30"]/1e6, label="30-day MA")
ax.set_ylabel("Passengers (millions)")
ax.legend()
st.pyplot(fig)
plt.close(fig)

st.subheader("요일별 평균")
order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
weekday = view.groupby("weekday")["passengers"].mean().reindex(order)
fig, ax = plt.subplots(figsize=(8,4))
ax.bar(weekday.index, weekday.values/1e6)
ax.set_ylabel("Passengers (millions)")
st.pyplot(fig)
plt.close(fig)

st.subheader("전일 대비 변화율")
fig, ax = plt.subplots(figsize=(12,4))
ax.plot(view["date"], view["change_rate_pct"])
ax.axhline(0, linewidth=.8)
ax.set_ylabel("Change (%)")
st.pyplot(fig)
plt.close(fig)

st.subheader("변화율이 큰 날짜")
top = (
    view.dropna(subset=["change_rate_pct"])
        .assign(abs_change=lambda x: x["change_rate_pct"].abs())
        .nlargest(10, "abs_change")
)
st.dataframe(top[["date","passengers","change_rate_pct"]], width="stretch")

st.info("급격한 변화의 원인은 본 데이터만으로 확정하지 않습니다. 외부 달력·날씨·행사 자료가 추가 검증에 필요합니다.")
