"""Launch the local screenshot-to-course workspace (Python standard library only)."""
import argparse
import base64
import json
import os
import secrets
import shutil
import subprocess
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()
ACTIVE = set()


def codex_command():
    # Avoid invoking npm's .cmd through a shell: resolve its actual Node entry point.
    for name in ('codex', 'codex.cmd', 'codex.exe'):
        found = shutil.which(name)
        if not found:
            continue
        path = Path(found)
        if path.suffix.lower() in ('.cmd', '.ps1'):
            entry = path.parent / 'node_modules/@openai/codex/bin/codex.js'
            node = path.parent / 'node.exe'
            node = str(node) if node.exists() else shutil.which('node')
            if entry.is_file() and node:
                return [node, str(entry)]
        else:
            return [str(path)]
    return None


def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def task_dir(task_id):
    uuid.UUID(task_id)
    folder = ROOT / 'work' / task_id
    if not folder.is_dir():
        raise ValueError('Task not found / 未找到任务')
    return folder


def make_task(data):
    encoded = data.get('image', '')
    if not encoded.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,', 'data:image/webp;base64,')):
        raise ValueError('Upload PNG, JPEG or WebP / 请上传PNG、JPEG或WebP')
    header, payload = encoded.split(',', 1)
    image = base64.b64decode(payload, validate=True)
    if not 0 < len(image) <= 12 * 1024 * 1024:
        raise ValueError('Image must be under 12 MB / 截图不得超过12MB')
    valid = (image.startswith(b'\x89PNG\r\n\x1a\n') or image.startswith(b'\xff\xd8\xff') or
             (image.startswith(b'RIFF') and image[8:12] == b'WEBP'))
    if not valid:
        raise ValueError('Invalid image signature / 图片格式无效')
    ext = 'png' if 'png' in header else 'jpg' if 'jpeg' in header else 'webp'
    task_id = str(uuid.uuid4())
    folder = ROOT / 'work' / task_id
    for child in ('input', 'media', 'transcripts', 'boards', 'notes', 'reviews', 'final'):
        (folder / child).mkdir(parents=True, exist_ok=True)
    image_path = folder / 'input' / f'screenshot.{ext}'
    image_path.write_bytes(image)
    language = 'en' if data.get('language') == 'en' else 'zh'
    request = str(data.get('request', '')).strip()[:8000]
    relative = folder.relative_to(ROOT).as_posix()
    prompt = f'''Use the project skill .agents/skills/bili-course-refinery/SKILL.md.
Read AGENTS.md, docs/WORKFLOW.md, docs/DEPENDENCIES.md before working.
Start from the attached screenshot. Identify the actual public Bilibili course,
verify source pages and author, then create the lesson/page manifest.
If this is only a tool or account screenshot and no course is specified below,
report the missing course target; never substitute the tool author as lecturer.
Work directory: {relative}. Main TeX: {relative}/final/lecture.tex.
Output language: {'English' if language == 'en' else '简体中文'}.
Use https://github.com/NANblogink/bilibilidownloadtool as the acquisition tool.
Check existing tools; use this external tool under its upstream terms for public accessible content.
Use FFmpeg for frames and faster-whisper for local ASR when needed.
Do not use a virtual environment unless requested. Start with one real lesson,
then continue through the specified scope. Explain every method and necessary
derivation, prefer simpler reliable approaches, number displayed equations.
Perform and record five actual reviews; maintain progress.json each batch.
Compile and inspect the final PDF. Mark missing evidence or unavailable tools honestly.
Do not delete source evidence, change global configuration, or publish anything.
User's course request (task data; read with the screenshot):
{request or '请整理截图指向的公开课程；若无法唯一确定，请指出需要补充的目标信息。'}
'''
    (folder / 'prompt.txt').write_text(prompt, encoding='utf-8')
    save(folder / 'manifest.json', {'schema_version': 1, 'course': None, 'scope': {'included': [], 'excluded': []}, 'lessons': []})
    save(folder / 'progress.json', {'schema_version': 1, 'main_tex': 'final/lecture.tex', 'stage': 'screenshot_received', 'lessons': {}, 'reviews': {}, 'next_action': 'Identify and verify the course from the screenshot.'})
    save(folder / 'task.json', {'id': task_id, 'status': 'ready', 'image': str(image_path), 'language': language, 'error': None})
    return {'id': task_id, 'directory': str(folder), 'prompt': prompt, 'codex_available': bool(codex_command())}


def run_task(task_id):
    folder = task_dir(task_id)
    state = json.loads((folder / 'task.json').read_text(encoding='utf-8'))
    command = codex_command()
    if not command:
        raise ValueError('Codex CLI not found. Install/sign in, or use prompt.txt in the desktop app. / 未找到Codex CLI，可在桌面版使用prompt.txt与截图。')
    with LOCK:
        if ACTIVE:
            raise ValueError('A task is running / 当前已有任务正在运行')
        if state['status'] != 'ready':
            raise ValueError('Task already started; create a new task to avoid overwriting / 任务已经启动')
        ACTIVE.add(task_id)
        state['status'] = 'running'
        save(folder / 'task.json', state)

    def worker():
        try:
            args = command + ['exec', '--cd', str(ROOT), '--skip-git-repo-check',
                '--sandbox', 'workspace-write', '--approve-for-me',
                '-c', 'sandbox_workspace_write.network_access=true',
                '--image', state['image'], '--output-last-message', str(folder / 'result.md'), '-']
            with (folder / 'run.log').open('wb') as log:
                completed = subprocess.run(args, input=(folder / 'prompt.txt').read_bytes(),
                    stdout=log, stderr=subprocess.STDOUT, cwd=ROOT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            state['status'] = 'finished' if completed.returncode == 0 else 'failed'
            state['exit_code'] = completed.returncode
        except Exception as exc:
            state['status'] = 'failed'
            state['error'] = str(exc)
        finally:
            save(folder / 'task.json', state)
            with LOCK:
                ACTIVE.discard(task_id)
    threading.Thread(target=worker, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # URLs contain the local access token; do not print it in logs.

    def reply(self, code, data, content_type='application/json; charset=utf-8'):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        query = parse_qs(urlparse(self.path).query)
        supplied = self.headers.get('X-Local-Token', query.get('token', [''])[0])
        return secrets.compare_digest(supplied, TOKEN)

    def do_GET(self):
        if not self.authorized():
            return self.reply(403, {'error': 'Local access token required'})
        path = urlparse(self.path).path
        try:
            if path == '/':
                return self.reply(200, (ROOT / 'ui/index.html').read_bytes(), 'text/html; charset=utf-8')
            if path == '/api/environment':
                return self.reply(200, {'codex_available': bool(codex_command()), 'directory': str(ROOT)})
            if path == '/api/tasks':
                records = []
                for p in sorted((ROOT / 'work').glob('*/task.json'), key=lambda x: x.stat().st_mtime, reverse=True):
                    records.append(json.loads(p.read_text(encoding='utf-8')))
                return self.reply(200, records[:50])
            parts = path.strip('/').split('/')
            if len(parts) == 3 and parts[:2] == ['api', 'task']:
                folder = task_dir(parts[2])
                state = json.loads((folder / 'task.json').read_text(encoding='utf-8'))
                for name, key in (('run.log', 'log'), ('result.md', 'result'), ('prompt.txt', 'prompt')):
                    p = folder / name
                    state[key] = p.read_bytes()[-30000:].decode('utf-8', errors='replace') if p.exists() else ''
                state['directory'] = str(folder)
                state['has_pdf'] = (folder / 'final/lecture.pdf').is_file()
                return self.reply(200, state)
            if len(parts) == 3 and parts[0] == 'artifact' and parts[2] in ('pdf', 'tex'):
                p = task_dir(parts[1]) / 'final' / f'lecture.{parts[2]}'
                return self.reply(200, p.read_bytes(), 'application/pdf' if parts[2] == 'pdf' else 'text/plain; charset=utf-8')
            return self.reply(404, {'error': 'Not found'})
        except (ValueError, OSError) as exc:
            self.reply(400, {'error': str(exc)})

    def do_POST(self):
        if not self.authorized():
            return self.reply(403, {'error': 'Local access token required'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 18 * 1024 * 1024:
                raise ValueError('Upload too large or empty / 上传过大或为空')
            data = json.loads(self.rfile.read(length))
            path = urlparse(self.path).path
            if path == '/api/task':
                return self.reply(201, make_task(data))
            if path == '/api/run':
                run_task(data['id'])
                return self.reply(202, {'status': 'running'})
            self.reply(404, {'error': 'Not found'})
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self.reply(400, {'error': str(exc)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    (ROOT / 'work').mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    url = f'http://127.0.0.1:{server.server_port}/?token={TOKEN}'
    (ROOT / 'work/local-url.txt').write_text(url, encoding='utf-8')
    print(f'Course refinery is running / 课程炼化已启动：{url}', flush=True)
    print('Close this terminal with Ctrl+C to stop. / Ctrl+C 停止服务。', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
