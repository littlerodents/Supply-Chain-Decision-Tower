"""Owner-authorized single-file frontend patch; compare source/data/model/Gateway first.
Requires existing SSH master and DGX_TARGET. No service management or model invocation.
Keeps a remote backup; refuses overwriting a concurrent revision.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

here=Path(__file__).resolve().parent
before=json.loads((here/'before.json').read_text())
source=(here/'app-candidate.py').read_text()
ast.parse(source)
payload={'expected':before['app_sha256'],'source':source,'data':before['data_hashes'],
         'model':before['default_model'],'gateway':before['gateway']}
remote='''import datetime,hashlib,json,os,pathlib,stat,subprocess,sys,tempfile
p=json.load(sys.stdin);h=pathlib.Path.home();root=h/'.openclaw/workspace/skills/supply-chain-control-tower';target=root/'panel/app.py'
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def data_hashes(): return {str(n.relative_to(root)):digest(n) for n in (root/'data').glob('*') if n.is_file() and n.suffix in ('.csv','.json')}
def protected():
 names=['SKILL.md','scripts/tools.py','scripts/algorithms.py','scripts/daily_scan.py','evals/gold.json','evals/evals.json','references/api.md']
 return {n:digest(root/n) for n in names if (root/n).is_file()}
assert not target.is_symlink(), 'Refuse symlink target'
assert digest(target)==p['expected'], 'SOURCE_CHANGED: do not overwrite concurrent work'
assert data_hashes()==p['data'], 'DATA_CHANGED: need new baseline'
env=dict(os.environ);env['PATH']=str(h/'node26/bin')+':'+env.get('PATH','')
r=subprocess.run([str(h/'node26/bin/openclaw'),'config','get','agents.defaults.model'],env=env,capture_output=True,text=True,timeout=15);assert r.returncode==0
assert json.loads(r.stdout)==p['model'], 'MODEL_CHANGED: no model mutation allowed'
r=subprocess.run(['systemctl','--user','show','openclaw-gateway','--property=ActiveState,MainPID,ActiveEnterTimestamp','--no-pager'],capture_output=True,text=True,timeout=5)
assert r.returncode==0 and r.stdout.strip()==p['gateway'], 'GATEWAY_CHANGED: baseline no longer matches'
pre=protected(); original=target.read_bytes();st=target.stat();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=target.parent/('.app.py.before-pi-minfix-'+stamp+'.bak')
with backup.open('xb') as f: f.write(original)
backup.chmod(0o600)
fd,temp=tempfile.mkstemp(prefix='.app-minfix-',suffix='.tmp',dir=target.parent)
try:
 with os.fdopen(fd,'w') as f:
  os.fchmod(f.fileno(),stat.S_IMODE(st.st_mode));f.write(p['source']);f.flush();os.fsync(f.fileno())
 assert digest(target)==p['expected'] and target.stat().st_ino==st.st_ino, 'SOURCE_CHANGED during staging'
 assert data_hashes()==p['data'] and protected()==pre, 'PROTECTED_INPUT_CHANGED during staging'
 os.replace(temp,target)
finally:
 if pathlib.Path(temp).exists(): pathlib.Path(temp).unlink()
after=digest(target);assert after==hashlib.sha256(p['source'].encode()).hexdigest()
assert data_hashes()==p['data'] and protected()==pre, 'PROTECTED_INPUT_CHANGED after apply'
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds'),
 'before_sha256':p['expected'],'after_sha256':after,'changed_production_files':['panel/app.py'],
 'backup':str(backup),'data_unchanged':True,'protected_hashes':pre,'protected_unchanged':True,
 'gateway_before':p['gateway'],'default_model_before':p['model'],'service_restart':False,'new_model_calls':0},ensure_ascii=False,indent=2))
'''
cmd=['ssh','-T','-S',os.environ.get('DGX_SOCKET','/tmp/dgx-spark-master.sock'),'-o','BatchMode=yes','-o','ProxyCommand=false',os.environ['DGX_TARGET']]
r=subprocess.run(cmd+['python3 -B -c '+shlex.quote(remote)],input=json.dumps(payload),text=True,capture_output=True,timeout=35)
sys.stdout.write(r.stdout);sys.stderr.write(r.stderr);sys.exit(r.returncode)
