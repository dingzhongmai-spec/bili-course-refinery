"""Optional local ASR; formulas still require visual and mathematical review."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--model', default='small', help='Model name (may download) or local CT2 directory')
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    parser.add_argument('--compute-type', default=None)
    args = parser.parse_args()
    audio, out = Path(args.audio).resolve(), Path(args.out).resolve()
    if not audio.is_file():
        raise ValueError('Audio input not found.')
    if out.exists():
        raise ValueError('Output already exists; choose another path to preserve prior evidence.')
    from faster_whisper import WhisperModel
    compute = args.compute_type or ('int8' if args.device == 'cpu' else 'int8_float16')
    model = WhisperModel(args.model, device=args.device, compute_type=compute)
    segments, info = model.transcribe(str(audio), language='zh', beam_size=5, vad_filter=True)
    # Exhausting this generator performs inference; obtaining it alone is not completion.
    data = [{'start': s.start, 'end': s.end, 'text': s.text,
             'avg_logprob': s.avg_logprob, 'no_speech_prob': s.no_speech_prob} for s in segments]
    if not data:
        raise ValueError('No speech segments produced. Review the input before proceeding.')
    payload = {'source_audio': str(audio), 'source_type': 'local_asr', 'model': args.model,
               'device': args.device, 'compute_type': compute,
               'duration_seconds': info.duration, 'segments': data, 'read_status': 'unread',
               'warning': '自动转写：公式、数字、量词和时间定位必须另行核对'}
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
