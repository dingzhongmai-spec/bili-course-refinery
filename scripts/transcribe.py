"""Optional local ASR; formulas still require visual and mathematical review."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import activate
CONFIG = activate()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--model', default=CONFIG.get('asr_model', 'small'), help='Configured local CT2 model or model name')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--compute-type', default=None)
    parser.add_argument('--clip-map', help='Timing map produced by cut_audio.py; adds original-source times')
    args = parser.parse_args()
    audio, out = Path(args.audio).resolve(), Path(args.out).resolve()
    if not audio.is_file():
        raise ValueError('Audio input not found.')
    if out.exists():
        raise ValueError('Output already exists; choose another path to preserve prior evidence.')
    timing = None
    if args.clip_map:
        from scripts.cut_audio import sha256
        timing = json.loads(Path(args.clip_map).read_text(encoding='utf-8'))
        offset = timing['source_start_seconds']
        import math
        if not isinstance(offset, (int, float)) or not math.isfinite(offset) or offset < 0:
            raise ValueError('Invalid source timing offset')
        if timing['clip_sha256'] != sha256(audio):
            raise ValueError('Timing map does not match this audio clip')
    from faster_whisper import WhisperModel
    compute = args.compute_type or ('int8' if args.device == 'cpu' else 'int8_float16')
    model = WhisperModel(args.model, device=args.device, compute_type=compute)
    segments, info = model.transcribe(str(audio), language='zh', beam_size=5, vad_filter=True)
    # Exhausting this generator performs inference; obtaining it alone is not completion.
    data = [{'start': s.start, 'end': s.end, 'text': s.text,
             'avg_logprob': s.avg_logprob, 'no_speech_prob': s.no_speech_prob} for s in segments]
    if not data:
        raise ValueError('No speech segments produced. Review the input before proceeding.')
    if timing:
        for segment in data:
            segment['original_start'] = segment['start'] + offset
            segment['original_end'] = segment['end'] + offset
    payload = {'source_audio': str(audio), 'source_type': 'local_asr', 'model': args.model,
               'device': args.device, 'compute_type': compute,
               'duration_seconds': info.duration, 'segments': data, 'read_status': 'unread',
               'warning': '自动转写：公式、数字、量词和时间定位必须另行核对'}
    if timing:
        payload['original_source'] = timing['source_file']
        payload['original_source_sha256'] = timing['source_sha256']
        payload['source_time_offset_seconds'] = offset
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_suffix(out.suffix + '.tmp')
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(out)
    print(f'Saved {len(data)} segments to {out}; evidence remains unread.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'ASR_ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
