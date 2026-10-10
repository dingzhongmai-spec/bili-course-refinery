import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from install import download, unpack
from runtime import activate


class InstallationTests(unittest.TestCase):
    def test_zip_cannot_escape_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'evil.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('../outside.txt', 'unsafe')
            with self.assertRaises(ValueError):
                unpack(archive, root / 'tools')
            self.assertFalse((root / 'outside.txt').exists())

    def test_checksum_mismatch_is_never_promoted(self):
        import io
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / 'binary.zip'
            with patch('install.RUNTIME', root), patch('install.urllib.request.urlopen', side_effect=lambda *a, **k: io.BytesIO(b'wrong')), patch('install.time.sleep'):
                with self.assertRaises(ValueError):
                    download('https://example.invalid/file.zip', target, 'sha256:' + hashlib.sha256(b'expected').hexdigest())
            self.assertFalse(target.exists())

    def test_missing_configuration_does_not_claim_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(activate(Path(tmp)), {})


if __name__ == '__main__':
    unittest.main()
