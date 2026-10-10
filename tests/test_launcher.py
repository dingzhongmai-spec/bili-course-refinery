"""Local HTTP and task execution checks; no live Codex calls or account usage."""
import base64
import http.client
import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launch

PNG = 'data:image/png;base64,' + base64.b64encode(bytes.fromhex('89504e470d0a1a0a') + b'test').decode()


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'work').mkdir()
        shutil.copytree(launch.ROOT / 'ui', self.root / 'ui')
        self.root_patch = patch.object(launch, 'ROOT', self.root)
        self.root_patch.start()
        self.server = launch.ThreadingHTTPServer(('127.0.0.1', 0), launch.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.root_patch.stop()
        self.temp.cleanup()

    def request(self, method, path, data=None, authorized=True):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type': 'application/json'}
        if authorized:
            headers['X-Local-Token'] = launch.TOKEN
        conn.request(method, path, json.dumps(data).encode() if data else None, headers)
        response = conn.getresponse()
        status, body = response.status, response.read()
        conn.close()
        return status, json.loads(body)

    def test_requires_local_token(self):
        self.assertEqual(self.request('POST', '/api/task', {'image': PNG}, False)[0], 403)
        self.assertEqual(list((self.root / 'work').iterdir()), [])

    def test_upload_persists_without_claiming_review(self):
        status, task = self.request('POST', '/api/task', {'image': PNG, 'request': '目标课程'})
        self.assertEqual(status, 201)
        folder = launch.task_dir(task['id'])
        self.assertTrue((folder / 'input/screenshot.png').exists())
        progress = json.loads((folder / 'progress.json').read_text(encoding='utf-8'))
        self.assertEqual(progress['stage'], 'screenshot_received')
        self.assertEqual(progress['lessons'], {})
        self.assertIn('目标课程', (folder / 'prompt.txt').read_text(encoding='utf-8'))
        self.assertEqual(self.request('GET', '/api/tasks')[1][0]['id'], task['id'])

    def test_invalid_image_rejected(self):
        invalid = 'data:image/png;base64,' + base64.b64encode(b'not an image').decode()
        self.assertEqual(self.request('POST', '/api/task', {'image': invalid})[0], 400)

    def test_missing_cli_keeps_desktop_task(self):
        task = launch.make_task({'image': PNG})
        with patch.object(launch, 'codex_command', return_value=None):
            self.assertEqual(self.request('POST', '/api/run', {'id': task['id']})[0], 400)
        self.assertEqual(self.request('GET', '/api/task/' + task['id'])[1]['status'], 'ready')

    def test_exec_attaches_image_and_reads_prompt_from_stdin(self):
        fake = self.root / 'fake.py'
        fake.write_text('import sys,json\nfrom pathlib import Path\na=sys.argv[1:]\np=Path(a[a.index("--output-last-message")+1])\np.write_text("stub result",encoding="utf-8")\np.with_name("trace.json").write_text(json.dumps({"args":a,"prompt":sys.stdin.buffer.read().decode("utf-8")}),encoding="utf-8")\n', encoding='utf-8')
        task = launch.make_task({'image': PNG, 'request': '仅测试接线', 'language': 'en'})
        with patch.object(launch, 'codex_command', return_value=[sys.executable, str(fake)]):
            self.assertEqual(self.request('POST', '/api/run', {'id': task['id']})[0], 202)
            for _ in range(100):
                status = self.request('GET', '/api/task/' + task['id'])[1]
                if status['status'] != 'running':
                    break
                time.sleep(.05)
        self.assertEqual(status['status'], 'finished')
        self.assertEqual(status['result'], 'stub result')
        trace = json.loads((launch.task_dir(task['id']) / 'trace.json').read_text(encoding='utf-8'))
        self.assertTrue(Path(trace['args'][trace['args'].index('--image') + 1]).is_file())
        self.assertIn('仅测试接线', trace['prompt'])
        self.assertEqual(trace['args'][-1], '-')
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', trace['args'])
        self.assertEqual(self.request('POST', '/api/run', {'id': task['id']})[0], 400)


if __name__ == '__main__':
    unittest.main()
