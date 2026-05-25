"""
VS 비교 리포트 v3 — 3곡 토글 (이사랑 고정 / 떠나가요 ↔ 까만안경 스왑)

황PD 피드백 (2026-05-25):
- 블루 사이드(이사랑) 고정. 핑크 사이드만 떠나가요/까만안경 클릭 토글.
- CSS-only 라디오 + 두 매칭 pane.
- 가운데 3지표 다수결 화살표 + 점수 + ★ 별표 + datetime 메인+보조(↳) 양식 그대로.
"""
import csv, json, html, base64, requests, datetime as dt
from pathlib import Path

# ---------- 경로 ----------
OUT = Path(r'C:\Users\wizsr\music_data_vs_compare')
REPO = OUT / 'repo'
OUT.mkdir(exist_ok=True); REPO.mkdir(exist_ok=True)

# ---------- 메타 (3곡) ----------
TT = {
    'key': 'tt',
    'title': '떠나가요, 떠나지마요',
    'subtitle': '시대를 초월한 마음',
    'short': '떠나가요',
    'artist': '순순희(기태), 백예슬',
    'release': dt.datetime(2026, 4, 26, 18, 0),
    'color': '#ff7ab6', 'accent': '#ff3d8a',
    'cover_url': 'https://cdn.guyso.me/image/album/melon/13345046.jpg',
    'data_dir': Path(r'C:\Users\wizsr\music_data_13345046_tteonagayo'),
    'has_melon_daily': True,
    'has_youtube': True,
    'genie_csv': 'genie_realtime_hourly_listener_play.csv',
}
TH = {
    'key': 'th',
    'title': '까만안경',
    'subtitle': '',
    'short': '까만안경',
    'artist': '탑현',
    'release': dt.datetime(2026, 4, 16, 18, 0),
    'color': '#ff7ab6', 'accent': '#ff3d8a',  # 핑크 (TT와 동일 사이드)
    'cover_url': 'https://cdn.guyso.me/image/album/melon/13331510.jpg',
    'data_dir': Path(r'C:\Users\wizsr\music_data_tophyun_kkamananggyong'),
    'has_melon_daily': False,  # daily 0 rows
    'has_youtube': False,
    'genie_csv': 'genie_realtime_hourly_listener_play.csv',
}
WD = {
    'key': 'wd',
    'title': '이 사랑',
    'subtitle': 'Natural Ver',
    'short': '이 사랑',
    'artist': '우디 (Woody)',
    'release': dt.datetime(2026, 5, 24, 18, 0),
    'color': '#6ea8fe', 'accent': '#3d7dff',
    'cover_url': 'https://cdn.guyso.me/image/album/melon/13611730.jpg',
    'data_dir': Path(r'C:\Users\wizsr\music_data_woody_isarang_20260524'),
    'has_melon_daily': False,
    'has_youtube': False,
    'genie_csv': None,  # snapshots_hourly.csv 경로
}

# ---------- 자산 로딩 ----------
def fetch_cover_b64(url):
    try:
        r = requests.get(url, timeout=15)
        if r.ok:
            return 'data:image/jpeg;base64,' + base64.b64encode(r.content).decode('ascii')
    except Exception:
        pass
    return ''

for song in (TT, TH, WD):
    song['cover_b64'] = fetch_cover_b64(song['cover_url'])

_hero_svg = OUT / 'assets' / 'hero_bg.svg'
HERO_BG_B64 = ''
if _hero_svg.exists():
    HERO_BG_B64 = 'data:image/svg+xml;base64,' + base64.b64encode(_hero_svg.read_bytes()).decode('ascii')

def fetch_favicon_b64(domain):
    try:
        r = requests.get(f'https://www.google.com/s2/favicons?domain={domain}&sz=64', timeout=8)
        if r.ok:
            return 'data:image/png;base64,' + base64.b64encode(r.content).decode('ascii')
    except Exception:
        pass
    return ''

FAVICON = {
    'melon': fetch_favicon_b64('melon.com'),
    'genie': fetch_favicon_b64('genie.co.kr'),
    'youtube': fetch_favicon_b64('youtube.com'),
}

def src_chip(platform, label=None):
    labels = {'melon': '멜론', 'genie': '지니', 'youtube': '유튜브'}
    txt = label or labels.get(platform, platform.upper())
    fav = FAVICON.get(platform, '')
    img = f'<img class="src-chip-fav" src="{fav}" alt="">' if fav else ''
    return f'<span class="src-chip src-{platform}">{img}<span class="src-chip-txt">{esc(txt)}</span></span>'

# ---------- 유틸 ----------
def read_csv(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def num(v):
    if v in (None, '', 'None'): return None
    try: return float(str(v))
    except: return None

def fmt(n):
    if n is None: return '-'
    n = float(n)
    if n != n: return '-'
    return f'{int(n):,}' if abs(n - int(n)) < 1e-9 else f'{n:,.2f}'

def band(n):
    if n is None: return 'muted'
    if n >= 2.6: return 'hot'
    if n >= 2.0: return 'high'
    if n >= 1.8: return 'mid'
    return 'low'

def esc(s): return html.escape(str(s) if s is not None else '')

def fmt_dt_short(dtobj):
    if dtobj is None: return '-'
    return dtobj.strftime('%m/%d %H:%M')

def fmt_dt_full(dtobj):
    if dtobj is None: return '-'
    return dtobj.strftime('%Y-%m-%d %H:%M KST')

def fmt_d_short(dateobj):
    if dateobj is None: return '-'
    return dateobj.strftime('%m/%d')

# ---------- 데이터 로딩 ----------
def load_genie_hourly_direct(song):
    """TT/TH 패턴: genie_realtime_hourly_listener_play.csv 직접 로딩"""
    rows = read_csv(song['data_dir'] / song['genie_csv'])
    for r in rows:
        t = dt.datetime.fromisoformat(r['time'])
        r['_dt'] = t
        r['_hours_since_release'] = (t - song['release']).total_seconds() / 3600
        r['_listeners_cum'] = num(r.get('count1'))
        r['_plays_cum'] = num(r.get('count2'))
        r['_listener_delta'] = num(r.get('count1Diff'))
        r['_play_delta'] = num(r.get('count2Diff'))
        r['_rank'] = num(r.get('ranking'))
        # 첫 행 또는 단발 행: count1Diff 비어있으면 누적값을 delta로 (발매 직후만)
        if r['_listener_delta'] is None and r['_hours_since_release'] <= 1.1:
            r['_listener_delta'] = r['_listeners_cum']
            r['_play_delta'] = r['_plays_cum']
        r['_cum_mult'] = (r['_plays_cum'] / r['_listeners_cum']) if r['_listeners_cum'] else None
        r['_hour_mult'] = (r['_play_delta'] / r['_listener_delta']) if (r['_listener_delta'] and r['_listener_delta'] > 0) else None
    return rows

def load_genie_hourly_snapshots(song):
    """WD 패턴: snapshots_hourly.csv → genie_latest_* 컬럼 추출 + 시간 dedup + delta 계산"""
    raw = read_csv(song['data_dir'] / 'snapshots_hourly.csv')
    dedup = {}
    for r in raw:
        t = r.get('genie_latest_time')
        if not t: continue
        dedup[t] = r
    rows = sorted(dedup.values(), key=lambda r: r['genie_latest_time'])
    for i, r in enumerate(rows):
        t = dt.datetime.fromisoformat(r['genie_latest_time'])
        r['_dt'] = t
        r['_hours_since_release'] = (t - song['release']).total_seconds() / 3600
        r['_listeners_cum'] = num(r.get('genie_latest_listeners'))
        r['_plays_cum'] = num(r.get('genie_latest_plays'))
        r['_rank'] = num(r.get('genie_latest_rank'))
        r['_cum_mult'] = num(r.get('genie_latest_repeat_multiplier'))
        if i == 0:
            r['_listener_delta'] = r['_listeners_cum']
            r['_play_delta'] = r['_plays_cum']
        else:
            prev = rows[i - 1]
            ld = (r['_listeners_cum'] or 0) - (prev['_listeners_cum'] or 0)
            pd_ = (r['_plays_cum'] or 0) - (prev['_plays_cum'] or 0)
            r['_listener_delta'] = ld if ld >= 0 else None
            r['_play_delta'] = pd_ if pd_ >= 0 else None
        r['_hour_mult'] = (r['_play_delta'] / r['_listener_delta']) if (r['_listener_delta'] and r['_listener_delta'] > 0) else None
    return rows

# 곡별 시간 데이터
TT['genie_hourly'] = load_genie_hourly_direct(TT)
TH['genie_hourly'] = load_genie_hourly_direct(TH)
WD['genie_hourly'] = load_genie_hourly_snapshots(WD)

# 떠나가요 멜론 일별 + 유튜브 (단독)
tt_melon_stream = read_csv(TT['data_dir'] / 'melon_streaming_card_daily.csv')
tt_melon_users = read_csv(TT['data_dir'] / 'melon_daily_users.csv')
tt_youtube = read_csv(TT['data_dir'] / 'youtube_current_search.csv')

for r in tt_melon_stream:
    d = dt.date.fromisoformat(r['date'])
    r['_date'] = d
    r['_days_since_release'] = (d - TT['release'].date()).days
    r['_listeners_cum'] = num(r.get('count1'))
    r['_plays_cum'] = num(r.get('count2'))
    r['_listener_delta'] = num(r.get('daily_listener_delta'))
    r['_play_delta'] = num(r.get('daily_play_delta'))
    r['_cum_mult'] = (r['_plays_cum'] / r['_listeners_cum']) if r['_listeners_cum'] else None
    r['_day_mult'] = (r['_play_delta'] / r['_listener_delta']) if (r['_listener_delta'] and r['_listener_delta'] > 0) else None

mu_map = {}
for r in tt_melon_users:
    d = dt.date.fromisoformat(r['date'])
    r['_date'] = d
    r['_days_since_release'] = (d - TT['release'].date()).days
    r['_users'] = num(r.get('count'))
    r['_users_delta'] = num(r.get('countDiff'))
    r['_rank'] = num(r.get('ranking'))
    mu_map[d] = r

tt_yt_total = sum((num(r.get('view_count')) or 0) for r in tt_youtube)
tt_yt_top = sorted(tt_youtube, key=lambda r: -(num(r.get('view_count')) or 0))[:5]

# ---------- 매칭 계산 (좌 vs 우, 같은 H+N) ----------
def by_hour(rows):
    d = {}
    for r in rows:
        h = int(round(r['_hours_since_release']))
        # H<0 또는 음수 hour_delta는 제외 (이상치)
        if h < 0: continue
        d[h] = r
    return d

def compute_match(left, right):
    """left vs right (right = 블루 기준). 반환 = {vs_rows, score, wins_l, wins_r, total_battles, recent}"""
    L_by_h = by_hour(left['genie_hourly'])
    R_by_h = by_hour(right['genie_hourly'])
    all_hours = sorted(set(L_by_h) & set(R_by_h))

    vs_rows = []
    score = {'L_l': 0, 'R_l': 0, 'L_p': 0, 'R_p': 0, 'L_m': 0, 'R_m': 0, 'L_r': 0, 'R_r': 0}
    for h in all_hours:
        l = L_by_h[h]; r = R_by_h[h]
        def winner(a, b, lower_better=False):
            if a is None or b is None: return 'na'
            if a == b: return 'tie'
            if lower_better: return 'L' if a < b else 'R'
            return 'L' if a > b else 'R'
        w_l = winner(l['_listener_delta'], r['_listener_delta'])
        w_p = winner(l['_play_delta'], r['_play_delta'])
        w_m = winner(l['_hour_mult'], r['_hour_mult'])
        w_r = winner(l['_rank'], r['_rank'], lower_better=True)
        for k, v in [('L_l', w_l == 'L'), ('R_l', w_l == 'R'),
                     ('L_p', w_p == 'L'), ('R_p', w_p == 'R'),
                     ('L_m', w_m == 'L'), ('R_m', w_m == 'R'),
                     ('L_r', w_r == 'L'), ('R_r', w_r == 'R')]:
            if v: score[k] += 1
        def diff(a, b):
            if a is None or b is None: return None
            return a - b
        vs_rows.append({
            'h': h, 'L': l, 'R': r,
            'w_l': w_l, 'w_p': w_p, 'w_m': w_m, 'w_r': w_r,
            'diff_l': diff(l['_listener_delta'], r['_listener_delta']),
            'diff_p': diff(l['_play_delta'], r['_play_delta']),
            'diff_m': diff(l['_hour_mult'], r['_hour_mult']),
            'diff_r': diff(r['_rank'], l['_rank']),
        })

    wins_L = score['L_l'] + score['L_p'] + score['L_m']
    wins_R = score['R_l'] + score['R_p'] + score['R_m']
    total = len(vs_rows) * 3
    recent = vs_rows[-1] if vs_rows else None

    return {
        'left': left, 'right': right,
        'vs_rows': vs_rows, 'score': score,
        'wins_L': wins_L, 'wins_R': wins_R,
        'total_battles': total,
        'recent': recent,
    }

MATCH_TT_WD = compute_match(TT, WD)
MATCH_TH_WD = compute_match(TH, WD)

now_kst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))

# ---------- 차트 빌더 (시간 라인) ----------
def dual_line(L_rows, R_rows, left_song, right_song, x_key, y_key, title, y_fmt='int', x_label='hour', height=300, uniq=''):
    Wd = 920; Hd = height; PAD_L = 64; PAD_R = 32; PAD_T = 28; PAD_B = 44
    pts_L = [(r[x_key], r[y_key]) for r in L_rows if r.get(y_key) is not None and r.get(x_key) is not None]
    pts_R = [(r[x_key], r[y_key]) for r in R_rows if r.get(y_key) is not None and r.get(x_key) is not None]
    if not (pts_L or pts_R): return ''
    all_x = [p[0] for p in pts_L + pts_R]
    all_y = [p[1] for p in pts_L + pts_R]
    xmin, xmax = min(all_x), max(all_x); ymin, ymax = min(all_y), max(all_y)
    if ymin > 0 and ymax / max(ymin, 1) > 5:
        ymin = 0
    xr = max(xmax - xmin, 0.1); yr = max(ymax - ymin, 0.1)
    def to_path(pts):
        out = []
        for x, y in pts:
            px = PAD_L + (x - xmin) / xr * (Wd - PAD_L - PAD_R)
            py = Hd - PAD_B - (y - ymin) / yr * (Hd - PAD_T - PAD_B)
            out.append(('M' if not out else 'L') + f'{px:.1f},{py:.1f}')
        return ' '.join(out)
    def to_area(pts):
        if not pts: return ''
        out = []
        for x, y in pts:
            px = PAD_L + (x - xmin) / xr * (Wd - PAD_L - PAD_R)
            py = Hd - PAD_B - (y - ymin) / yr * (Hd - PAD_T - PAD_B)
            out.append(('M' if not out else 'L') + f'{px:.1f},{py:.1f}')
        last_x = PAD_L + (pts[-1][0] - xmin) / xr * (Wd - PAD_L - PAD_R)
        first_x = PAD_L + (pts[0][0] - xmin) / xr * (Wd - PAD_L - PAD_R)
        out.append(f'L{last_x:.1f},{Hd-PAD_B}')
        out.append(f'L{first_x:.1f},{Hd-PAD_B}')
        out.append('Z')
        return ' '.join(out)
    def to_dots(pts, color):
        return ''.join(f'<circle cx="{PAD_L + (x - xmin) / xr * (Wd - PAD_L - PAD_R):.1f}" cy="{Hd - PAD_B - (y - ymin) / yr * (Hd - PAD_T - PAD_B):.1f}" r="3" fill="#0E1320" stroke="{color}" stroke-width="2"/>' for x, y in pts)
    path_L = to_path(pts_L); path_R = to_path(pts_R)
    area_L = to_area(pts_L); area_R = to_area(pts_R)
    grid = []
    for i in range(5):
        y = ymin + yr * i / 4
        py = Hd - PAD_B - i / 4 * (Hd - PAD_T - PAD_B)
        label = f'{y:,.2f}' if y_fmt == 'mult' else (f'{int(y/1000)}K' if abs(y) >= 1000 else f'{int(y):,}')
        grid.append(f'<line x1="{PAD_L}" y1="{py:.1f}" x2="{Wd-PAD_R}" y2="{py:.1f}" stroke="#1A2238" stroke-dasharray="2 6"/>'
                    f'<text x="{PAD_L-10}" y="{py+4:.1f}" fill="#6B7B99" font-size="11" font-weight="500" text-anchor="end" font-family="JetBrains Mono, ui-monospace, monospace">{label}</text>')
    xticks = []
    nticks = 5
    for i in range(nticks):
        x = xmin + xr * i / (nticks - 1)
        px = PAD_L + i / (nticks - 1) * (Wd - PAD_L - PAD_R)
        label = f'+{int(x)}h' if x_label == 'hour' else f'D+{int(x)}'
        xticks.append(f'<text x="{px:.1f}" y="{Hd-PAD_B+22}" fill="#6B7B99" font-size="11" font-weight="500" text-anchor="middle" font-family="JetBrains Mono, ui-monospace, monospace">{label}</text>')
    gid = f'{uniq}-{y_key}-{x_label}'
    return f'''<div class="chart-box"><div class="chart-title-row"><div class="chart-title">{esc(title)}</div><div class="chart-legend"><span class="lg-chip"><span class="lg-dot" style="background:{left_song["color"]}"></span>{esc(left_song["short"])}</span><span class="lg-chip"><span class="lg-dot" style="background:{right_song["color"]}"></span>{esc(right_song["short"])}</span></div></div>
<svg viewBox="0 0 {Wd} {Hd}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" role="img">
<defs>
<linearGradient id="gL-{gid}" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="{left_song['color']}" stop-opacity="0.22"/>
<stop offset="100%" stop-color="{left_song['color']}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="gR-{gid}" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="{right_song['color']}" stop-opacity="0.22"/>
<stop offset="100%" stop-color="{right_song['color']}" stop-opacity="0"/>
</linearGradient>
</defs>
{"".join(grid)}
{"".join(xticks)}
<path d="{area_L}" fill="url(#gL-{gid})"/>
<path d="{area_R}" fill="url(#gR-{gid})"/>
<path d="{path_L}" fill="none" stroke="{left_song["color"]}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>
<path d="{path_R}" fill="none" stroke="{right_song["color"]}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>
{to_dots(pts_L, left_song["color"])}
{to_dots(pts_R, right_song["color"])}
</svg>
</div>'''

# ---------- 렌더링 함수 ----------
def render_recent1h(match, sec_no='01'):
    """최근 1시간 증가분 VS 카드. left/right pair 자동."""
    left = match['left']; right = match['right']
    if not match['recent']:
        return f'''<section class="section"><div class="section-h"><h2 class="section-title"><span class="sec-no">{sec_no}</span>가장 최근 1시간 <span class="em">증가분</span> VS</h2></div><div class="callout"><div class="ic">·</div><div>같은 발매 후 경과시간 매칭이 없습니다 ({esc(left["short"])} ↔ {esc(right["short"])}).</div></div></section>'''
    last = match['recent']
    l_recent = last['L']; r_recent = last['R']; recent_h = last['h']
    l_win = last['w_l'] == 'L'
    r_win = last['w_l'] == 'R'
    l_card_cls = 'delta-card l-side winner' if l_win else 'delta-card l-side'
    r_card_cls = 'delta-card r-side winner' if r_win else 'delta-card r-side'

    def stat_html(listener_delta, play_delta, mult, rank):
        return f'''<div class="row">
<div class="stat"><div class="lbl">재생/시</div><div class="val">+{fmt(play_delta)}</div></div>
<div class="stat"><div class="lbl">시간배수</div><div class="val">{fmt(mult)}×</div></div>
<div class="stat"><div class="lbl">현재 순위</div><div class="val">{fmt(rank)}위</div></div>
</div>'''

    l_badge = '<span class="win-badge">WIN</span>' if l_win else ''
    r_badge = '<span class="win-badge">WIN</span>' if r_win else ''

    out = [f'''<section class="section">
<div class="section-h">
  <h2 class="section-title"><span class="sec-no">{sec_no}</span>가장 최근 매칭 1시간 <span class="em">증가분</span> VS {src_chip('genie')}</h2>
  <span class="section-sub">발매 H+{recent_h} 시점 · {esc(left["short"])} {esc(fmt_dt_short(l_recent["_dt"]))} KST vs {esc(right["short"])} {esc(fmt_dt_short(r_recent["_dt"]))} KST</span>
</div>
<div class="delta-grid" style="--l-color:{left["color"]};--r-color:{right["color"]};--l-soft:{left["color"]}1a;--r-soft:{right["color"]}1a">
<div class="{l_card_cls}">
  <div class="head"><div class="name" style="color:{left["color"]}">{esc(left["short"])} · H+{recent_h}</div>{l_badge}</div>
  <div class="when">{esc(fmt_dt_full(l_recent["_dt"]))}</div>
  <div class="big" style="color:{left["color"]}">+{fmt(l_recent["_listener_delta"])}<span class="big-unit">명/시</span></div>
  <div class="big-sub">이번 1시간 새 청취자 증가</div>
  {stat_html(l_recent["_listener_delta"], l_recent["_play_delta"], l_recent["_hour_mult"], l_recent["_rank"])}
</div>
<div class="vs-mid"><div class="glyph">VS</div></div>
<div class="{r_card_cls}">
  <div class="head"><div class="name" style="color:{right["color"]}">{esc(right["short"])} · H+{int(round(r_recent["_hours_since_release"]))}</div>{r_badge}</div>
  <div class="when">{esc(fmt_dt_full(r_recent["_dt"]))}</div>
  <div class="big" style="color:{right["color"]}">+{fmt(r_recent["_listener_delta"])}<span class="big-unit">명/시</span></div>
  <div class="big-sub">이번 1시간 새 청취자 증가</div>
  {stat_html(r_recent["_listener_delta"], r_recent["_play_delta"], r_recent["_hour_mult"], r_recent["_rank"])}
</div>
</div>''']

    if last['w_l'] in ('L', 'R'):
        win_short = left['short'] if last['w_l'] == 'L' else right['short']
        win_color = left['color'] if last['w_l'] == 'L' else right['color']
        diff_abs = abs(last['diff_l'] or 0)
        a = max(l_recent['_listener_delta'] or 0, r_recent['_listener_delta'] or 0)
        b = max(min(l_recent['_listener_delta'] or 1, r_recent['_listener_delta'] or 1), 1)
        ratio = a / b
        out.append(f'''<div class="callout">
  <div class="ic">⚡</div>
  <div><b>최근 1시간 판정:</b> <span style="color:{win_color};font-weight:800">{esc(win_short)}</span>가 청취자 <span class="num">+{fmt(diff_abs)}명</span> 더 추가 (<span class="num">{ratio:.2f}배</span> 차이) · 재생 차이 <span class="num">+{fmt(abs(last["diff_p"] or 0))}회</span></div>
</div>''')
    out.append('</section>')
    return '\n'.join(out)


def render_scoreboard_extras(match):
    """매칭 pane 내부 점수판: 좌 N : 우 M 형식"""
    left = match['left']; right = match['right']
    return f'''<div class="match-scoreboard" style="--l-color:{left["color"]};--r-color:{right["color"]}">
  <div class="ms-block ms-l">
    <div class="ms-label">{esc(left["short"])} WINS</div>
    <div class="ms-score" style="color:{left["color"]};text-shadow:0 0 60px {left["color"]}55">{match["wins_L"]}</div>
  </div>
  <div class="ms-dash">— VS —</div>
  <div class="ms-block ms-r">
    <div class="ms-label">{esc(right["short"])} WINS</div>
    <div class="ms-score" style="color:{right["color"]};text-shadow:0 0 60px {right["color"]}55">{match["wins_R"]}</div>
  </div>
  <div class="ms-note">발매 후 같은 경과시간 매칭 · 청취자/시 · 재생/시 · 시간배수 = 총 <b>{match["total_battles"]}회 대결</b> ({len(match["vs_rows"])}시간 × 3항목)</div>
</div>'''


def render_battle_table(match, sec_no='02'):
    """매시간 VS 표 (델타) — 가운데 화살표 + 우측 곡 datetime 메인 + 좌측 보조(↳)"""
    left = match['left']; right = match['right']
    parts = [f'''<section class="section">
<div class="section-h">
  <h2 class="section-title"><span class="sec-no">{sec_no}</span>매시간 <span class="em">증가분</span> 매칭 {src_chip('genie')} <span style="font-size:11.5px;color:var(--muted);font-weight:600;margin-left:4px">최신순</span></h2>
  <span class="section-sub">같은 발매 후 경과시간(H+N)에서 그 시간 청취자·재생·시간배수 비교 · 가운데 화살표 = 3지표 다수결 · 행 양쪽 옅은 컬러는 종합 승자 사이드</span>
</div>
<div class="tbl-wrap" style="--l-color:{left["color"]};--r-color:{right["color"]};--l-soft:{left["color"]}14;--r-soft:{right["color"]}14"><table>
<thead>
<tr>
<th rowspan="2" class="center">시각<br><span style="font-weight:600;color:{right["color"]};font-size:10.5px">({esc(right["short"])} 기준)</span></th>
<th colspan="3" class="center divide-r" style="color:{left["color"]}">{esc(left["short"])} 증가</th>
<th rowspan="2" class="center">청취자<br>승자</th>
<th colspan="3" class="center" style="color:{right["color"]}">{esc(right["short"])} 증가</th>
<th rowspan="2" class="center">재생<br>Δ</th>
</tr>
<tr class="subhead">
<th style="color:{left["color"]}">청취자/시</th><th style="color:{left["color"]}">재생/시</th><th class="divide-r" style="color:{left["color"]}">시간배수</th>
<th style="color:{right["color"]}">청취자/시</th><th style="color:{right["color"]}">재생/시</th><th style="color:{right["color"]}">시간배수</th>
</tr>
</thead><tbody>''']

    def vs_arrow(w_l, w_p, w_m):
        items = [w_l, w_p, w_m]
        l = items.count('L'); r = items.count('R')
        score_html = f'<span class="vs-score">{l}<span class="vs-dash">·</span>{r}</span>'
        if l == 0 and r == 0:
            return '<div class="vs-arrow"><span class="arr">·</span></div>'
        if l > r:
            cls = 'l-strong' if l == 3 else 'l-side'
            return f'<div class="vs-arrow {cls}"><span class="arr">←</span>{score_html}</div>'
        if r > l:
            cls = 'r-strong' if r == 3 else 'r-side'
            return f'<div class="vs-arrow {cls}"><span class="arr">→</span>{score_html}</div>'
        return f'<div class="vs-arrow split"><span class="arr">⇄</span>{score_html}</div>'

    def diff_pill(diff, winner_side):
        if diff is None: return '<span class="diff na">-</span>'
        sign = '+' if diff >= 0 else '-'
        if winner_side == 'L': cls = 'l-side'
        elif winner_side == 'R': cls = 'r-side'
        elif winner_side == 'tie': cls = 'tie'
        else: cls = 'na'
        val = abs(diff)
        body = f'{int(val):,}' if abs(val - int(val)) < 1e-9 else f'{val:,.2f}'
        return f'<span class="diff {cls}">{sign}{body}</span>'

    for r in reversed(match['vs_rows']):
        l_row = r['L']; r_row = r['R']
        l_l_cls = 'cell-l-win' if r['w_l'] == 'L' else 'cell-faded'
        r_l_cls = 'cell-r-win' if r['w_l'] == 'R' else 'cell-faded'
        l_p_cls = 'cell-l-win' if r['w_p'] == 'L' else 'cell-faded'
        r_p_cls = 'cell-r-win' if r['w_p'] == 'R' else 'cell-faded'
        wins_L = sum(1 for x in (r['w_l'], r['w_p'], r['w_m']) if x == 'L')
        wins_R = sum(1 for x in (r['w_l'], r['w_p'], r['w_m']) if x == 'R')
        l_side_bg = ' l-bg' if wins_L > wins_R else ''
        r_side_bg = ' r-bg' if wins_R > wins_L else ''
        sweep = '<span class="sweep-mark" title="3-0 완승">★</span>' if (wins_L == 3 or wins_R == 3) else ''
        diff_p_side = 'L' if (r['diff_p'] or 0) > 0 else ('R' if (r['diff_p'] or 0) < 0 else ('tie' if r['diff_p'] is not None else 'na'))
        parts.append(f'''<tr>
<td class="center"><div class="tcell-time">{sweep}<span class="dt">{esc(fmt_dt_short(r_row["_dt"]))}</span><span class="rel">H+{r["h"]}</span><span class="ref">{esc(fmt_dt_short(l_row["_dt"]))} {esc(left["short"])}</span></div></td>
<td class="cell-num{l_side_bg} {l_l_cls}">+{fmt(l_row["_listener_delta"])}</td>
<td class="cell-num{l_side_bg} {l_p_cls}">+{fmt(l_row["_play_delta"])}</td>
<td class="{('l-bg ' if l_side_bg else '').rstrip()} divide-r"><span class="pill-mult {band(l_row["_hour_mult"])}">{fmt(l_row["_hour_mult"])}×</span></td>
<td class="vs-cell">{vs_arrow(r["w_l"], r["w_p"], r["w_m"])}</td>
<td class="cell-num{r_side_bg} {r_l_cls}">+{fmt(r_row["_listener_delta"])}</td>
<td class="cell-num{r_side_bg} {r_p_cls}">+{fmt(r_row["_play_delta"])}</td>
<td class="{('r-bg' if r_side_bg else '').strip()}"><span class="pill-mult {band(r_row["_hour_mult"])}">{fmt(r_row["_hour_mult"])}×</span></td>
<td class="center">{diff_pill(r["diff_p"], diff_p_side)}</td>
</tr>''')
    parts.append('</tbody></table></div></section>')
    return '\n'.join(parts)


def render_charts(match, sec_no='03'):
    """48시간 라인 차트"""
    left = match['left']; right = match['right']
    L_first_48 = [r for r in left['genie_hourly'] if 0 <= r['_hours_since_release'] <= 48]
    R_first_48 = [r for r in right['genie_hourly'] if 0 <= r['_hours_since_release'] <= 48]
    uniq = f'{left["key"]}-{right["key"]}'
    out = [f'''<section class="section">
<div class="section-h">
  <h2 class="section-title"><span class="sec-no">{sec_no}</span>발매 후 48시간 <span class="em">증가분</span> 추이 {src_chip('genie')}</h2>
  <span class="section-sub">{esc(left["short"])} vs {esc(right["short"])} · 같은 H+N 정렬</span>
</div>
<div class="charts">''']
    out.append(dual_line(L_first_48, R_first_48, left, right, '_hours_since_release', '_listener_delta',
                         '시간당 청취자 증가 · 발매 후 48시간', x_label='hour', uniq=uniq))
    out.append(dual_line(L_first_48, R_first_48, left, right, '_hours_since_release', '_play_delta',
                         '시간당 재생 증가 · 발매 후 48시간', x_label='hour', uniq=uniq))
    out.append('</div></section>')
    return '\n'.join(out)


def render_tt_daily(sec_no='04'):
    """떠나가요 28일 일별 (TT 단독 — 멜론 데이터)"""
    parts = [f'''<section class="section">
<div class="section-h">
  <h2 class="section-title"><span class="sec-no">{sec_no}</span>{esc(TT["short"])} 28일 일별 증가분 {src_chip('melon')} <span style="font-size:11.5px;color:var(--muted);font-weight:600;margin-left:4px">최신순</span></h2>
  <span class="section-sub">{esc(TT["short"])} 단독 · 멜론 일별 스트리밍 카드 기준</span>
</div>
<div class="tbl-wrap"><table>
<thead><tr>
<th class="center">날짜</th><th class="center">경과</th><th>멜론 순위</th><th>일간 이용자</th>
<th style="color:var(--tt)">청취자/일</th><th style="color:var(--tt)">재생/일</th><th class="center">일간 배수</th>
<th>누적 청취자</th><th>누적 재생</th>
</tr></thead><tbody>''']
    for r in sorted(tt_melon_stream, key=lambda x: x['_date'], reverse=True):
        mu = mu_map.get(r['_date'], {})
        parts.append(f'''<tr>
<td class="center"><div class="tcell-time"><span class="dt">{esc(fmt_d_short(r["_date"]))}</span><span class="rel">{r["_date"].isoformat()}</span></div></td>
<td class="center"><span class="diff na">D+{r["_days_since_release"]}</span></td>
<td class="cell-num">{fmt(mu.get("_rank"))}위</td>
<td class="cell-num">{fmt(mu.get("_users"))}</td>
<td class="cell-num cell-l-win">+{fmt(r["_listener_delta"])}</td>
<td class="cell-num cell-l-win">+{fmt(r["_play_delta"])}</td>
<td class="center"><span class="pill-mult {band(r["_day_mult"])}">{fmt(r["_day_mult"])}×</span></td>
<td class="cell-num cell-faded">{fmt(r["_listeners_cum"])}</td>
<td class="cell-num cell-faded">{fmt(r["_plays_cum"])}</td>
</tr>''')
    parts.append('</tbody></table></div></section>')
    return '\n'.join(parts)


def render_tt_youtube(sec_no='05'):
    """떠나가요 유튜브 (TT 단독)"""
    parts = [f'''<section class="section">
<div class="section-h">
  <h2 class="section-title"><span class="sec-no">{sec_no}</span>유튜브 누적 조회수 {src_chip('youtube')}</h2>
  <span class="section-sub">{esc(TT["short"])} 검색 결과 상위 영상 (단독)</span>
</div>
<div class="delta-grid" style="grid-template-columns:repeat(3,1fr);gap:14px;--l-color:var(--tt);--r-color:var(--wd)">
<div class="mini-card l-tint"><div class="name" style="color:var(--tt)">{esc(TT["short"])} · 관련 영상</div><div class="big">{len(tt_youtube)}<span class="big-unit">개</span></div><div class="big-sub">공개 검색 기준</div></div>
<div class="mini-card l-tint"><div class="name" style="color:var(--tt)">{esc(TT["short"])} · 누적 조회수</div><div class="big">{fmt(tt_yt_total)}<span class="big-unit">회</span></div><div class="big-sub">관련 영상 전체 합</div></div>
<div class="mini-card r-tint"><div class="name" style="color:var(--wd)">{esc(WD["short"])} · 유튜브</div><div class="big" style="font-size:24px">수집 대기</div><div class="big-sub">발매 직후 별도 파이프라인</div></div>
</div>
<div class="tbl-wrap" style="margin-top:16px"><table>
<thead><tr>
<th style="text-align:left">영상 제목</th><th>조회수</th><th class="center">업로드</th><th style="text-align:left">채널</th>
</tr></thead><tbody>''']
    for y in tt_yt_top:
        upload_d = esc(y.get("upload_date") or '-')
        parts.append(f'''<tr>
<td style="text-align:left;max-width:560px;white-space:normal"><a href="{esc(y.get("webpage_url"))}" style="color:var(--ink-2);text-decoration:none;border-bottom:1px dotted var(--line-2)" target="_blank">{esc(y.get("title"))}</a></td>
<td class="cell-num">{fmt(num(y.get("view_count")))}</td>
<td class="center cell-num">{upload_d}</td>
<td style="text-align:left;color:var(--muted)">{esc(y.get("channel"))}</td>
</tr>''')
    parts.append('</tbody></table></div></section>')
    return '\n'.join(parts)


# ---------- CSS ----------
css = '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#06080F;--bg-2:#0A0E1A;--panel:#0E1320;--panel-2:#121829;--panel-3:#181F33;
  --line:#1D2740;--line-2:#283555;--ink:#F2F5FB;--ink-2:#CAD3E5;--muted:#8896B0;--muted-2:#7384A4;
  --tt:''' + TT['color'] + ''';--tt2:''' + TT['accent'] + ''';
  --th:''' + TH['color'] + ''';--th2:''' + TH['accent'] + ''';
  --wd:''' + WD['color'] + ''';--wd2:''' + WD['accent'] + ''';
  --gold:#F4C46C;--red:#FF6B7E;--green:#5FE6B0;--orange:#FFA64D;
  --mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace;
  --sans:'Pretendard Variable',Pretendard,-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Segoe UI',sans-serif;
}
*{box-sizing:border-box}html,body{margin:0;padding:0;overflow-x:hidden}
body{background:var(--bg);color:var(--ink);font:14.5px/1.55 var(--sans);letter-spacing:-.005em;
  background-image:radial-gradient(1200px 600px at 20% -10%,rgba(255,122,182,.06),transparent 60%),
                   radial-gradient(1200px 600px at 80% -10%,rgba(110,168,254,.06),transparent 60%);
  background-attachment:fixed;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;
}
.wrap{max-width:1320px;margin:auto;padding:28px 24px 120px}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}

/* TOP BAR */
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;color:var(--muted);font-size:12px}
.brand{display:flex;align-items:center;gap:10px}
.brand-mark{width:26px;height:26px;border-radius:8px;background:linear-gradient(135deg,var(--tt) 0%,var(--wd) 100%);display:grid;place-items:center;color:#0a0d14;font-weight:900;font-size:13px;letter-spacing:-.04em;box-shadow:0 0 24px rgba(255,122,182,.25),0 0 24px rgba(110,168,254,.18)}
.brand-text{font-size:13px;font-weight:700;color:var(--ink-2);letter-spacing:-.01em}
.brand-text .slash{color:var(--muted-2);margin:0 8px;font-weight:400}
.brand-text .sub{color:var(--muted);font-weight:500}
.topbar .meta{display:flex;align-items:center;gap:14px;font-family:var(--mono);font-size:11.5px}
.live-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 0 0 rgba(95,230,176,.5);animation:pulse 2.2s ease-out infinite;display:inline-block;margin-right:6px;vertical-align:middle}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(95,230,176,.55)}70%{box-shadow:0 0 0 10px rgba(95,230,176,0)}100%{box-shadow:0 0 0 0 rgba(95,230,176,0)}}

/* HERO 3-card row (왼쪽 토글 핑크 + 가운데 VS + 오른쪽 고정 블루) */
.hero{position:relative;border-radius:24px;overflow:hidden;background:
  linear-gradient(180deg,var(--panel-2) 0%,var(--panel) 100%);
  border:1px solid var(--line);
  box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 30px 80px rgba(0,0,0,.45);
}
.hero::before{content:"";position:absolute;inset:0;background:
  radial-gradient(800px 320px at 18% 0%,rgba(255,122,182,.18),transparent 60%),
  radial-gradient(800px 320px at 82% 0%,rgba(110,168,254,.18),transparent 60%);
  pointer-events:none;
}
.hero::after{content:"";position:absolute;left:50%;top:0;bottom:0;width:1px;background:linear-gradient(180deg,transparent 0%,var(--line-2) 30%,var(--line-2) 70%,transparent 100%);pointer-events:none;opacity:.6;z-index:1}
.hero-bg-art{position:absolute;inset:0;background-image:var(--hero-art);background-size:cover;background-position:center;opacity:.42;mix-blend-mode:screen;pointer-events:none;z-index:0}
.hero-fg{position:relative;z-index:2;padding:40px 44px 32px}
.hero-row{display:grid;grid-template-columns:1fr 120px 1fr;gap:32px;align-items:start}
.hero-side{padding:8px 0}
.hero-side.l{text-align:right}
.hero-side.r{text-align:left}
.cover-thumb{width:172px;height:172px;border-radius:18px;object-fit:cover;display:block;
  box-shadow:0 24px 50px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.06);
}
.hero-side.l .cover-thumb{margin-left:auto;box-shadow:0 24px 50px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.06),0 0 60px rgba(255,122,182,.22)}
.hero-side.r .cover-thumb{box-shadow:0 24px 50px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.06),0 0 60px rgba(110,168,254,.22)}
.side-tag{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin-top:18px;font-family:var(--mono)}
.hero-side.l .side-tag{background:rgba(255,122,182,.1);color:var(--tt);border:1px solid rgba(255,122,182,.25)}
.hero-side.r .side-tag{background:rgba(110,168,254,.1);color:var(--wd);border:1px solid rgba(110,168,254,.25)}
.side-tag .tag-dot{width:5px;height:5px;border-radius:50%;display:inline-block}
.hero-side.l .tag-dot{background:var(--tt)}.hero-side.r .tag-dot{background:var(--wd)}
.hero-side h1{margin:12px 0 4px;font-size:30px;font-weight:800;letter-spacing:-.035em;line-height:1.1;color:var(--ink)}
.hero-side .sub-title{color:var(--muted);font-size:13px;font-weight:500;letter-spacing:-.01em;min-height:18px}
.hero-side .artist{color:var(--ink-2);font-size:14px;font-weight:600;margin-top:14px;letter-spacing:-.015em}
.hero-side .release{color:var(--muted);font-size:11.5px;margin-top:6px;font-family:var(--mono);letter-spacing:.01em}

.vs-mark{display:grid;place-items:center;height:172px;position:relative}
.vs-mark .vs-glyph{font-family:var(--mono);font-size:18px;font-weight:700;color:var(--muted);letter-spacing:.3em;padding:6px 14px;border:1px solid var(--line-2);border-radius:999px;background:var(--panel);box-shadow:0 0 0 4px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.4)}

/* MATCH TOGGLE (라디오 기반 CSS-only 탭) */
.match-radios{position:absolute;opacity:0;pointer-events:none;left:-9999px}
.match-tabs{display:flex;gap:8px;margin:28px 0 24px;justify-content:center;flex-wrap:wrap}
.match-tab{display:inline-flex;align-items:center;gap:10px;padding:11px 20px;border-radius:14px;
  background:var(--panel-2);border:1px solid var(--line);color:var(--ink-2);
  font-family:var(--sans);font-size:13.5px;font-weight:700;letter-spacing:-.01em;
  cursor:pointer;transition:all .18s ease;user-select:none;
  position:relative;
}
.match-tab:hover{background:var(--panel-3);border-color:var(--line-2);transform:translateY(-1px)}
.match-tab .mt-pink{color:var(--tt);font-weight:800}
.match-tab .mt-blue{color:var(--wd);font-weight:800}
.match-tab .mt-vs{color:var(--muted);font-family:var(--mono);font-size:11px;letter-spacing:.2em;font-weight:700;padding:0 2px}
.match-tab .mt-wins{font-family:var(--mono);font-size:11px;font-weight:700;padding:2px 7px;border-radius:6px;background:var(--panel);border:1px solid var(--line);color:var(--muted);letter-spacing:.02em;margin-left:6px}
.match-tab .mt-mini-cover{width:22px;height:22px;border-radius:6px;object-fit:cover;box-shadow:0 0 0 1px rgba(255,255,255,.08)}

/* tab active state */
#match-tt:checked ~ .hero .match-tabs label[for="match-tt"],
#match-th:checked ~ .hero .match-tabs label[for="match-th"]{
  background:linear-gradient(180deg,rgba(255,122,182,.16),rgba(255,122,182,.04));
  border-color:rgba(255,122,182,.5);
  color:var(--ink);
  box-shadow:0 0 0 1px rgba(255,122,182,.25),0 8px 28px rgba(255,122,182,.18),inset 0 1px 0 rgba(255,255,255,.04);
}
#match-tt:checked ~ .hero .match-tabs label[for="match-tt"] .mt-wins,
#match-th:checked ~ .hero .match-tabs label[for="match-th"] .mt-wins{
  background:rgba(255,122,182,.15);border-color:rgba(255,122,182,.4);color:#FFD0E4
}

/* pane visibility */
.match-pane{display:none;animation:paneIn .35s ease-out}
#match-tt:checked ~ .match-pane.pane-tt,
#match-th:checked ~ .match-pane.pane-th{display:block}
@keyframes paneIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* hero side swap based on selected radio */
.hero-side.l .swap-tt,.hero-side.l .swap-th{display:none}
#match-tt:checked ~ .hero .hero-side.l .swap-tt{display:block}
#match-th:checked ~ .hero .hero-side.l .swap-th{display:block}

/* scoreboard inside pane */
.match-scoreboard{margin:18px 0 28px;padding:24px 28px;border-radius:18px;
  background:linear-gradient(180deg,var(--panel-2),var(--panel));
  border:1px solid var(--line);
  display:grid;grid-template-columns:1fr auto 1fr;gap:24px;align-items:center;
  box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 12px 40px rgba(0,0,0,.3);
  position:relative;overflow:hidden;
}
.match-scoreboard::before{content:"";position:absolute;inset:0;background:
  radial-gradient(600px 200px at 0% 50%,color-mix(in srgb,var(--l-color) 14%,transparent),transparent 60%),
  radial-gradient(600px 200px at 100% 50%,color-mix(in srgb,var(--r-color) 14%,transparent),transparent 60%);
  pointer-events:none}
.ms-block{display:flex;flex-direction:column;gap:4px;position:relative;z-index:1}
.ms-l{align-items:flex-end;text-align:right}
.ms-r{align-items:flex-start;text-align:left}
.ms-label{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-family:var(--mono)}
.ms-score{font-family:var(--mono);font-size:64px;font-weight:700;letter-spacing:-.05em;line-height:.95;font-variant-numeric:tabular-nums}
.ms-dash{font-family:var(--mono);text-align:center;font-size:14px;color:var(--muted-2);font-weight:500;letter-spacing:.2em;position:relative;z-index:1}
.ms-note{grid-column:1/-1;text-align:center;color:var(--muted);font-size:12px;font-family:var(--mono);letter-spacing:.01em;border-top:1px solid var(--line);padding-top:16px;margin-top:6px;position:relative;z-index:1}
.ms-note b{color:var(--ink-2);font-weight:700}

/* SECTIONS */
.section{margin-top:48px}
.section-h{display:flex;align-items:baseline;justify-content:space-between;gap:20px;margin-bottom:18px;flex-wrap:wrap}
.section-title{font-size:20px;font-weight:800;margin:0;letter-spacing:-.025em;color:var(--ink);display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.section-title .sec-no{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--muted);letter-spacing:.08em;padding:3px 8px;border:1px solid var(--line);border-radius:6px;background:var(--panel)}
.section-title .em{color:var(--gold)}
.src-chip{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 9px 0 6px;border-radius:7px;font-size:11.5px;font-weight:700;letter-spacing:.01em;border:1px solid var(--line);background:var(--panel-2);color:var(--ink-2);font-family:var(--sans);vertical-align:middle}
.src-chip-fav{width:14px;height:14px;border-radius:3px;display:block;flex-shrink:0}
.src-chip-txt{line-height:1}
.src-chip.src-melon{border-color:rgba(0,205,60,.4);background:rgba(0,205,60,.08);color:#4FE17A}
.src-chip.src-genie{border-color:rgba(255,107,107,.4);background:rgba(255,107,107,.08);color:#FF8E8E}
.src-chip.src-youtube{border-color:rgba(255,0,51,.4);background:rgba(255,0,51,.08);color:#FF6A85}
.chart-title{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:13.5px;font-weight:700;color:var(--ink);letter-spacing:-.015em}
.section-sub{color:var(--muted);font-size:12.5px;letter-spacing:-.005em;max-width:680px;line-height:1.5}

/* DELTA CARDS */
.delta-grid{display:grid;grid-template-columns:1fr 80px 1fr;gap:16px;align-items:stretch}
.delta-card{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:24px 26px;position:relative;overflow:hidden;transition:border-color .2s ease}
.delta-card.l-side{background:linear-gradient(180deg,color-mix(in srgb,var(--l-color) 6%,transparent),transparent 60%),var(--panel)}
.delta-card.r-side{background:linear-gradient(180deg,color-mix(in srgb,var(--r-color) 6%,transparent),transparent 60%),var(--panel)}
.delta-card.l-side:hover{border-color:color-mix(in srgb,var(--l-color) 40%,transparent)}
.delta-card.r-side:hover{border-color:color-mix(in srgb,var(--r-color) 40%,transparent)}
.delta-card.winner.l-side::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--l-color);box-shadow:0 0 20px var(--l-color)}
.delta-card.winner.r-side::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--r-color);box-shadow:0 0 20px var(--r-color)}
.delta-card .head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.delta-card .name{font-size:14px;font-weight:700;letter-spacing:-.015em}
.delta-card .win-badge{font-family:var(--mono);font-size:10.5px;font-weight:700;padding:3px 8px;border-radius:6px;letter-spacing:.05em;text-transform:uppercase;background:rgba(244,196,108,.12);color:var(--gold);border:1px solid rgba(244,196,108,.3)}
.delta-card .when{font-size:11px;color:var(--muted);margin-top:4px;font-family:var(--mono);letter-spacing:.01em}
.delta-card .big{font-family:var(--mono);font-size:52px;font-weight:700;margin-top:16px;letter-spacing:-.045em;line-height:1;font-variant-numeric:tabular-nums}
.delta-card .big-unit{font-family:var(--sans);font-size:15px;font-weight:600;color:var(--muted);margin-left:6px;letter-spacing:-.01em}
.delta-card .big-sub{font-size:12.5px;color:var(--muted);margin-top:6px;letter-spacing:-.005em}
.delta-card .row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:20px;padding-top:18px;border-top:1px solid var(--line)}
.delta-card .stat .lbl{font-size:10.5px;color:var(--muted);text-transform:uppercase;font-weight:700;letter-spacing:.06em;font-family:var(--mono)}
.delta-card .stat .val{font-family:var(--mono);font-size:18px;font-weight:700;margin-top:4px;color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.vs-mid{display:flex;align-items:center;justify-content:center}
.vs-mid .glyph{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--muted);letter-spacing:.3em;padding:6px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel)}

/* CALLOUT */
.callout{background:linear-gradient(135deg,var(--panel-2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:18px 22px;margin-top:18px;color:var(--ink-2);font-size:13.5px;display:flex;align-items:center;gap:14px;letter-spacing:-.005em}
.callout .ic{flex-shrink:0;width:32px;height:32px;border-radius:10px;background:rgba(244,196,108,.12);color:var(--gold);display:grid;place-items:center;font-weight:800;border:1px solid rgba(244,196,108,.25)}
.callout b{color:var(--ink)}
.callout .num{color:var(--ink);font-weight:700}

/* CHARTS */
.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chart-box{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:20px 22px}
.chart-title-row{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:8px;flex-wrap:wrap}
.chart-legend{display:flex;gap:8px;font-size:11px}
.lg-chip{display:inline-flex;align-items:center;gap:6px;padding:3px 9px;border-radius:999px;background:var(--panel-3);border:1px solid var(--line);color:var(--ink-2);font-weight:600;letter-spacing:-.005em}
.lg-dot{display:inline-block;width:8px;height:8px;border-radius:50%}
.chart-box svg{display:block;width:100%;height:auto}

/* TABLE */
.tbl-wrap{background:var(--panel);border:1px solid var(--line);border-radius:18px;overflow:auto;max-height:680px;position:relative}
.tbl-wrap::-webkit-scrollbar{width:10px;height:10px}
.tbl-wrap::-webkit-scrollbar-track{background:var(--panel)}
.tbl-wrap::-webkit-scrollbar-thumb{background:var(--line-2);border-radius:10px;border:2px solid var(--panel)}
table{border-collapse:separate;border-spacing:0;width:100%;min-width:1020px}
th,td{padding:13px 14px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;font-size:13px;letter-spacing:-.005em}
thead th{position:sticky;top:0;background:var(--panel-2);color:var(--ink-2);font-weight:700;font-size:11px;z-index:2;text-transform:uppercase;letter-spacing:.05em;font-family:var(--mono);padding-top:14px;padding-bottom:14px}
thead tr:first-child th{border-bottom:1px solid var(--line)}
thead tr.subhead th{top:42px;font-size:10.5px;color:var(--muted)}
th.center,td.center{text-align:center}
th.divide-r,td.divide-r{border-right:1px solid var(--line)}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel);z-index:1;font-weight:600;color:var(--ink-2)}
thead th:first-child{background:var(--panel-2);z-index:3}
tbody tr{transition:background .12s ease}
tbody tr:hover td{background:var(--panel-3)}
tbody tr:hover td:first-child{background:var(--panel-3)}
.cell-num{font-family:var(--mono);font-variant-numeric:tabular-nums;font-weight:600;color:var(--ink-2)}
.cell-l-win{color:var(--l-color,var(--tt)) !important;font-weight:700}
.cell-r-win{color:var(--r-color,var(--wd)) !important;font-weight:700}
.cell-faded{color:var(--muted-2) !important;font-weight:500}
td.l-bg{background:linear-gradient(90deg,var(--l-soft,rgba(255,122,182,.04)),transparent)}
td.r-bg{background:linear-gradient(270deg,var(--r-soft,rgba(110,168,254,.04)),transparent)}
tbody tr:hover td.l-bg{background:linear-gradient(90deg,color-mix(in srgb,var(--l-color) 12%,transparent),var(--panel-3))}
tbody tr:hover td.r-bg{background:linear-gradient(270deg,color-mix(in srgb,var(--r-color) 12%,transparent),var(--panel-3))}
.tcell-time{display:flex;flex-direction:column;gap:2px}
.tcell-time .dt{font-family:var(--mono);font-size:12.5px;color:var(--ink);font-weight:600;letter-spacing:.005em}
.tcell-time .rel{font-size:10.5px;color:var(--muted);font-family:var(--mono);letter-spacing:.02em}
.tcell-time .ref{font-size:10px;color:var(--muted-2);font-family:var(--mono);letter-spacing:.02em;margin-top:1px}
.tcell-time .ref::before{content:"↳ ";opacity:.6}

/* VS arrow */
.vs-cell{text-align:center;padding:8px 4px !important}
.vs-arrow{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-width:72px;height:30px;padding:0 10px;border-radius:9px;font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.04em;border:1px solid var(--line);background:var(--panel-2);color:var(--muted)}
.vs-arrow.l-side{background:linear-gradient(90deg,color-mix(in srgb,var(--l-color) 12%,transparent),transparent);border-color:color-mix(in srgb,var(--l-color) 42%,transparent);color:var(--l-color);box-shadow:inset 2px 0 0 var(--l-color)}
.vs-arrow.l-strong{background:linear-gradient(90deg,color-mix(in srgb,var(--l-color) 30%,transparent),color-mix(in srgb,var(--l-color) 6%,transparent));border-color:var(--l-color);color:#FFE6F1;box-shadow:inset 3px 0 0 var(--l-color),0 0 18px color-mix(in srgb,var(--l-color) 22%,transparent)}
.vs-arrow.r-side{background:linear-gradient(270deg,color-mix(in srgb,var(--r-color) 12%,transparent),transparent);border-color:color-mix(in srgb,var(--r-color) 42%,transparent);color:var(--r-color);box-shadow:inset -2px 0 0 var(--r-color)}
.vs-arrow.r-strong{background:linear-gradient(270deg,color-mix(in srgb,var(--r-color) 30%,transparent),color-mix(in srgb,var(--r-color) 6%,transparent));border-color:var(--r-color);color:#E6EFFF;box-shadow:inset -3px 0 0 var(--r-color),0 0 18px color-mix(in srgb,var(--r-color) 22%,transparent)}
.vs-arrow.split{color:var(--ink-2);border-color:rgba(160,180,210,.30);background:rgba(160,180,210,.05)}
.vs-arrow .arr{font-size:14px;line-height:1;font-weight:700}
.vs-arrow .vs-score{font-size:11.5px;font-variant-numeric:tabular-nums;font-weight:800;opacity:.95}
.vs-arrow .vs-dash{margin:0 2px;opacity:.6}
.sweep-mark{display:inline-block;margin-right:6px;color:var(--gold);font-size:10px;line-height:1;vertical-align:1px}

/* DIFF PILLS */
.diff{display:inline-block;padding:3px 10px;border-radius:6px;font-family:var(--mono);font-size:11.5px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:.005em;border:1px solid transparent}
.diff.l-side{background:color-mix(in srgb,var(--l-color) 10%,transparent);color:var(--l-color);border-color:color-mix(in srgb,var(--l-color) 22%,transparent)}
.diff.r-side{background:color-mix(in srgb,var(--r-color) 10%,transparent);color:var(--r-color);border-color:color-mix(in srgb,var(--r-color) 22%,transparent)}
.diff.tie{background:rgba(244,196,108,.10);color:var(--gold);border-color:rgba(244,196,108,.25)}
.diff.na{background:transparent;color:var(--muted-2)}

/* MULTIPLIER */
.pill-mult{display:inline-block;padding:3px 9px;border-radius:6px;font-family:var(--mono);font-size:11.5px;font-weight:700;font-variant-numeric:tabular-nums;border:1px solid transparent;letter-spacing:.005em}
.pill-mult.hot{background:rgba(255,107,126,.10);color:var(--red);border-color:rgba(255,107,126,.25)}
.pill-mult.high{background:rgba(255,166,77,.10);color:var(--orange);border-color:rgba(255,166,77,.25)}
.pill-mult.mid{background:rgba(244,196,108,.10);color:var(--gold);border-color:rgba(244,196,108,.25)}
.pill-mult.low{background:rgba(95,230,176,.08);color:var(--green);border-color:rgba(95,230,176,.22)}
.pill-mult.muted{background:transparent;color:var(--muted-2)}

/* MINI CARDS */
.mini-card{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:20px 22px}
.mini-card.l-tint{background:linear-gradient(180deg,rgba(255,122,182,.04),transparent 60%),var(--panel)}
.mini-card.r-tint{background:linear-gradient(180deg,rgba(110,168,254,.04),transparent 60%),var(--panel)}
.mini-card .name{font-size:11.5px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.06em;font-family:var(--mono)}
.mini-card .big{font-family:var(--mono);font-size:36px;font-weight:700;margin-top:10px;color:var(--ink);letter-spacing:-.04em;font-variant-numeric:tabular-nums;line-height:1}
.mini-card .big-unit{font-family:var(--sans);font-size:14px;font-weight:600;color:var(--muted);margin-left:5px}
.mini-card .big-sub{font-size:12px;color:var(--muted);margin-top:6px}

/* FOOTER */
.foot{color:var(--muted);font-size:11.5px;margin-top:60px;padding-top:30px;border-top:1px solid var(--line);line-height:1.7;font-family:var(--mono);letter-spacing:.005em}
.foot .row{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}
.foot b{color:var(--ink-2);font-weight:700}

/* RESPONSIVE */
@media(max-width:1100px){
  .hero-fg{padding:32px 28px}
  .cover-thumb{width:140px;height:140px}
  .vs-mark{height:140px}
  .ms-score{font-size:48px}
}
@media(max-width:780px){
  .wrap{padding:20px 16px 80px}
  .hero-row{grid-template-columns:1fr;gap:20px}
  .hero-side.l,.hero-side.r{text-align:center}
  .hero-side.l .cover-thumb{margin:0 auto}
  .vs-mark{height:auto;padding:6px 0}
  .hero::after{display:none}
  .match-tabs{flex-direction:column;align-items:stretch;gap:6px}
  .match-tab{justify-content:center}
  .match-scoreboard{grid-template-columns:1fr;gap:14px;padding:20px 22px}
  .ms-l,.ms-r{align-items:center;text-align:center}
  .ms-dash{display:none}
  .delta-grid{grid-template-columns:1fr}
  .vs-mid{display:none}
  .charts{grid-template-columns:1fr}
  .ms-score{font-size:48px}
  .hero-side h1{font-size:24px}
  .delta-card .row{grid-template-columns:repeat(3,1fr);gap:10px}
  .delta-card .stat .val{font-size:15px}
}
</style>'''

# ---------- 헤더 + 토글 라디오 (HTML 시작) ----------
wd_days_since = (now_kst.date() - WD['release'].date()).days
tt_days_since = (now_kst.date() - TT['release'].date()).days
th_days_since = (now_kst.date() - TH['release'].date()).days

parts = [f'''<!doctype html><html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>이 사랑 VS 떠나가요/까만안경 — 매시간 증가분 대결</title>
<meta name="description" content="이 사랑(우디) 기준 핑크 사이드 두 곡 (떠나가요/까만안경) 토글 매칭 비교">
<meta property="og:title" content="VS REPORT · 이 사랑 ⚔️ 떠나가요/까만안경">
<meta property="og:description" content="발매 후 같은 경과시간에서 매시간 증가분 VS 비교 — 토글 다크 리포트">
{css}
</head><body><div class="wrap">
<header class="topbar">
  <div class="brand">
    <div class="brand-mark">V</div>
    <div class="brand-text">VS REPORT<span class="slash">/</span><span class="sub">한국 음악 매시간 증가분 매칭 · 3곡 토글</span></div>
  </div>
  <div class="meta">
    <span><span class="live-dot"></span>LIVE</span>
    <span>UPDATED · {esc(now_kst.strftime("%Y-%m-%d %H:%M KST"))}</span>
  </div>
</header>

<!-- 토글 라디오 (CSS-only) -->
<input type="radio" name="match" id="match-tt" class="match-radios" checked>
<input type="radio" name="match" id="match-th" class="match-radios">

<section class="hero"{f' style="--hero-art:url({HERO_BG_B64});"' if HERO_BG_B64 else ''}>
  {f'<div class="hero-bg-art"></div>' if HERO_BG_B64 else ''}
  <div class="hero-fg">
    <div class="hero-row">
      <div class="hero-side l">
        <div class="swap-tt">
          <img class="cover-thumb" src="{TT["cover_b64"]}" alt="{esc(TT["short"])} 앨범 커버">
          <div class="side-tag"><span class="tag-dot"></span>PINK SIDE · 떠나가요</div>
          <h1>{esc(TT["title"])}</h1>
          <div class="sub-title">{esc(TT["subtitle"])}</div>
          <div class="artist">{esc(TT["artist"])}</div>
          <div class="release">{esc(TT["release"].strftime("%Y-%m-%d %H:%M KST"))} · D+{tt_days_since}</div>
        </div>
        <div class="swap-th">
          <img class="cover-thumb" src="{TH["cover_b64"]}" alt="{esc(TH["short"])} 앨범 커버">
          <div class="side-tag"><span class="tag-dot"></span>PINK SIDE · 까만안경</div>
          <h1>{esc(TH["title"])}</h1>
          <div class="sub-title">{esc(TH["subtitle"]) or "&nbsp;"}</div>
          <div class="artist">{esc(TH["artist"])}</div>
          <div class="release">{esc(TH["release"].strftime("%Y-%m-%d %H:%M KST"))} · D+{th_days_since}</div>
        </div>
      </div>
      <div class="vs-mark"><div class="vs-glyph">VS</div></div>
      <div class="hero-side r">
        <img class="cover-thumb" src="{WD["cover_b64"]}" alt="{esc(WD["short"])} 앨범 커버">
        <div class="side-tag"><span class="tag-dot"></span>BLUE SIDE · 고정</div>
        <h1>{esc(WD["title"])}</h1>
        <div class="sub-title">{esc(WD["subtitle"])}</div>
        <div class="artist">{esc(WD["artist"])}</div>
        <div class="release">{esc(WD["release"].strftime("%Y-%m-%d %H:%M KST"))} · D+{wd_days_since}</div>
      </div>
    </div>
    <div class="match-tabs" role="tablist" aria-label="매칭 선택">
      <label class="match-tab" for="match-tt" role="tab">
        <img class="mt-mini-cover" src="{TT["cover_b64"]}" alt="">
        <span class="mt-pink">{esc(TT["short"])}</span>
        <span class="mt-vs">VS</span>
        <span class="mt-blue">{esc(WD["short"])}</span>
        <span class="mt-wins">{MATCH_TT_WD["wins_L"]}·{MATCH_TT_WD["wins_R"]}</span>
      </label>
      <label class="match-tab" for="match-th" role="tab">
        <img class="mt-mini-cover" src="{TH["cover_b64"]}" alt="">
        <span class="mt-pink">{esc(TH["short"])}</span>
        <span class="mt-vs">VS</span>
        <span class="mt-blue">{esc(WD["short"])}</span>
        <span class="mt-wins">{MATCH_TH_WD["wins_L"]}·{MATCH_TH_WD["wins_R"]}</span>
      </label>
    </div>
  </div>
</section>''']

# ---------- 매칭 A: TT vs WD ----------
parts.append('<div class="match-pane pane-tt">')
parts.append(render_scoreboard_extras(MATCH_TT_WD))
parts.append(render_recent1h(MATCH_TT_WD, sec_no='01'))
parts.append(render_battle_table(MATCH_TT_WD, sec_no='02'))
parts.append(render_charts(MATCH_TT_WD, sec_no='03'))
parts.append(render_tt_daily(sec_no='04'))
parts.append(render_tt_youtube(sec_no='05'))
parts.append('</div>')

# ---------- 매칭 B: TH vs WD ----------
parts.append('<div class="match-pane pane-th">')
parts.append(render_scoreboard_extras(MATCH_TH_WD))
parts.append(render_recent1h(MATCH_TH_WD, sec_no='01'))
parts.append(render_battle_table(MATCH_TH_WD, sec_no='02'))
parts.append(render_charts(MATCH_TH_WD, sec_no='03'))
# TH 멜론·유튜브는 데이터 없음 — 안내 callout
parts.append(f'''<section class="section">
<div class="section-h">
  <h2 class="section-title"><span class="sec-no">04</span>{esc(TH["short"])} 멜론·유튜브</h2>
</div>
<div class="callout"><div class="ic">·</div><div>{esc(TH["short"])}은 발매 6일 만에 차트 100위권 이탈 ({esc(TH["release"].strftime("%m/%d"))} 발매 → 04/22 17:00 마지막 229위). 멜론 일별/스트리밍 카드는 0 rows, 유튜브 별도 수집 없음. 지니 누적 청취자 <span class="num">{fmt(16278)}명</span> · 누적 재생 <span class="num">{fmt(60461)}회</span> · 누적 배수 <span class="num">3.71×</span> (마지막 단발 스냅샷)</div></div>
</section>''')
parts.append('</div>')

# ---------- 푸터 ----------
parts.append(f'''<footer class="foot">
<div class="row">
<div><b>산식</b> · 매시간 1시간 동안 늘어난 청취자/재생 증가분 직접 매칭 · 시간배수 = 시간 재생 증가 ÷ 시간 청취자 증가</div>
<div><b>BUILD</b> · {esc(now_kst.strftime("%Y-%m-%d %H:%M:%S KST"))}</div>
</div>
<div class="row" style="margin-top:6px">
<div><b>SOURCES</b> · 멜론 일간/스트리밍 카드 · 지니 실시간 차트 · 유튜브 검색 API · 매시간 자동 빌드 → GitHub 자동 배포</div>
<div>VS REPORT v3 · 3-SONG TOGGLE</div>
</div>
</footer></div></body></html>''')

# 저장
html_out = '\n'.join(parts)
(REPO / 'index.html').write_text(html_out, encoding='utf-8')

data = {
    'built_at_kst': now_kst.isoformat(),
    'match_tt_wd': {
        'wins_L': MATCH_TT_WD['wins_L'], 'wins_R': MATCH_TT_WD['wins_R'],
        'total_battles': MATCH_TT_WD['total_battles'], 'rows': len(MATCH_TT_WD['vs_rows']),
    },
    'match_th_wd': {
        'wins_L': MATCH_TH_WD['wins_L'], 'wins_R': MATCH_TH_WD['wins_R'],
        'total_battles': MATCH_TH_WD['total_battles'], 'rows': len(MATCH_TH_WD['vs_rows']),
    },
}
(OUT / 'vs_compare_data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

print(json.dumps({
    'html_bytes': len(html_out.encode('utf-8')),
    'cover_tt_kb': round(len(TT['cover_b64']) / 1024, 1),
    'cover_th_kb': round(len(TH['cover_b64']) / 1024, 1),
    'cover_wd_kb': round(len(WD['cover_b64']) / 1024, 1),
    'match_tt_wd_rows': len(MATCH_TT_WD['vs_rows']),
    'match_tt_wd_score': f'{MATCH_TT_WD["wins_L"]}-{MATCH_TT_WD["wins_R"]}',
    'match_th_wd_rows': len(MATCH_TH_WD['vs_rows']),
    'match_th_wd_score': f'{MATCH_TH_WD["wins_L"]}-{MATCH_TH_WD["wins_R"]}',
}, ensure_ascii=False, indent=2))
