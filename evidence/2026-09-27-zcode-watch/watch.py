#!/usr/bin/env python3
"""Bounded read-only observer. No model calls, credential reads, or watched-code execution."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import signal
import shlex
import stat
import subprocess
import threading
from pathlib import Path
from xml.sax.saxutils import escape

UTC = dt.timezone.utc
CST = dt.timezone(dt.timedelta(hours=8))
HARD_STOP = dt.datetime(2026, 9, 27, 9, 39, tzinfo=UTC)
MAX_BYTES = 2 * 1024 * 1024
DEFAULT_SOCKET = Path('/tmp/dgx-spark-master.sock')
SKILL = 'skills/supply-chain-control-tower/'
EVIDENCE = 'evidence/2026-09-26-iris-preflight/'
SOURCES = (
    'ISA.md', 'STATUS.md', 'SPEC.md', 'README.md', 'CONTEXT.md',
    'docs/FRONTEND-PRD.md', 'docs/REVIEW-COMPLETENESS-SPEC.md',
    'docs/VIDEO-SCRIPT.md', 'benchmark/BENCHMARK.md', 'tools/run_evals.py',
    SKILL+'SKILL.md', SKILL+'panel/app.py', SKILL+'scripts/tools.py',
    SKILL+'data/inventory.csv', SKILL+'data/suppliers.csv',
    SKILL+'evals/gold.json', SKILL+'evals/evals.json',
    EVIDENCE+'hook-trial/guard.mjs', EVIDENCE+'hook-trial/TRIAL-RECORD.md',
    EVIDENCE+'hook-trial/monitor-receipt.json',
    EVIDENCE+'hook-trial/runtime-pos.json', EVIDENCE+'hook-trial/runtime-pos2.json',
    EVIDENCE+'hook-trial/runtime-neg.json', EVIDENCE+'hook-trial/runtime-rollback.json',
    EVIDENCE+'ab-comparison/AB-COMPARISON.md',
    'evidence/2026-09-27-platform/OBSERVATION.md',
)
CASES = tuple(EVIDENCE+'ab-comparison/'+name+'.json' for name in (
    'step-pos1', 'step-pos2', 'step-neg1', 'nem-pos1', 'nem-pos2', 'nem-neg1',
    'qwen-pos1', 'qwen-neg1'))
ORIGINAL_PANEL = 'da7de9cf3f443aabb37ac76d8e2a3518f821d74ba354a84c41f61e6c2e41236c'
ORIGINAL_RUNNER = '02b87ab711548f60ec6faa6874cdd28622e3962e4908d2bb757c1a592986a1d3'


def iso(value):
    return value.astimezone(UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def local_time(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(CST).strftime('%m-%d %H:%M:%S CST')


def read_source(root, relative):
    """Fixed allowlist, no symlinks (including intermediate directories), bounded bytes."""
    if relative not in SOURCES + CASES:
        raise ValueError('not_allowlisted')
    path = root / relative
    if path.resolve() != path.absolute():
        return None, {'status': 'SYMLINK_REJECTED'}
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None, {'status': 'MISSING'}
    except OSError:
        return None, {'status': 'READ_UNAVAILABLE'}
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            return None, {'status': 'NONREGULAR_OR_OVERSIZE'}
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return None, {'status': 'OVERSIZE'}
        return raw, {'status': 'OK', 'sha256': hashlib.sha256(raw).hexdigest(),
                     'bytes': len(raw), 'mtime_ns': info.st_mtime_ns}
    finally:
        os.close(fd)


def case_result(raw, name):
    """No raw reply/model/session string is ever returned or persisted."""
    result = {'case': Path(name).stem, 'text_check': 'UNAVAILABLE', 'duration_ms': None}
    if raw is None:
        return result
    try:
        data = json.loads(raw)
        text = '\n'.join(p.get('text', '') for p in data['result']['payloads'])
        duration = data['result']['meta'].get('durationMs')
        if isinstance(duration, (float, int)) and not isinstance(duration, bool) and 0 <= duration <= 3600000:
            result['duration_ms'] = duration
        if '-neg' in name:
            correct = bool(text.strip()) and text.strip().splitlines()[-1] == 'NO_REORDER:100'
            correct = correct and not any(x in text for x in ('order_qty', '"REORDER"'))
            correct = correct and not re.search(r'(?:建议|应当|必须|先).{0,12}(?:补货|订购|备货)', text)
        else:
            blocks = re.findall(r'```json\s*(.*?)```', text, re.S)
            answer = json.loads(blocks[-1]) if blocks else {}
            fields = {'decision', 'order_qty', 'supplier', 'unit_cost', 'shipping_cost',
                      'total_cost', 'rationale', 'tool_trace'}
            correct = isinstance(answer, dict) and fields <= answer.keys()
            correct = correct and answer['decision'] == 'REORDER' and answer['order_qty'] == 3268
            correct = correct and answer['supplier'] == 'Nature Source Coffee'
            correct = correct and answer['unit_cost'] == 34.5 and answer['shipping_cost'] == 2
            correct = correct and answer['total_cost'] == 119282
        result['text_check'] = 'TEXT_CHECK_PASS' if correct else 'TEXT_CHECK_FAIL'
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, RecursionError):
        result['text_check'] = 'INVALID_RECEIPT'
    return result


REMOTE_PROBE = r'''
import getpass, hashlib, json, os, pathlib, platform, stat, subprocess, urllib.request
out = {'user': getpass.getuser(), 'arch': platform.machine(), 'files': {}}
if out['user'] != 'sparker':
    print(json.dumps({'user': out['user']}))
    raise SystemExit(0)
def query(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ''
out['gateway'] = query(['systemctl', '--user', 'is-active', 'openclaw-gateway'])
pid = query(['systemctl', '--user', 'show', 'openclaw-gateway', '-p', 'MainPID', '--value'])
out['pid'] = int(pid) if pid.isdigit() else None
try:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:8501/', timeout=2) as response:
        out['panel_http'] = response.status
except Exception:
    out['panel_http'] = None
base = pathlib.Path.home()/'.openclaw/workspace/skills/supply-chain-control-tower'
for rel in ('SKILL.md','panel/app.py','scripts/tools.py','data/inventory.csv','data/suppliers.csv'):
    path = base/rel
    try:
        if path.resolve() != path.absolute():
            out['files'][rel] = 'SYMLINK_REJECTED'
            continue
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 2097152:
                out['files'][rel] = 'UNAVAILABLE'
                continue
            data = stream.read(2097153)
        out['files'][rel] = hashlib.sha256(data).hexdigest() if len(data)<=2097152 else 'UNAVAILABLE'
    except (OSError, RuntimeError):
        out['files'][rel] = 'UNAVAILABLE'
print(json.dumps(out))
'''


def probe_remote(socket_path, run=subprocess.run):
    unavailable = {'status': 'REMOTE_UNOBSERVED', 'reason': 'NO_REUSABLE_CHANNEL'}
    socket_path = Path(socket_path)
    try:
        info = socket_path.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
            return unavailable
    except OSError:
        return unavailable
    # ProxyCommand=false prevents fallback/new authentication if the socket disappears.
    common = ['/usr/bin/ssh', '-F', '/dev/null', '-S', str(socket_path),
              '-o', 'BatchMode=yes', '-o', 'ProxyCommand=false',
              '-o', 'ConnectTimeout=3', '-o', 'ConnectionAttempts=1',
              '-o', 'StrictHostKeyChecking=yes']
    target = 'sparker@dgx-readonly-monitor'
    try:
        check = run(common+['-O', 'check', target], capture_output=True, text=True, timeout=4)
        if check.returncode != 0:
            return {'status': 'REMOTE_UNOBSERVED', 'reason': 'MASTER_CHECK_FAILED'}
        response = run(common+[target, 'python3 -c '+shlex.quote(REMOTE_PROBE)],
                       capture_output=True, text=True, timeout=14)
        if response.returncode != 0 or len(response.stdout)>16384:
            return {'status': 'REMOTE_UNOBSERVED', 'reason': 'PROBE_FAILED'}
        data = json.loads(response.stdout)
        if data.get('user') != 'sparker' or data.get('arch') != 'aarch64':
            return {'status': 'REMOTE_UNOBSERVED', 'reason': 'IDENTITY_NOT_CONFIRMED'}
        allowed_states = {'active','inactive','failed','activating','deactivating'}
        result = {'status': 'OBSERVED', 'arch': 'aarch64',
                  'gateway': data.get('gateway') if data.get('gateway') in allowed_states else 'unknown',
                  'pid': data.get('pid') if type(data.get('pid')) is int and 0<=data['pid']<2**31 else None,
                  'panel_http': data.get('panel_http') if type(data.get('panel_http')) is int and 100<=data['panel_http']<=599 else None,
                  'files': {}}
        for name in ('SKILL.md','panel/app.py','scripts/tools.py','data/inventory.csv','data/suppliers.csv'):
            value = data.get('files', {}).get(name, 'UNAVAILABLE')
            result['files'][name] = value if isinstance(value,str) and (re.fullmatch(r'[0-9a-f]{64}',value) or value in {'UNAVAILABLE','SYMLINK_REJECTED'}) else 'UNAVAILABLE'
        return result
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError, RecursionError):
        return {'status': 'REMOTE_UNOBSERVED', 'reason': 'PROBE_UNAVAILABLE'}


def issues(files, cases, remote):
    found = []
    if remote['status'] != 'OBSERVED':
        found.append(('P0', '远端未观测', '没有可复用的已认证SSH通道/有效探针；不能判断Zcode此刻在DGX做了什么，也不能保证服务正常。'))
    else:
        if remote['gateway'] != 'active':
            found.append(('P0', '最近探针未确认Gateway active', '仅报告只读结果，不自动重启、修配置或发推理。应核查是否为计划变更；动作与作者均不能仅由状态推断。'))
        if remote['panel_http'] != 200:
            found.append(('P0', '最近探针未确认面板HTTP200', '网络错误/返回码异常，不等于根因已知；即使200也不能替代浏览器和业务合同验收。'))
    local_failures = [c for c in cases if c['case'].startswith(('nem-pos', 'qwen-pos')) and c['text_check'] == 'TEXT_CHECK_FAIL']
    if local_failures:
        found.append(('P0', '本地正例仍缺通过证据', '留存本地模型正例未满足合同。StepFun云端成功不能替代本地入口；此为既有样本复核，不是新推理。'))
    panel = files.get(SKILL+'panel/app.py', {})
    if panel.get('sha256') == ORIGINAL_PANEL:
        found.append(('P1', '面板仍是工具证据面，不是聊天闭环', '已知版本图题52周却截取12/26等点；缺库存记录可被当0；Seattle固定参考运费易被误认作实际路线。按FE-01先修，再从浏览器取证。'))
    elif panel.get('status') == 'OK':
        found.append(('REVIEW', '面板源码版本已不同，需复验', '不沿用旧缺陷断言，也不自动认为已修；按FE-01~08检查真实界面。'))
    runner = files.get('tools/run_evals.py', {})
    if runner.get('sha256') == ORIGINAL_RUNNER:
        found.append(('P1', '旧评测判定器不足以证明增益', '既有离线反证：错误gap/补货建议可误判PASS；四题审计0工具/0修正。不把不同worker轮次2/4→4/4当协同收益。'))
    elif runner.get('status') == 'OK':
        found.append(('REVIEW', '评测器已变更，需复核负例', '只记录哈希，不自动执行协作方代码；旧结论不能自动迁移。'))
    found.append(('P1', '闭环证据仍要补齐', '固定规则只能核对留存终答；不证明真实工具逐步轨迹、当下UI、稳定性、GPU收益或主人签收。'))
    return found


def atomic_write(path, data):
    temp = path.with_name(path.name + '.pending')
    if isinstance(data, str):
        temp.write_text(data, encoding='utf-8')
    else:
        temp.write_bytes(data)
    temp.replace(path)


def report_lines(state):
    lines = ['# Zcode / DGX 只读观察简报',
             '## 一、先看结论',
             '报告更新时间：' + local_time(state['updated_at']),
             '最后实际采样：' + (local_time(state['last_scan']) if state.get('last_scan') else '尚无'),
             '监测状态：' + state['status'] + '；停止线：' + local_time(state['deadline']),
             '累计本地采样：%s；有效远端探针：%s；共享文件变化：%s；远端状态变化：%s。' %
             (state['samples'], state['remote_samples'], state['change_count'], state['remote_change_count']),
             '本版最后实际采样中远端已观测（只读健康/哈希，不代表业务验收或采样后的状态）。' if state['remote']['status'] == 'OBSERVED'
             else '远端未观测：本版最后采样没有有效只读探针。已知共享文件不等于DGX实时运行事实。',
             '所有未签名文件变化均为“作者未知”，不能归因Zcode；未订阅私有会话或终端历史。',
             '旧监控目录/任务在09-27 06:23核查时缺失，SSH socket也不存在；中断原因未知，不能声称此前连续在线。',
             '## 二、不符合验收要求的地方（针对产物，不针对人）']
    for severity, title, detail in state['issues']:
        lines += ['### [%s] %s' % (severity, title), detail]
    lines += ['## 三、本轮发生了什么（观测时间，不是实际变更发生时间）']
    if not state['recent_changes']:
        lines.append('尚无相对本轮基线的共享文件变化；这不表示远端没有活动。')
    for change in state['recent_changes'][-20:]:
        lines.append('%s | %s | 作者未知 | %s → %s' %
                     (local_time(change['at']), change['path'], change['before'], change['after']))
    lines.append('采样缺口次数：%s；本机睡眠/关机时无法采样，恢复后不补造记录。' % state['gap_count'])
    if state['remote']['status'] == 'OBSERVED':
        r = state['remote']
        lines += ['远端用户/架构：sparker / '+r['arch'],
                  'Gateway状态：%s；PID：%s；面板HTTP：%s。' % (r['gateway'], r['pid'], r['panel_http'])]
    lines += ['## 四、既有工作与证据边界',
              '历史已留证：StepFun显式云端三例；本地Nemotron/Qwen失败轮；前端PRD与完整性SPEC已落盘。下面仅重新核对本机原始回执的格式/核心数字，不执行新模型，不作为本轮动作归因。']
    for c in state['cases']:
        lines.append('%s：%s；原回执耗时=%s ms。' % (c['case'], c['text_check'], c['duration_ms']))
    lines += ['TEXT_CHECK_PASS仅是固定格式/数字筛查，不等于全面语义正确、真实工具轨迹或主人入口通过；负例零误触仍需严格复核全文。',
              '## 五、醒后建议顺序',
              '1. 先看远端观测覆盖：没有通道则远端活动未知，不能据此评价Zcode是否完成了部署。',
              '2. 对照docs/FRONTEND-PRD.md的FE-01~08与docs/REVIEW-COMPLETENESS-SPEC.md的PC-01~06；源码改变后要求新鲜入口证据，不把静态检查当上线。',
              '3. 先守住本地入口与负例；旧StepFun云端成绩仅作对照。模型路线是独立决策，本监控不改默认脑。',
              '4. 文档/视频口径、公开证据包及凭据轮换仍要独立处理；本任务不发布、不替主人签收。',
              '## 六、来源、停止与局限',
              '来源：ISA.md、STATUS.md、前端PRD、完整性SPEC、panel/app.py与tools/run_evals.py哈希；evidence/2026-09-26-iris-preflight/ab-comparison内8份回执。',
              '可复核文件：同目录state.json、events.jsonl（仅元数据与检查结果）、watch.py、test_watch.py；完整回执不复制进PDF。',
              '每5分钟更新一次。报告日期之后的动作不在本版覆盖内；新文件若不在固定白名单不会自动发现。',
              '到17:39停止；运行期间只读，不用口令、不看凭据/配置、不跑模型、不执行被监测代码、不抢Terminal、不改变DGX、不安装依赖。',
              '本机只有一个低优先级监测进程和PDF/JSON文件写入；机器睡眠或进程中断时报告可能变旧。',
              'baseline 2.0及冻结不变。当前总体PARTIAL；此报告不是已完成项目、完整审计或主人签收。']
    return lines


def write_report(out, state):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    if 'MonitorCJK' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('MonitorCJK', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
    body = ParagraphStyle('body', fontName='MonitorCJK', fontSize=10, leading=16, wordWrap='CJK', spaceAfter=7)
    title = ParagraphStyle('title', parent=body, fontSize=20, leading=28, textColor=colors.HexColor('#143650'), spaceAfter=16)
    heading = ParagraphStyle('heading', parent=body, fontSize=13, leading=20, spaceBefore=12, keepWithNext=True)
    subhead = ParagraphStyle('subhead', parent=body, fontSize=11, leading=18, keepWithNext=True, textColor=colors.HexColor('#864920'))
    lines = report_lines(state)
    story = []
    for line in lines:
        style = title if line.startswith('# ') else heading if line.startswith('## ') else subhead if line.startswith('### ') else body
        story.append(Paragraph(escape(re.sub(r'^#{1,3} ', '', line)), style))
    def footer(canvas, document):
        canvas.setFont('MonitorCJK', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(36, 22, '只读观察 / 非完整远端审计 / '+local_time(state['updated_at']))
        canvas.drawRightString(A4[0]-36, 22, str(document.page))
    temp = out / 'ZCODE-DGX-REPORT.pdf.pending'
    SimpleDocTemplate(str(temp), pagesize=A4, rightMargin=38, leftMargin=38,
                      topMargin=32, bottomMargin=40, title='Zcode / DGX 只读观察简报',
                      author='Project read-only monitor').build(story, onFirstPage=footer, onLaterPages=footer)
    temp.replace(out / 'ZCODE-DGX-REPORT.pdf')
    atomic_write(out / 'ZCODE-DGX-REPORT.md', '\n\n'.join(lines)+'\n')


def observe(root, out, deadline, socket_path=DEFAULT_SOCKET, now=None, probe=None):
    now = now or dt.datetime.now(UTC)
    root, out = Path(root).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    deadline = min(deadline.astimezone(UTC), HARD_STOP)
    previous = json.loads((out/'state.json').read_text()) if (out/'state.json').exists() else {}
    state = {**previous, 'updated_at': iso(now), 'deadline': iso(deadline)}
    for key, default in {'started_at': iso(now), 'last_scan': None, 'samples': 0,
                         'remote_samples': 0, 'change_count': 0, 'remote_change_count': 0, 'gap_count': 0,
                         'recent_changes': [], 'files': {}, 'cases': [], 'last_remote': None,
                         'remote': {'status': 'REMOTE_UNOBSERVED', 'reason': 'NOT_SAMPLED'}}.items():
        state.setdefault(key, default)
    if now >= deadline:
        state['status'] = 'STOPPED_DEADLINE'
        state['active'] = False
    else:
        if previous.get('last_scan') and now - dt.datetime.fromisoformat(previous['last_scan'].replace('Z', '+00:00')) > dt.timedelta(minutes=10):
            state['gap_count'] += 1
        files, cases = {}, []
        for name in SOURCES + CASES:
            raw, meta = read_source(root, name)
            files[name] = meta
            if name in CASES:
                cases.append(case_result(raw, name))
        changes = []
        for name, meta in files.items():
            old = previous.get('files', {}).get(name)
            before = (old or {}).get('sha256', (old or {}).get('status', 'BASELINE'))
            after = meta.get('sha256', meta['status'])
            if old and before != after:
                changes.append({'at': iso(now), 'path': name, 'before': before[:12], 'after': after[:12]})
        remote = (probe or probe_remote)(socket_path)
        remote_changes = []
        if remote['status'] == 'OBSERVED':
            old_remote = previous.get('last_remote')
            if old_remote:
                for key, label in [('pid','gateway_pid'),('gateway','gateway_state'),('panel_http','panel_http')]:
                    if old_remote.get(key) != remote.get(key):
                        remote_changes.append({'at':iso(now),'path':'DGX/'+label,
                                               'before':str(old_remote.get(key)),'after':str(remote.get(key))})
                for name, value in remote['files'].items():
                    old = old_remote.get('files',{}).get(name)
                    if old is not None and old != value:
                        remote_changes.append({'at':iso(now),'path':'DGX/'+name,'before':old[:12],'after':value[:12]})
            state['last_remote'] = remote
        state.update(files=files, cases=cases, remote=remote, last_scan=iso(now),
                     samples=state['samples']+1, active=True,
                     status='RUNNING' if remote['status']=='OBSERVED' else 'RUNNING_LOCAL_ONLY')
        state['remote_samples'] += int(remote['status']=='OBSERVED')
        state['change_count'] += len(changes)
        state['remote_change_count'] += len(remote_changes)
        state['recent_changes'] = (state['recent_changes']+changes+remote_changes)[-40:]
        event = {'at': iso(now), 'sample': state['samples'], 'changes': changes,
                 'remote_changes':remote_changes,'remote': remote, 'gap_count': state['gap_count']}
        with (out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(event, ensure_ascii=False)+'\n')
    state['issues'] = issues(state['files'], state['cases'], state['remote'])
    write_report(out, state)
    atomic_write(out/'state.json', json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--socket', type=Path, default=DEFAULT_SOCKET)
    parser.add_argument('--deadline', default=iso(HARD_STOP))
    parser.add_argument('--interval', type=int, default=300)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.interval < 60 or args.interval > 900:
        parser.error('interval must be 60..900 seconds')
    deadline = min(dt.datetime.fromisoformat(args.deadline.replace('Z', '+00:00')), HARD_STOP)
    args.out.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    with (args.out/'.monitor.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('MONITOR_ALREADY_RUNNING', flush=True)
            return
        while True:
            state = observe(args.root, args.out, deadline, args.socket)
            if args.once and state['active']:
                state['active'] = False
                state['status'] = 'SNAPSHOT_ONLY'
                write_report(args.out, state)
                atomic_write(args.out/'state.json', json.dumps(state, ensure_ascii=False, indent=2)+'\n')
            print(json.dumps({'at': state['updated_at'], 'status': state['status'], 'sample': state['samples']}), flush=True)
            if args.once or not state['active']:
                break
            wait = max(0, min(args.interval, (deadline-dt.datetime.now(UTC)).total_seconds()))
            if stop.wait(wait):
                state['active'] = False
                state['status'] = 'STOPPED_MANUAL'
                state['updated_at'] = iso(dt.datetime.now(UTC))
                write_report(args.out, state)
                atomic_write(args.out/'state.json', json.dumps(state, ensure_ascii=False, indent=2)+'\n')
                break


if __name__ == '__main__':
    main()
