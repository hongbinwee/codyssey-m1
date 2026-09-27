# Processed data

`python scripts/prepare_data.py` 실행 시 아래 파일이 생성됩니다.
원본의 완전 빈 행 134개를 제외하고 2025년 365일을 검증한 뒤 저장합니다.

```text
seoul_metro_daily_2025.csv
```

컬럼:
- `date`: 날짜
- `passengers`: 해당 날짜의 전체 승차+하차 인원
- `weekday_num`: 월=0 ... 일=6
- `weekday`: Mon ... Sun
- `ma7`: 7일 이동평균
- `ma30`: 30일 이동평균
- `change_rate_pct`: 전일 대비 변화율(%)
- `month`: 월

`ma7`의 첫 6행, `ma30`의 첫 29행, `change_rate_pct`의 첫 행은
계산 창이 아직 채워지지 않아 비어 있습니다. `date`와 `passengers`의 결측은 허용하지 않습니다.

공식 원본의 라이선스와 재배포 조건을 존중하기 위해 이 폴더에는 생성 결과를 기본 포함하지 않습니다.
