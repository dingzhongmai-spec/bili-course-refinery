"""Render PDF pages and flag layout clues; rendering does not certify visual review."""
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import activate


def review(pdf, out, dpi=100, log=None):
    import pymupdf as fitz
    pdf, out = Path(pdf).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('Review directory already exists; choose a new revision directory')
    if not 36 <= dpi <= 200:
        raise ValueError('DPI must be between 36 and 200')
    with fitz.open(pdf) as doc:
        if doc.is_encrypted or not len(doc):
            raise ValueError('PDF must be readable and nonempty')
        log_text = Path(log).read_text(encoding='utf-8', errors='replace') if log else None
        report = {'pdf': str(pdf), 'pages': len(doc), 'rendered_pages': [], 'visual_review': 'not_performed',
                  'outside_page_spans': [], 'small_spans_under_6pt': [],
                  'log_file': str(Path(log).resolve()) if log else None,
                  'log_clues': {name: len(re.findall(pattern, log_text)) for name, pattern in {
                      'missing_glyphs': r'Missing character', 'overfull_boxes': r'Overfull',
                      'undefined_references': r'(?:Reference|Citation).*undefined'
                  }.items()} if log_text is not None else None}
        out.mkdir(parents=True)
        for number, page in enumerate(doc, 1):
            name = f'page_{number:04d}.png'
            page.get_pixmap(dpi=dpi, alpha=False).save(out / name)
            report['rendered_pages'].append(name)
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    for span in line.get('spans', []):
                        if not span['text'].strip():
                            continue
                        x0, y0, x1, y1 = span['bbox']
                        item = {'page': number, 'text': span['text'], 'bbox': span['bbox'], 'size': span['size']}
                        if x0 < 0 or y0 < 0 or x1 > page.rect.width or y1 > page.rect.height:
                            report['outside_page_spans'].append(item)
                        if span['size'] < 6:
                            report['small_spans_under_6pt'].append(item)
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return report


def main():
    activate()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--dpi', type=int, default=100)
    parser.add_argument('--log', help='Compiler log from this exact revision, if available')
    args = parser.parse_args()
    data = review(args.pdf, args.out, args.dpi, args.log)
    print(f"Rendered {data['pages']} pages. Inspect actual PNGs; visual review has not been performed.")


if __name__ == '__main__':
    main()
