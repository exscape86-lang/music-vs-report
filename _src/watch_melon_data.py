"""
GuySome 멜론 데이터 풀리는 순간 감지 → 즉시 collect + build + push.

매 10분마다 schtask로 실행. 두 곡의 GuySome melon endpoint 4개를 가볍게 GET 해서
이전 상태(500/0rows)와 비교. 200/rows>0 또는 row 증가 감지 시 트리거.

수집 트리거 우선순위:
1. 이 사랑 (D+1, 멜론 풀리길 대기 중)  → collect_woody_isarang.py 호출
2. 그 다음 run_vs_hourly.ps1 호출 (build + push)

평소엔 변화 없으면 조용히 종료 (raw 저장도 안 함).
"""
import json, sys, datetime as dt, subprocess
from pathlib import Path
import requests

BASE = Path(r'C:\Users\wizsr\music_data_vs_compare')
WD_COLLECT = Path(r'C:\Users\wizsr\music_data_woody_isarang_20260524\collect_woody_isarang.py')
TH_COLLECT = Path(r'C:\Users\wizsr\music_data_tophyun_kkamananggyong\collect_tophyun_kkamananggyong.py')
STATE_FILE = BASE / 'watch_state.json'
LOG_DIR = BASE / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f'watch_{dt.datetime.now().strftime("%Y%m%d")}.log'

# 두 곡 GuySome 멜론 endpoint (이사랑 위주, 떠나가요도 새 데이터 풀릴 가능성 모니터)
ENDPOINTS = [
    ('wd_melon_daily',  'https://xn--o39an51b2re.com/chart/melon/daily/trend/graph?songIds=602067978',           True),   # 이사랑 멜론 일별
    ('wd_melon_stream', 'https://xn--o39an51b2re.com/chart/melon/streaming-card/trend/graph?songIds=602067978', True),   # 이사랑 멜론 스트리밍 카드
    ('tt_melon_daily',  'https://xn--o39an51b2re.com/chart/melon/daily/trend/graph?songIds=601831572',           False),  # 떠나가요 (이미 풀림, row 증가만 감지)
    ('tt_melon_stream', 'https://xn--o39an51b2re.com/chart/melon/streaming-card/trend/graph?songIds=601831572', False),
    ('th_melon_daily',  'https://xn--o39an51b2re.com/chart/melon/daily/trend/graph?songIds=601786200',           False),  # 까만안경 (현재 0 rows, 차트 재진입 시 감지)
    ('th_melon_stream', 'https://xn--o39an51b2re.com/chart/melon/streaming-card/trend/graph?songIds=601786200', False),
]


def log(msg):
    line = f'[{dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}'
    LOG_FILE.open('a', encoding='utf-8').write(line + '\n')
    print(line)


def check(url):
    try:
        r = requests.get(url, timeout=12)
        status = r.status_code
        rows = 0
        if status == 200:
            try:
                d = r.json()
                if isinstance(d, dict):
                    # GuySome은 보통 {chart, timeUnit, columns, rows: [...]} 구조
                    rows = len(d.get('rows') or d.get('data') or [])
                elif isinstance(d, list):
                    rows = len(d)
            except Exception:
                # JSON 파싱 실패해도 200이면 텍스트 길이로 대체 판단
                rows = 1 if len(r.text) > 100 else 0
        return status, rows
    except Exception as e:
        log(f'check failed {url}: {e}')
        return 0, 0


def main():
    log('=== watch start ===')
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass

    new_state = {}
    triggers = []  # 변화 이유 리스트

    for key, url, primary in ENDPOINTS:
        status, rows = check(url)
        new_state[key] = {'status': status, 'rows': rows, 'checked_at': dt.datetime.now().isoformat()}
        prev = state.get(key, {})
        prev_status = prev.get('status', 0)
        prev_rows = prev.get('rows', 0)

        # 트리거 조건 1: 500/0 → 200/rows>0 (데이터 처음 풀린 순간)
        if prev_status != 200 and status == 200 and rows > 0:
            triggers.append(f'{key} 데이터 풀림 ({prev_status}/{prev_rows} → 200/{rows})')
        # 트리거 조건 2: 200/N → 200/N+ (rows 증가)
        elif status == 200 and rows > prev_rows:
            triggers.append(f'{key} 행 증가 ({prev_rows} → {rows})')

        log(f'{key}: {status}/{rows} (prev {prev_status}/{prev_rows})')

    STATE_FILE.write_text(json.dumps(new_state, ensure_ascii=False, indent=2), encoding='utf-8')

    if not triggers:
        log('변화 없음 → 종료')
        return

    log(f'트리거 발동 ({len(triggers)}건): ' + ' | '.join(triggers))

    # 1a. 이 사랑 collect (멜론 raw 저장)
    log('[STEP 1a] collect_woody_isarang.py')
    cp = subprocess.run(['python', str(WD_COLLECT)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    log(f'wd collect exit={cp.returncode}')
    if cp.stdout:
        log('wd collect stdout: ' + cp.stdout[-300:])

    # 1b. 까만안경 collect
    if TH_COLLECT.exists():
        log('[STEP 1b] collect_tophyun_kkamananggyong.py')
        cp = subprocess.run(['python', str(TH_COLLECT)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        log(f'th collect exit={cp.returncode}')
        if cp.stdout:
            log('th collect stdout: ' + cp.stdout[-300:])

    # 2. build + push
    log('[STEP 2] run_vs_hourly.ps1')
    cp = subprocess.run([
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', str(BASE / 'run_vs_hourly.ps1'),
    ], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    log(f'run_vs_hourly exit={cp.returncode}')
    if cp.stdout:
        log('run_vs_hourly stdout: ' + cp.stdout[-400:])

    log('=== watch end (triggered) ===')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f'FATAL: {e}')
        sys.exit(1)
