from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
EXPECTED_FILE = "서울교통공사_역별 일별 시간대별 승하차인원_20251231.csv"
TIME_COLS = (["06시이전"] +
             [f"{hour:02d}-{hour + 1:02d}시간대" for hour in range(6, 24)] +
             ["24시이후"])
META_COLS = ["수송일자", "호선", "역번호", "역명", "승하차구분"]

def read_csv_flexible(path: Path) -> pd.DataFrame:
    errors = []
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception as e:
            errors.append((enc, str(e)))
    raise RuntimeError(f"CSV 인코딩을 판별하지 못했습니다: {errors}")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
    return df

def main():
    raw_path = RAW_DIR / EXPECTED_FILE
    if not raw_path.exists():
        raise FileNotFoundError(
            f"공식 2025 원본 CSV가 없습니다: {raw_path}\n"
            "https://data.seoul.go.kr/dataList/OA-12921/F/1/datasetView.do"
        )

    print(f"[1/5] 원본 읽기: {raw_path.name}")
    raw = normalize_columns(read_csv_flexible(raw_path))
    missing_cols = [col for col in META_COLS + TIME_COLS if col not in raw.columns]
    if missing_cols:
        raise ValueError(f"공식 CSV 필수 컬럼이 없습니다: {missing_cols}")
    if raw.columns.duplicated().any():
        raise ValueError("원본 CSV에 중복 컬럼명이 있습니다.")

    blank_rows = int(raw.isna().all(axis=1).sum())
    raw = raw.dropna(how="all").copy()
    print(f"[2/5] 완전 빈 행 제외: {blank_rows}개; 유효 행: {len(raw):,}개")
    if raw.empty or raw[META_COLS].isna().any().any():
        raise ValueError("데이터 행의 날짜·호선·역 정보·승하차구분에 결측치가 있습니다.")

    raw["수송일자"] = pd.to_datetime(raw["수송일자"], errors="coerce")
    if raw["수송일자"].isna().any():
        raise ValueError("날짜 변환에 실패한 데이터 행이 있습니다.")
    expected_dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    observed_dates = pd.DatetimeIndex(raw["수송일자"].unique()).sort_values()
    if not observed_dates.equals(expected_dates):
        raise ValueError("2025년 날짜가 누락되었거나 다른 연도/시간 값이 섞여 있습니다.")
    if set(raw["호선"].unique()) != {f"{n}호선" for n in range(1, 9)}:
        raise ValueError("호선 값이 서울교통공사 1~8호선 범위와 다릅니다.")
    if set(raw["승하차구분"].unique()) != {"승차", "하차"}:
        raise ValueError("승하차구분 값은 승차와 하차여야 합니다.")

    key_cols = ["수송일자", "호선", "역번호", "승하차구분"]
    if raw.duplicated(key_cols).any():
        raise ValueError("날짜·호선·역번호·승하차구분 조합이 중복되었습니다.")
    station_cols = ["호선", "역번호"]
    station_count = len(raw[station_cols].drop_duplicates())
    daily_station_count = raw.groupby("수송일자").apply(
        lambda group: len(group[station_cols].drop_duplicates()), include_groups=False
    )
    if not daily_station_count.eq(station_count).all():
        raise ValueError("일부 날짜에 관측된 역번호가 누락되었습니다.")
    if not raw.groupby(["수송일자"] + station_cols)["승하차구분"].nunique().eq(2).all():
        raise ValueError("일부 날짜·역에 승차 또는 하차 행이 없습니다.")

    numbers = raw[TIME_COLS].apply(pd.to_numeric, errors="coerce")
    if numbers.isna().any().any():
        raise ValueError("시간대 인원에 결측치 또는 숫자 변환 실패 값이 있습니다.")
    if (numbers < 0).any().any() or (numbers.mod(1) != 0).any().any():
        raise ValueError("시간대 인원에 음수 또는 정수가 아닌 값이 있습니다.")
    raw["row_total"] = numbers.astype("int64").sum(axis=1)
    print(f"[3/5] 시간대 {len(TIME_COLS)}개, 매일 역 {station_count}개, 승차·하차 모두 확인")

    daily = (
        raw.groupby("수송일자", as_index=False)["row_total"]
        .sum()
        .rename(columns={"수송일자": "date", "row_total": "passengers"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    if daily["passengers"].isna().any() or (daily["passengers"] <= 0).any():
        raise ValueError("일별 승객 수에 결측치 또는 0 이하 값이 있습니다.")

    daily["weekday_num"] = daily["date"].dt.weekday
    daily["weekday"] = daily["weekday_num"].map(
        {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}
    )
    daily["ma7"] = daily["passengers"].rolling(7).mean()
    daily["ma30"] = daily["passengers"].rolling(30).mean()
    daily["change_rate_pct"] = daily["passengers"].pct_change() * 100
    daily["month"] = daily["date"].dt.month

    out = OUT_DIR / "seoul_metro_daily_2025.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out, index=False, encoding="utf-8-sig")

    print(f"[4/5] 처리 데이터 저장: {out}")
    print(f"[5/5] 완료: {len(daily)}일, 일평균 {daily['passengers'].mean():,.0f}명")

if __name__ == "__main__":
    main()
