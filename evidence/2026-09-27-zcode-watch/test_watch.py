"""Tests only the owner-visible sampling/report seam, on isolated fixture trees."""
import datetime as dt
import hashlib
import importlib.util
import tempfile
import unittest
import socket
import subprocess
import json
from pathlib import Path

from pypdf import PdfReader

spec = importlib.util.spec_from_file_location("zcode_watch", Path(__file__).with_name("watch.py"))
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)

NOW = dt.datetime(2026, 9, 26, 23, 0, tzinfo=dt.timezone.utc)
END = dt.datetime(2026, 9, 27, 9, 39, tzinfo=dt.timezone.utc)


class ReportBoundary(unittest.TestCase):
    def test_no_channel_produces_honest_readonly_chinese_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            source = root / "STATUS.md"
            source.write_text("PARTIAL\nprivate-canary-not-for-report\n")
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            out = Path(temp) / "output"
            state = watch.observe(root, out, END, Path(temp) / "no-socket", now=NOW)
            self.assertEqual(state["remote"]["status"], "REMOTE_UNOBSERVED")
            self.assertEqual(state["samples"], 1)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            text = "\n".join(page.extract_text() for page in PdfReader(out / "ZCODE-DGX-REPORT.pdf").pages)
            self.assertIn("远端未观测", text)
            self.assertIn("作者未知", text)
            for artifact in out.glob("*"):
                if artifact.is_file():
                    self.assertNotIn(b"private-canary-not-for-report", artifact.read_bytes())


class MonitoringBoundary(unittest.TestCase):
    def test_remote_change_is_observed_but_never_attributed_to_zcode(self):
        with tempfile.TemporaryDirectory() as temp:
            root, out = Path(temp)/'repo', Path(temp)/'out'
            root.mkdir()
            values = iter([
                {'status':'OBSERVED','arch':'aarch64','gateway':'active','pid':10,'panel_http':200,'files':{}},
                {'status':'OBSERVED','arch':'aarch64','gateway':'active','pid':11,'panel_http':200,'files':{}},
            ])
            probe = lambda _: next(values)
            watch.observe(root,out,END,now=NOW,probe=probe)
            state = watch.observe(root,out,END,now=NOW+dt.timedelta(minutes=5),probe=probe)
            self.assertEqual(state['remote_samples'],2)
            self.assertEqual(state['remote_change_count'],1)
            self.assertTrue(any(c['path']=='DGX/gateway_pid' for c in state['recent_changes']))
            self.assertIn('作者未知',(out/'ZCODE-DGX-REPORT.md').read_text())

    def test_deadline_stops_before_any_new_scan_or_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out=Path(temp)/'repo',Path(temp)/'out'
            root.mkdir()
            def forbidden_probe(_):
                raise AssertionError('probe after deadline')
            state=watch.observe(root,out,END,now=END,probe=forbidden_probe)
            self.assertEqual(state['status'],'STOPPED_DEADLINE')
            self.assertFalse(state['active'])
            self.assertEqual(state['samples'],0)
            self.assertFalse((out/'events.jsonl').exists())

    def test_file_changes_are_readonly_and_sampling_gaps_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out=Path(temp)/'repo',Path(temp)/'out'
            root.mkdir()
            source=root/'STATUS.md'
            source.write_text('version one')
            no_socket=Path(temp)/'none'
            watch.observe(root,out,END,no_socket,now=NOW)
            source.write_text('version two')
            state=watch.observe(root,out,END,no_socket,now=NOW+dt.timedelta(minutes=20))
            self.assertEqual(state['change_count'],1)
            self.assertEqual(state['gap_count'],1)
            self.assertEqual(source.read_text(),'version two')
            self.assertEqual(state['recent_changes'][0]['path'],'STATUS.md')

    def test_symlinked_source_never_read_or_copied(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out=Path(temp)/'repo',Path(temp)/'out'
            root.mkdir()
            external=Path(temp)/'outside'
            external.write_text('do-not-read-or-copy-this-canary')
            (root/'STATUS.md').symlink_to(external)
            state=watch.observe(root,out,END,Path(temp)/'none',now=NOW)
            self.assertEqual(state['files']['STATUS.md']['status'],'SYMLINK_REJECTED')
            for file in out.glob('*'):
                if file.is_file():
                    self.assertNotIn(b'do-not-read-or-copy-this-canary',file.read_bytes())

    def test_changed_watched_code_is_not_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out=Path(temp)/'repo',Path(temp)/'out'
            source=root/'skills/supply-chain-control-tower/panel/app.py'
            source.parent.mkdir(parents=True)
            marker=Path(temp)/'executed'
            source.write_text('raise RuntimeError("first version")')
            no_socket=Path(temp)/'none'
            watch.observe(root,out,END,no_socket,now=NOW)
            source.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("bad")')
            state=watch.observe(root,out,END,no_socket,now=NOW+dt.timedelta(minutes=5))
            self.assertEqual(state['change_count'],1)
            self.assertFalse(marker.exists())
            self.assertTrue(any(i[0]=='REVIEW' for i in state['issues']))

    def test_deeply_malformed_receipt_does_not_kill_monitor(self):
        with tempfile.TemporaryDirectory() as temp:
            root,out=Path(temp)/'repo',Path(temp)/'out'
            receipt=root/watch.CASES[0]
            receipt.parent.mkdir(parents=True)
            receipt.write_text('['*20000+'0'+']'*20000)
            state=watch.observe(root,out,END,Path(temp)/'none',now=NOW)
            self.assertEqual(state['cases'][0]['text_check'],'INVALID_RECEIPT')
            self.assertTrue(state['active'])


class RemoteBoundary(unittest.TestCase):
    def test_existing_master_is_only_transport_and_response_is_allowlisted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'master.sock'
            master = socket.socket(socket.AF_UNIX)
            self.addCleanup(master.close)
            master.bind(str(path))
            calls = []
            def fake_transport(args, **kwargs):
                calls.append(args)
                if '-O' in args:
                    return subprocess.CompletedProcess(args, 0, 'Master running', '')
                payload = {'user': 'sparker', 'arch': 'aarch64', 'gateway': 'active',
                           'pid': 123, 'panel_http': 200, 'files': {},
                           'secret': 'remote-canary-must-not-persist'}
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), '')
            result = watch.probe_remote(path, run=fake_transport)
            self.assertEqual(result['status'], 'OBSERVED')
            self.assertEqual(result['pid'], 123)
            self.assertEqual(len(calls), 2)
            self.assertNotIn('remote-canary-must-not-persist', json.dumps(result))
            self.assertTrue(all('ProxyCommand=false' in args and 'BatchMode=yes' in args for args in calls))

    def test_absent_socket_never_dials_and_failed_master_never_runs_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            def must_not_dial(*args,**kwargs):
                raise AssertionError('unexpected transport')
            self.assertEqual(watch.probe_remote(Path(temp)/'absent',run=must_not_dial)['status'],'REMOTE_UNOBSERVED')
            path=Path(temp)/'master.sock'
            master=socket.socket(socket.AF_UNIX)
            self.addCleanup(master.close)
            master.bind(str(path))
            calls=[]
            def failed(args,**kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(args,255,'','auth-canary-must-not-copy')
            result=watch.probe_remote(path,run=failed)
            self.assertEqual(len(calls),1)
            self.assertEqual(result['reason'],'MASTER_CHECK_FAILED')
            self.assertNotIn('auth-canary',json.dumps(result))


if __name__ == "__main__":
    unittest.main()
