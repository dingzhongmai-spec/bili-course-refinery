"""Preview or apply exact, hash-guarded edits to the current UTF-8 TeX source."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import tempfile


def prepare(tex, plan):
    original = Path(tex).read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if plan.get('source_sha256') != digest:
        raise ValueError('Source hash changed; re-read the current main TeX and revise the plan')
    bom = original.startswith(b'\xef\xbb\xbf')
    text = original.decode('utf-8-sig')
    edits = plan.get('edits')
    if not isinstance(edits, list) or not edits:
        raise ValueError('Plan must include a nonempty edits list')
    updated = text
    for edit in edits:
        before, after, count = edit['before'], edit['after'], edit.get('count', 1)
        if not isinstance(before, str) or not before or not isinstance(after, str):
            raise ValueError('Each edit needs a nonempty before string and an after string')
        if type(count) is not int or count < 1 or updated.count(before) != count:
            raise ValueError('Exact match count differs; resolve ambiguous or stale edits')
        updated = updated.replace(before, after)
    if updated == text:
        raise ValueError('Plan makes no change')
    result = (b'\xef\xbb\xbf' if bom else b'') + updated.encode('utf-8')
    return original, result, text, updated


def apply(tex, original, result):
    tex = Path(tex).resolve()
    with tempfile.NamedTemporaryFile(prefix='.tex-edit-', suffix='.tmp', dir=tex.parent, delete=False) as stream:
        temp = Path(stream.name)
        stream.write(result)
    try:
        if tex.read_bytes() != original:
            raise ValueError('Source changed after preview; edit cancelled')
        os.replace(temp, tex)
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tex', required=True)
    parser.add_argument('--plan', help='JSON with source_sha256 and edits: before/after/count')
    parser.add_argument('--apply', action='store_true', help='Apply the reviewed plan; default prints a diff only')
    args = parser.parse_args()
    tex = Path(args.tex).resolve()
    if tex.suffix.lower() != '.tex' or not tex.is_file():
        parser.error('Provide an existing .tex file')
    if not args.plan:
        if args.apply:
            parser.error('--apply requires --plan')
        print(hashlib.sha256(tex.read_bytes()).hexdigest())
        return
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8-sig'))
    original, result, text, updated = prepare(tex, plan)
    print(''.join(difflib.unified_diff(text.splitlines(True), updated.splitlines(True),
                                   fromfile=tex.name, tofile=tex.name)), end='')
    if args.apply:
        apply(tex, original, result)
        print('\nApplied to the current main TeX. Recompile and inspect the PDF.')


if __name__ == '__main__':
    main()
