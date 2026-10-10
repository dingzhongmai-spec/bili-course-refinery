"""Install and validate a local course-refinery runtime without a virtualenv."""
import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import struct
import sys
import site
import tarfile
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'
DOWNLOADER_COMMIT = 'ad6a40f75a66082dd7884fec3cf01decf927021f'


def say(message):
    print(message, flush=True)
    with (RUNTIME / 'install.log').open('a', encoding='utf-8') as log:
        log.write(message + '\n')


def run(args, **kwargs):
    say('> ' + ' '.join(map(str, args)))
    with (RUNTIME / 'install.log').open('ab') as log:
        completed = subprocess.run(list(map(str, args)), stdout=log, stderr=subprocess.STDOUT,
                                   env=os.environ.copy(), **kwargs)
    if completed.returncode:
        raise RuntimeError(f'Command failed ({completed.returncode}); see {RUNTIME / "install.log"}')


def fetch_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'bili-course-refinery-setup'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def file_sha256(stream):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def download(url, target, digest):
    if not digest or not digest.startswith('sha256:'):
        raise ValueError('Upstream SHA-256 digest is required')
    expected = digest.split(':', 1)[1]
    if target.is_file():
        with target.open('rb') as stream:
            if file_sha256(stream) == expected:
                return
    temp = target.with_suffix(target.suffix + '.part')
    for attempt in range(3):
        try:
            say(f'Download / 下载: {url}')
            request = urllib.request.Request(url, headers={'User-Agent': 'bili-course-refinery-setup'})
            with urllib.request.urlopen(request, timeout=45) as response, temp.open('wb') as output:
                last_report = time.monotonic()
                while block := response.read(1024 * 1024):
                    output.write(block)
                    if time.monotonic() - last_report > 10:
                        say(f'  {output.tell() // (1024 * 1024)} MB received / 已下载')
                        last_report = time.monotonic()
            with temp.open('rb') as stream:
                actual = file_sha256(stream)
            if actual != expected:
                raise ValueError('Downloaded file SHA-256 mismatch; refusing to execute it')
            temp.replace(target)
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def unpack(archive, target):
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    if archive.suffix == '.zip':
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                dest = (root / item.filename).resolve()
                if not dest.is_relative_to(root):
                    raise ValueError('Archive path escapes extraction directory')
            z.extractall(root)
    else:
        with tarfile.open(archive) as t:
            for item in t.getmembers():
                if item.issym() or item.islnk() or not (root / item.name).resolve().is_relative_to(root):
                    raise ValueError('Unsafe archive member')
            t.extractall(root, filter='data')


def tool_release(repo, tag, name, executable, config):
    destination = RUNTIME / 'tools' / executable
    extension = '.exe' if os.name == 'nt' else ''
    existing = list(destination.rglob(executable + extension)) if destination.is_dir() else []
    if existing:
        return str(existing[0])
    # Locked immutable release assets avoid anonymous GitHub API rate limits.
    lock = json.loads((ROOT / 'tool-lock.json').read_text(encoding='utf-8'))
    asset = lock[name]
    archive = RUNTIME / 'downloads' / asset['name']
    download(asset['browser_download_url'], archive, asset.get('digest'))
    unpack(archive, destination)
    found = next(destination.rglob(executable + extension))
    if os.name != 'nt':
        found.chmod(found.stat().st_mode | 0o111)
    config['downloads'].append({'source': repo, 'tag': asset['tag_name'], 'asset': name, 'digest': asset['digest']})
    return str(found)


def configure_tools(config, portable):
    if os.name != 'nt' or struct.calcsize('P') != 8:
        raise ValueError(f'Automatic setup needs 64-bit Windows Python; detected {os.name}, {struct.calcsize("P") * 8} bit')
    ffmpeg = None if portable else shutil.which('ffmpeg')
    ffprobe = None if portable else shutil.which('ffprobe')
    if not (ffmpeg and ffprobe):
        ffmpeg = tool_release('GyanD/codexffmpeg', 'tags/9.0.2',
            'ffmpeg-9.0.2-essentials_build.zip', 'ffmpeg', config)
        ffprobe = str(Path(ffmpeg).with_name('ffprobe.exe'))
    config['tools']['ffmpeg'], config['tools']['ffprobe'] = ffmpeg, ffprobe
    xelatex = None if portable else shutil.which('xelatex')
    tectonic = None if portable else shutil.which('tectonic')
    if not xelatex and not tectonic:
        tectonic = tool_release('tectonic-typesetting/tectonic', 'tags/tectonic%400.17.0',
            'tectonic-0.17.0-x86_64-pc-windows-msvc.zip', 'tectonic', config)
    config['tools']['tex'] = xelatex or tectonic
    config['tex_engine'] = 'xelatex' if xelatex else 'tectonic'
    config['bin_dirs'] = list(dict.fromkeys([str(Path(sys.executable).parent)] + [str(Path(v).parent) for v in config['tools'].values()]))


def install_codex(config):
    from launch import codex_command
    existing = codex_command()
    if existing:
        config['codex_command'] = existing
        return
    node = shutil.which('node')
    if not node:
        base = 'https://nodejs.org/dist/latest-v22.x/'
        with urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=60) as response:
            lines = response.read().decode().splitlines()
        name = next(row.split()[-1] for row in lines if row.split()[-1].endswith('-win-x64.zip'))
        digest = next(row.split()[0] for row in lines if row.split()[-1] == name)
        archive = RUNTIME / 'downloads' / name
        download(base + name, archive, 'sha256:' + digest)
        unpack(archive, RUNTIME / 'tools/node')
        node = str(next((RUNTIME / 'tools/node').rglob('node.exe')))
    npm = Path(node).parent / 'node_modules/npm/bin/npm-cli.js'
    if not npm.is_file():
        raise RuntimeError('Node found but npm entry is missing; repair your Node installation')
    run([node, npm, 'install', '--prefix', RUNTIME / 'codex', '@openai/codex'])
    config['codex_command'] = [node, str(RUNTIME / 'codex/node_modules/@openai/codex/bin/codex.js')]
    config['bin_dirs'].append(str(Path(node).parent))


def install_downloader(config):
    repo = RUNTIME / 'tools/bilibilidownloadtool'
    if not (repo / '.git').is_dir():
        run(['git', 'clone', '--filter=blob:none', '--no-checkout',
             'https://github.com/NANblogink/bilibilidownloadtool.git', repo])
        run(['git', '-C', repo, 'sparse-checkout', 'set', 'core', 'parsers', 'assets'])
        run(['git', '-C', repo, 'checkout', DOWNLOADER_COMMIT])
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != DOWNLOADER_COMMIT:
        raise ValueError('Downloader checkout differs from tested commit; preserve it and resolve manually')
    config['downloader'] = {'path': str(repo), 'commit': revision,
                            'source': 'https://github.com/NANblogink/bilibilidownloadtool'}


def model_and_packages(config, refresh):
    packages = RUNTIME / 'packages'
    if refresh or not (RUNTIME / 'packages-ready.json').exists():
        run([sys.executable, '-m', 'pip', '--isolated', 'install', '--index-url', 'https://pypi.org/simple', '--timeout', '30', '--retries', '2', '--ignore-installed', '--target', packages, '--upgrade',
             '-r', ROOT / 'requirements-runtime.txt'])
        (RUNTIME / 'packages-ready.json').write_text(json.dumps({'python': sys.version}), encoding='utf-8')
    sys.path.insert(0, str(packages))
    site.addsitedir(str(packages))
    os.environ['PYTHONPATH'] = str(packages)
    os.environ['HF_HOME'] = str(RUNTIME / 'cache/huggingface')
    # Standard HTTPS works on networks that block Hugging Face's extra Xet hosts.
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '60'
    from huggingface_hub import snapshot_download
    revision = config.get('asr_revision')
    if not revision:
        revision = fetch_json('https://huggingface.co/api/models/Systran/faster-whisper-small')['sha']
    say('Preparing local ASR model / 准备本地small转写模型（首次约几百MB）')
    config['asr_revision'] = revision
    config['status'] = 'installing_model'
    (RUNTIME / 'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    model = snapshot_download('Systran/faster-whisper-small', revision=revision,
        local_dir=RUNTIME / 'models/small', allow_patterns=['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.*', '*.txt'])
    config['asr_model'], config['asr_revision'] = model, revision


def validate(config):
    say('Verifying media, model imports and Chinese PDF / 验证媒体、模型导入与中文PDF')
    for tool in ('ffmpeg', 'ffprobe'):
        run([config['tools'][tool], '-version'])
    media = RUNTIME / 'selftest/media'
    media.mkdir(parents=True, exist_ok=True)
    run([config['tools']['ffmpeg'], '-v', 'error', '-nostdin', '-y', '-f', 'lavfi',
        '-i', 'testsrc=size=320x240:rate=10:duration=1', '-pix_fmt', 'yuv420p', str(media / 'sample.mp4')])
    probe = subprocess.check_output([config['tools']['ffprobe'], '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(media / 'sample.mp4')], text=True, encoding='utf-8')
    if abs(float(json.loads(probe)['format']['duration']) - 1) > .1:
        raise ValueError('Media duration self-test failed')
    run([config['tools']['ffmpeg'], '-v', 'error', '-nostdin', '-y', '-ss', '0.2', '-i', str(media / 'sample.mp4'), '-frames:v', '1', str(media / 'frame.png')])
    run([sys.executable, '-c', 'from runtime import activate; activate(); import faster_whisper, fitz, PyQt5, requests, curl_cffi, cryptography, orjson'], cwd=ROOT)
    # Load the local model to ensure its data and inference runtime work, without cloud speech services.
    run([sys.executable, '-c', 'from runtime import activate; activate(); from faster_whisper import WhisperModel; import sys; WhisperModel(sys.argv[1],device="cpu",compute_type="int8"); print("ASR_MODEL_READY")', config['asr_model']], cwd=ROOT)
    run([sys.executable, '-c', 'from runtime import activate; activate(); import sys; sys.path.insert(0,sys.argv[1]); import _pathsetup; from bilibili_parser import BilibiliParser; from config import ConfigLoader; print("DOWNLOADER_IMPORT_READY")', config['downloader']['path']], cwd=ROOT)
    output = RUNTIME / 'selftest/pdf'
    output.mkdir(parents=True, exist_ok=True)
    if config['tex_engine'] == 'tectonic':
        run([config['tools']['tex'], '--keep-logs', '--outdir', output, ROOT / 'templates/lecture.tex'])
    else:
        for _ in range(2):
            run([config['tools']['tex'], '-interaction=nonstopmode', '-halt-on-error', '-output-directory', output, ROOT / 'templates/lecture.tex'])
    run([sys.executable, '-c', 'import fitz,sys; d=fitz.open(sys.argv[1]); text="".join(p.get_text() for p in d); assert "换元" in text and len(d)>0; print("CHINESE_PDF_READY")', output / 'lecture.pdf'])
    result = subprocess.run(config['codex_command'] + ['login', 'status'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    config['codex_logged_in'] = result.returncode == 0
    config['verified'] = {'media': True, 'asr_model_load': True, 'downloader_import': True, 'chinese_pdf': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-launch', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--portable-tools', action='store_true', help='Test downloaded tools even when system tools exist')
    args = parser.parse_args()
    for child in ('downloads', 'tools', 'cache', 'models', 'selftest'):
        (RUNTIME / child).mkdir(parents=True, exist_ok=True)
    os.environ['PYTHONUTF8'], os.environ['PYTHONIOENCODING'] = '1', 'utf-8'
    config_path = RUNTIME / 'config.json'
    old = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    config = {'schema_version': 1, 'python': sys.executable, 'python_version': sys.version,
              'tools': {}, 'downloads': old.get('downloads', []), 'bin_dirs': [],
              'asr_revision': old.get('asr_revision')}
    if (ROOT / '.git').exists():
        config['project_commit'] = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    else:
        build = (ROOT / 'BUILD_INFO.txt').read_text(encoding='utf-8') if (ROOT / 'BUILD_INFO.txt').exists() else ''
        match = re.search(r'Commit: ([0-9a-f]{40})\b', build)
        config['project_commit'] = match.group(1) if match else 'ZIP/unknown'
    config['project_version'] = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    try:
        configure_tools(config, args.portable_tools)
        os.environ['PATH'] = os.pathsep.join(config['bin_dirs'] + [os.environ['PATH']])
        install_codex(config)
        install_downloader(config)
        model_and_packages(config, args.refresh)
        config['status'] = 'validating'
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
        validate(config)
        config['status'] = 'ready'
        config['installed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
        versions = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '--path', str(RUNTIME / 'packages'), '--format=json'], text=True, encoding='utf-8')
        (RUNTIME / 'package-versions.json').write_text(versions, encoding='utf-8')
        say('INSTALL_READY / 安装验证完成')
        if not config['codex_logged_in']:
            say('Codex needs your login / Codex需要本人首次登录')
            if not args.no_launch:
                subprocess.run(config['codex_command'] + ['login'], check=True)
        if not args.no_launch:
            subprocess.run([sys.executable, '-X', 'utf8', ROOT / 'launch.py'], check=True)
    except Exception as exc:
        config['status'], config['error'] = 'failed', str(exc)
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
        say('INSTALL_FAILED / 安装未完成: ' + str(exc))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
