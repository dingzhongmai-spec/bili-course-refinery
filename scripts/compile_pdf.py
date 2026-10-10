"""Compile with the installed XeLaTeX or portable Tectonic engine."""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import activate


def main():
    config = activate()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tex', required=True)
    args = p.parse_args()
    tex = Path(args.tex).resolve()
    if not tex.is_file():
        raise FileNotFoundError(tex)
    engine = config.get('tex_engine', 'xelatex')
    tool = config.get('tools', {}).get('tex', engine)
    if engine == 'tectonic':
        subprocess.run([tool, '--keep-logs', '--outdir', str(tex.parent), str(tex)], check=True)
    else:
        for _ in range(2):
            subprocess.run([tool, '-interaction=nonstopmode', '-halt-on-error', '-output-directory', str(tex.parent), str(tex)], check=True)
    if not tex.with_suffix('.pdf').is_file():
        raise RuntimeError('Compiler did not generate the expected PDF')


if __name__ == '__main__':
    main()
