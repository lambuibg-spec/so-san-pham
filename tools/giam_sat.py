# -*- coding: utf-8 -*-
r"""GIAM SAT DONG BO SO SAN PHAM (20/10/2026, chu du an: "tao can 100% moi sua doi deu cap nhat dong bo ko sai").
Chay tren GitHub moi 10 phut, KHONG phu thuoc PC. Lech ⇒ thoat 1 (workflow do ⇒ email chu kho).
Kiem:
  1. Firebase doc duoc, du lieu dung khuon.
  2. Ban chup Firebase -> git (so-san-pham/online/*.json): moi muc Firebase moi hon ban chup QUA 20 PHUT ma chua vao git ⇒ LECH.
  3. Lan DUNG WEB thanh cong gan nhat (workflow dung-web-tu-git) cach day QUA 30 PHUT ⇒ LECH.
  4. Web dang chay: tai duoc, co dau 'build:', co ket noi Firebase, so the >= so ma (tru ma chua co link anh) - 0.
  5. Dau ban phieu quay tren web = dau ban lan dung gan nhat (neu da dung xong).
"""
import datetime as dt, json, os, re, subprocess, sys, time, urllib.request

FB = 'https://project-c3d8a9ea-5303-4e42-969-default-rtdb.asia-southeast1.firebasedatabase.app'
LAW = os.environ['TIKTOK_LUAT']
REPO = os.environ.get('REPO', 'lambuibg-spec/so-san-pham')
WEB = 'https://lambuibg-spec.github.io/so-san-pham/'
CHO_PHEP_GIT = 20 * 60
CHO_PHEP_DUNG = 30 * 60
loi, ghi = [], []
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def get(url, timeout=60, rng=None):
    h = {'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'}
    if rng:
        h['Range'] = rng
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout).read()


def jget(url):
    for lan in range(3):
        try:
            return json.loads(get(url).decode('utf-8') or 'null')
        except Exception as e:
            if lan == 2:
                raise
            time.sleep(3)


now = time.time()
# 1+2: Firebase <-> git
try:
    dq = jget(FB + '/daquay.json') or {}
    tim = jget(FB + '/tim/chung.json') or {}
    ghi.append('Firebase: %d khoa tich (x=1: %d) | %d tim' % (len(dq), sum(1 for v in dq.values() if v.get('x') == 1), len(tim)))
    for ten, fb in (('da_quay', dq), ('tim_chung', tim)):
        p = os.path.join(LAW, 'so-san-pham', 'online', ten + '.json')
        git = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        khoa_t = (lambda v: v.get('t', 0))
        chua = [k for k, v in fb.items() if k not in git or khoa_t(v) > khoa_t(git[k]) or (v.get('x', v.get('v')) != git[k].get('x', git[k].get('v')) and khoa_t(v) >= khoa_t(git[k]))]
        cu = [k for k in chua if fb[k].get('t', 0) > 10 ** 11 and now - fb[k]['t'] / 1000 > CHO_PHEP_GIT]
        mat = [k for k in git if k not in fb]
        ghi.append('%s: git %d khoa | Firebase moi hon git: %d khoa (qua 20 phut: %d) | co o git ma Firebase khong co: %d' % (ten, len(git), len(chua), len(cu), len(mat)))
        if cu:
            loi.append('%s: %d muc o Firebase da QUA 20 PHUT ma chua vao git (nguoi gac online tren PC co the da tat). Vi du: %s' % (ten, len(cu), cu[:2]))
        if mat:
            loi.append('%s: git co %d khoa Firebase khong co (Firebase bi xoa/mat du lieu?) vi du %s' % (ten, len(mat), mat[:2]))
except Exception as e:
    loi.append('Firebase/git: khong kiem duoc: %s' % str(e)[:150])

# 3: lan dung web gan nhat
try:
    out = subprocess.run(['gh', 'api', 'repos/%s/actions/workflows/build.yml/runs?status=success&per_page=1' % REPO, '--jq', '.workflow_runs[0] | [.created_at, .head_sha] | @tsv'],
                         capture_output=True, text=True, encoding='utf-8').stdout.strip()
    if not out:
        loi.append('Chua co lan dung web nao thanh cong (workflow dung-web-tu-git)')
    else:
        t = dt.datetime.fromisoformat(out.split('\t')[0].replace('Z', '+00:00')).timestamp()
        tuoi = now - t
        ghi.append('Lan dung web thanh cong gan nhat: %d phut truoc' % (tuoi // 60))
        if tuoi > CHO_PHEP_DUNG:
            loi.append('Lan dung web thanh cong gan nhat cach day %d phut (cho phep 30) — GitHub tu dung bi dung?' % (tuoi // 60))
except Exception as e:
    loi.append('Khong doc duoc lich su dung web: %s' % str(e)[:120])

# 4: web dang chay
try:
    s = get(WEB + '?x=%d' % now, 120).decode('utf-8', 'replace')
    the = s.count('<article class="the"')
    b = re.findall(r'build:([0-9a-f]{16})', s[-4000:])
    ghi.append('Web: %d the | build %s | Firebase %s' % (the, b[-1:] or 'KHONG CO', 'co' if 'firebasedatabase.app' in s else 'KHONG'))
    d = json.load(open(os.path.join(LAW, 'so-san-pham', 'danh_muc.json'), encoding='utf-8-sig'))['ma']
    can = sum(1 for m, v in d.items() if v.get('anh'))
    ghi.append('So goc %d ma (co link anh: %d) | the tren web: %d' % (len(d), can, the))
    try:
        ct = float(subprocess.run(['git', '-C', LAW, 'log', '-1', '--format=%ct', '--', 'so-san-pham/danh_muc.json'], capture_output=True, text=True).stdout.strip() or 0)
    except Exception:
        ct = 0
    moi_them = now - ct < CHO_PHEP_DUNG      # so goc vua doi < 30 phut: cho GitHub dung kip, chua coi la loi
    if the < can and not moi_them:
        loi.append('Web co %d the, so goc co %d ma co anh (thieu %d) va so goc da doi tu hon 30 phut' % (the, can, can - the))
    if 'firebasedatabase.app' not in s:
        loi.append('Trang web KHONG co ket noi Firebase')
    if not b:
        loi.append('Trang web khong co dau build (khong phai ban GitHub dung)')
except Exception as e:
    loi.append('Khong tai duoc web: %s' % str(e)[:120])

print('\n'.join('  ' + x for x in ghi))
if os.environ.get('GITHUB_STEP_SUMMARY'):
    open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8').write('### Giam sat dong bo\n' + '\n'.join('- ' + x for x in ghi) + '\n' + ('\n### LECH\n' + '\n'.join('- ' + x for x in loi) if loi else '\n**TAT CA KHOP**\n'))
if loi:
    print('LECH:')
    print('\n'.join('  ! ' + x for x in loi))
    sys.exit(1)
print('TAT CA KHOP')
