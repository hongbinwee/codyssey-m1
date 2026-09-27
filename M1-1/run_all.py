import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for script in ["scripts/prepare_data.py", "scripts/analyze.py"]:
    print(f"\n>>> {script}")
    subprocess.run([sys.executable, str(ROOT / script)], check=True, cwd=ROOT)

print("\n완료: 공식 원본에서 처리 데이터와 그래프를 재생성했습니다.")
