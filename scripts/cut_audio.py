"""Cut a verified time interval to mono 16 kHz WAV and retain source timing."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import activate


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def timestamp(value):
    parts = value.split(':')
    if len(parts) not in (1, 3):
        raise argparse.ArgumentTypeError('Use seconds or HH:MM:SS.sss')
    try:
        values = [float(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Invalid timestamp') from exc
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise argparse.ArgumentTypeError('Timestamp must be finite and nonnegative')
    if len(values) == 3:
        if values[0] != int(values[0]) or values[1] != int(values[1]) or values[1] >= 60 or values[2] >= 60:
            raise argparse.ArgumentTypeError('Invalid hours, minutes or seconds')
        return values[0] * 3600 + values[1] * 60 + values[2]
    return values[0]


def probe(path, tool):
    result = subprocess.run([tool, '-v', 'error', '-show_format', '-show_streams',
                             '-of', 'json', str(path)], check=True, capture_output=True, timeout=60)
    return json.loads(result.stdout)


def cut(source, out, start, end, tools):
    source, out = Path(source).resolve(), Path(out).resolve()
    mapping = out.with_suffix('.clip.json')
    if not source.is_file() or out.suffix.lower() != '.wav':
        raise ValueError('Provide an existing input and a .wav output')
    if out.exists() or mapping.exists():
        raise ValueError('Output or timing map already exists; choose a new path')
    if not all(math.isfinite(v) for v in (start, end)) or not 0 <= start < end:
        raise ValueError('Require 0 <= start < end with finite values')
    info = probe(source, tools.get('ffprobe', 'ffprobe'))
    if not any(s['codec_type'] == 'audio' for s in info['streams']):
        raise ValueError('Input has no audio stream')
    duration = float(info['format']['duration'])
    if not math.isfinite(duration) or end > duration:
        raise ValueError(f'Interval exceeds source duration ({duration:.3f}s)')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.audio-cut-', dir=out.parent) as tmp:
        wav = Path(tmp) / 'clip.wav'
        # Decode before trimming: packet-copy seeking is unsuitable for exact ASR clips.
        command = [tools.get('ffmpeg', 'ffmpeg'), '-v', 'error', '-nostdin', '-i', str(source),
                   '-map', '0:a:0', '-af', f'atrim=start={start:.9f}:end={end:.9f},asetpts=PTS-STARTPTS',
                   '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav)]
        subprocess.run(command, check=True, timeout=3600)
        actual = probe(wav, tools.get('ffprobe', 'ffprobe'))
        actual_duration = float(actual['format']['duration'])
        if abs(actual_duration - (end - start)) > 0.05 or actual_duration <= 0:
            raise ValueError('Decoded audio coverage does not match the requested interval')
        version = subprocess.run([command[0], '-version'], check=True, capture_output=True).stdout.decode('utf-8', errors='replace').splitlines()[0]
        payload = {'schema_version': 1, 'source_file': str(source), 'source_sha256': sha256(source),
                   'clip_file': str(out), 'clip_sha256': sha256(wav), 'source_start_seconds': start,
                   'source_end_seconds': end, 'source_duration_seconds': duration,
                   'clip_duration_seconds': actual_duration, 'sample_rate': 16000, 'channels': 1,
                   'ffmpeg_version': version, 'time_mapping': 'original_time = clip_time + source_start_seconds',
                   'read_status': 'unread'}
        meta = Path(tmp) / 'clip.json'
        meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Same-filesystem links publish completed files without overwriting existing evidence.
        os.link(wav, out)
        try:
            os.link(meta, mapping)
        except Exception:
            out.unlink()
            raise
    return payload


def main():
    config = activate()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--start', required=True, type=timestamp)
    parser.add_argument('--end', required=True, type=timestamp)
    args = parser.parse_args()
    data = cut(args.input, args.out, args.start, args.end, config.get('tools', {}))
    print(f"Saved {data['clip_duration_seconds']:.3f}s; source offset {args.start:.3f}s. Evidence remains unread.")


if __name__ == '__main__':
    main()
