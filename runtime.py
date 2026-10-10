"""Project-local dependency paths shared by installer, launcher and helpers."""
import json
import os
from pathlib import Path
import sys
import site

ROOT = Path(__file__).resolve().parent


def activate(root=ROOT):
    config_path = root / '.runtime/config.json'
    if not config_path.is_file():
        return {}
    config = json.loads(config_path.read_text(encoding='utf-8'))
    packages = root / '.runtime/packages'
    if packages.is_dir():
        site.addsitedir(str(packages))
        sys.path.insert(0, str(packages))
        os.environ['PYTHONPATH'] = str(packages) + os.pathsep + os.environ.get('PYTHONPATH', '')
    paths = config.get('bin_dirs', [])
    os.environ['PATH'] = os.pathsep.join(paths + [os.environ.get('PATH', '')])
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['HF_HOME'] = str(root / '.runtime/cache/huggingface')
    return config
