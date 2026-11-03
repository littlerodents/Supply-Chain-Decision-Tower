"""Run UI replay in an isolated temporary copy on the already-authenticated DGX.
Only app source + public fixture harness are uploaded; production data/tools are copied read-only.
The temporary copy is removed on exit. No service, config, model or production data mutation.
Usage: python3 -B run_replay.py app-before.py [case ...] > red.json
"""
import json
import os
from pathlib import Path
import subprocess
import sys

here=Path(__file__).resolve().parent
source=Path(sys.argv[1]).read_text()
payload={'app':source,'test':(here/'replay_ui.py').read_text(),'cases':sys.argv[2:]}
bootstrap='''import json,pathlib,shutil,subprocess,sys,tempfile
p=json.load(sys.stdin)
root=pathlib.Path.home()/'.openclaw/workspace/skills/supply-chain-control-tower'
with tempfile.TemporaryDirectory(prefix='pi-panel-minfix-') as d:
 t=pathlib.Path(d)
 for name in ('panel','scripts','data'): (t/name).mkdir()
 (t/'panel/app.py').write_text(p['app'])
 (t/'replay_ui.py').write_text(p['test'])
 shutil.copy2(root/'scripts/tools.py',t/'scripts/tools.py')
 for f in (root/'data').iterdir():
  if f.is_file() and f.suffix in ('.csv','.json'): shutil.copy2(f,t/'data'/f.name)
 r=subprocess.run([sys.executable,'-B',str(t/'replay_ui.py'),str(t/'panel/app.py')]+p['cases'],capture_output=True,text=True,timeout=180)
 sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)
'''
cmd=['ssh','-T','-S',os.environ.get('DGX_SOCKET','/tmp/dgx-spark-master.sock'),
     '-o','BatchMode=yes','-o','ProxyCommand=false',os.environ['DGX_TARGET']]
import shlex
p=subprocess.run(cmd+['python3 -B -c '+shlex.quote(bootstrap)],input=json.dumps(payload),text=True,capture_output=True,timeout=200)
sys.stdout.write(p.stdout);sys.stderr.write(p.stderr);sys.exit(p.returncode)
