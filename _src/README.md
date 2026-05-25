# Source

이 폴더는 빌더/수집기/자동화 스크립트 보존 백업입니다. Pages 빌드(`/index.html`)에는 영향 없음.

## 파일

| 파일 | 역할 |
|---|---|
| `build_vs_report.py` | VS 리포트 HTML 빌더 (3곡 토글 지원) |
| `run_vs_hourly.ps1` | 매시간 build + git push 자동화 |
| `watch_melon_data.py` | 10분 polling, GuySome 멜론 변화 감지 시 즉시 collect+build+push |
| `collect_woody_isarang.py` | 우디 - 이 사랑 데이터 수집기 |
| `collect_tophyun_kkamananggyong.py` | 탑현 - 까만안경 데이터 수집기 |
| `assets/hero_bg.svg` | 추상 음악 차트 라인 + 별 입자 hero 배경 |

## 절대 경로

스크립트 안에 절대 경로 (`C:\Users\wizsr\...`) 박혀있음. 다른 머신/사용자에서 사용 시 경로 치환 필요.

## Task Scheduler 잡

- `Music_VS_Report_Hourly` — 매시 :10
- `Woody_Isarang_Hourly_Collect` — 매시 :05
- `Tophyun_Kkamananggyong_Hourly_Collect` — 매시 :55
- `Melon_Data_Watcher` — 매 10분

## 데이터 폴더 (이 repo에 포함되지 않음)

- `C:\Users\wizsr\music_data_13345046_tteonagayo\` — 떠나가요 정적
- `C:\Users\wizsr\music_data_woody_isarang_20260524\` — 이 사랑 라이브
- `C:\Users\wizsr\music_data_tophyun_kkamananggyong\` — 까만안경 라이브
