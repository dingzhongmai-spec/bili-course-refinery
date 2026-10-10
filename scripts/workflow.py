"""Portable workflow helpers. Checks structure, never certifies course review."""
import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def doctor(_):
    print(json.dumps({
        'python': sys.version.split()[0], 'executable': sys.executable,
        'platform': platform.platform(),
        'tools': {name: shutil.which(name) for name in
                  ('ffmpeg', 'ffprobe', 'xelatex', 'latexmk', 'wolframscript')},
        'note': 'Missing optional tools do not block init/check. Availability is not a runtime test.'
    }, ensure_ascii=False, indent=2))


def init(args):
    work = Path(args.work).resolve()
    if work.exists() and any(work.iterdir()):
        raise ValueError('Work directory is not empty; choose a new directory to avoid overwriting revisions.')
    for folder in ('media', 'transcripts', 'boards', 'notes', 'reviews', 'final'):
        (work / folder).mkdir(parents=True, exist_ok=True)
    write_json(work / 'manifest.json', {
        'schema_version': 1, 'course': '原创演示，替换后用于真实课程',
        'scope': {'included': ['demo-001'], 'excluded': [], 'example_policy': 'representative'},
        'lessons': [{'id': 'demo-001', 'title': '换元积分演示', 'bvid': None,
                     'page': 1, 'url': None, 'author': '原创示例',
                     'duration_seconds': None, 'is_demo': True}]
    })
    write_json(work / 'progress.json', {
        'schema_version': 1, 'main_tex': 'final/lecture.tex',
        'lessons': {'demo-001': {'acquired': False, 'transcript_read': False,
                    'boards_reviewed': False, 'notes_written': False,
                    'evidence': [], 'unresolved': []}},
        'reviews': {name: {'status': 'pending', 'evidence': [], 'issues': []}
                    for name in ('coverage', 'mathematics', 'recalculation', 'method', 'layout')},
        'next_action': 'Replace the demo manifest, then acquire and review one real lesson.'
    })
    shutil.copyfile(ROOT / 'templates/lecture.tex', work / 'final/lecture.tex')
    shutil.copyfile(ROOT / 'examples/method.md', work / 'notes/demo.md')
    print(f'Initialized {work}; all review states remain pending.')


def check(args):
    work = Path(args.work).resolve()
    manifest = json.loads((work / 'manifest.json').read_text(encoding='utf-8'))
    progress = json.loads((work / 'progress.json').read_text(encoding='utf-8'))
    lessons = manifest.get('lessons', [])
    if not lessons:
        raise ValueError('Manifest contains no lessons.')
    ids = [row['id'] for row in lessons]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate lesson IDs. Include the page in IDs for multi-page videos.')
    errors = []
    for row in lessons:
        for key in ('title', 'bvid', 'page', 'url', 'author', 'duration_seconds'):
            if key not in row:
                errors.append(f'{row["id"]}: missing {key}')
        if not row.get('is_demo'):
            for key in ('title', 'bvid', 'url', 'author', 'duration_seconds'):
                if not row.get(key):
                    errors.append(f'{row["id"]}: real lesson requires {key}')
        state = progress.get('lessons', {}).get(row['id'])
        if not isinstance(state, dict):
            errors.append(f'{row["id"]}: missing progress entry')
            continue
        for key in ('acquired', 'transcript_read', 'boards_reviewed', 'notes_written'):
            if not isinstance(state.get(key), bool):
                errors.append(f'{row["id"]}: {key} must be boolean')
        if any(state.get(key) is True for key in ('transcript_read', 'boards_reviewed')) and not state.get('evidence'):
            errors.append(f'{row["id"]}: claimed reading needs evidence references')
    scope_ids = manifest.get('scope', {}).get('included', [])
    if set(scope_ids) != set(ids):
        errors.append('scope.included must match manifest lesson IDs')
    main = (work / progress.get('main_tex', '')).resolve()
    if not main.is_relative_to(work) or main.suffix != '.tex' or not main.is_file():
        errors.append('main_tex must identify a saved .tex inside the work directory')
    statuses = {}
    for name in ('coverage', 'mathematics', 'recalculation', 'method', 'layout'):
        review = progress.get('reviews', {}).get(name, {})
        statuses[name] = review.get('status')
        if review.get('status') not in ('pending', 'in_progress', 'passed', 'failed', 'blocked'):
            errors.append(f'{name}: invalid review status')
        if review.get('status') == 'passed' and (not review.get('evidence') or review.get('issues')):
            errors.append(f'{name}: passed requires evidence and no unresolved issues')
    print(json.dumps({'structure_ok': not errors, 'lesson_count': len(ids),
                      'review_status': statuses, 'errors': errors,
                      'note': 'Structural checks do not establish truth, coverage or mathematical correctness.'},
                     ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


def frames(args):
    video = Path(args.video).resolve()
    out = Path(args.out).resolve()
    if not video.is_file():
        raise ValueError('Video file not found.')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Frame directory is not empty; use a new directory to preserve existing evidence.')
    times = sorted(set(args.times))
    if not times or any(t < 0 for t in times):
        raise ValueError('Times must be nonnegative seconds.')
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for i, seconds in enumerate(times, 1):
        target = out / f'frame-{i:04d}.jpg'
        # Input seek + transcoding uses FFmpeg accurate seek by default.
        subprocess.run([args.ffmpeg, '-v', 'error', '-nostdin', '-n', '-ss', str(seconds),
                        '-i', str(video), '-frames:v', '1', '-q:v', '2', str(target)],
                       check=True, timeout=120)
        if not target.is_file() or target.stat().st_size == 0:
            raise ValueError(f'No frame at {seconds}s; check duration and decoding.')
        index.append({'file': target.name, 'requested_seconds': seconds,
                      'reviewed': False, 'note': 'Seek location; allow frame-rate rounding. Verify key claims nearby.'})
        write_json(out / 'index.json', {'video': str(video), 'frames': index})
    print(f'Extracted {len(index)} frames. None is marked reviewed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    p = commands.add_parser('doctor'); p.set_defaults(run=doctor)
    for name, func in (('init', init), ('check', check)):
        p = commands.add_parser(name); p.add_argument('--work', required=True); p.set_defaults(run=func)
    p = commands.add_parser('frames')
    p.add_argument('--video', required=True); p.add_argument('--out', required=True)
    p.add_argument('--times', required=True, nargs='+', type=float)
    p.add_argument('--ffmpeg', default='ffmpeg'); p.set_defaults(run=frames)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
