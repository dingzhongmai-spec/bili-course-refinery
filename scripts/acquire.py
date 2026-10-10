"""Acquire one accessible public Bilibili lecture through the pinned upstream parser."""
import argparse
import json
import re
import shutil
import subprocess
import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import activate


def main():
    cfg = activate()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bvid', required=True)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--work', required=True)
    p.add_argument('--probe-only', action='store_true')
    args = p.parse_args()
    if not re.fullmatch(r'BV[A-Za-z0-9]{10}', args.bvid) or args.page < 1:
        raise ValueError('Invalid BV or page')
    repo = cfg.get('downloader', {}).get('path')
    if not repo:
        raise ValueError('Run install.ps1 before acquisition')
    # Upstream debug logs may include session cookies. Suppress them in this adapter.
    logging.disable(logging.CRITICAL)
    local_data = Path(repo).parent / 'upstream-data'
    local_data.mkdir(exist_ok=True)
    os.environ['APPDATA'] = os.environ['LOCALAPPDATA'] = str(local_data)
    sys.path.insert(0, repo)
    import _pathsetup
    from config import ConfigLoader
    import bilibili_parser
    from bilibili_parser import BilibiliParser
    work = Path(args.work).resolve()
    folder = work / 'media' / f'{args.bvid}-p{args.page:02d}'
    folder.mkdir(parents=True, exist_ok=True)
    cache = folder / 'cache'
    cache.mkdir(exist_ok=True)
    # Public streams need no DRM tooling; keep the upstream's auxiliary cache local.
    bilibili_parser.get_tool_manager = None
    bilibili_parser.get_safe_temp_dir = lambda *a, **k: str(cache)
    parser = BilibiliParser(ConfigLoader(), cookie_path=str(Path(repo) / 'public-course-cookie.txt'))
    parser.ffmpeg_local = cfg['tools']['ffmpeg']
    response = parser.session.get('https://api.bilibili.com/x/web-interface/view', params={'bvid': args.bvid}, timeout=30)
    response.raise_for_status()
    view = response.json()
    if view.get('code') != 0:
        raise ValueError('Source metadata unavailable: ' + str(view.get('message')))
    data = view['data']
    pages = data['pages']
    if args.page > len(pages):
        raise ValueError('Requested page not found')
    page = pages[args.page - 1]
    cid, duration = page['cid'], page['duration']
    if data.get('rights', {}).get('is_stein_gate') or data.get('rights', {}).get('is_upower_exclusive'):
        raise ValueError('Interactive or restricted content is outside the public lecture adapter')
    source = {'bvid': args.bvid, 'page': args.page, 'cid': cid, 'duration_seconds': duration,
        'title': page.get('part') or data['title'], 'author': data['owner']['name'],
        'url': f'https://www.bilibili.com/video/{args.bvid}/?p={args.page}', 'status': 'metadata_only'}
    (folder / 'source.json').write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.probe_only:
        print(json.dumps(source, ensure_ascii=False))
        return
    play = parser._get_play_info('video', args.bvid, cid, False)
    if not play.get('success') or play.get('kid'):
        raise ValueError('No public unprotected stream available')
    candidates = [(k, v) for k, v in play.get('video_urls', {}).items() if isinstance(k, int)]
    if not candidates:
        raise ValueError('No public video stream')
    video_url = min(candidates, key=lambda pair: abs(pair[0] - 64))[1]
    for kind, url, filename in [('video', video_url, 'video.mp4'), ('audio', play.get('audio_url'), 'audio.m4a')]:
        if not url:
            continue
        target = folder / filename
        if target.exists():
            raise ValueError(f'Existing media preserved: {target}; validate it or choose a new work directory')
        actual = Path(parser.download_file(url, str(target), lambda *a: None, kind, args.bvid))
        if actual.resolve() != target.resolve():
            shutil.move(str(actual), str(target))
    if not (folder / 'audio.m4a').exists():
        subprocess.run([cfg['tools']['ffmpeg'], '-v', 'error', '-nostdin', '-n', '-i', str(folder / 'video.mp4'), '-vn', '-c:a', 'aac', str(folder / 'audio.m4a')], check=True)
    for filename in ('video.mp4', 'audio.m4a'):
        output = subprocess.check_output([cfg['tools']['ffprobe'], '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(folder / filename)], text=True, encoding='utf-8')
        actual_duration = float(json.loads(output)['format']['duration'])
        if abs(actual_duration - duration) > max(3, duration * .02):
            raise ValueError(f'Duration mismatch in {filename}; do not mark acquisition complete')
    source['status'] = 'media_duration_checked'
    (folder / 'source.json').write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(source, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'ACQUIRE_FAILED: {exc}', file=sys.stderr)
        raise SystemExit(1)
