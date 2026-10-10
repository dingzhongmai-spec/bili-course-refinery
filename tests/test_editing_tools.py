import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

from runtime import activate
from scripts.cut_audio import cut, timestamp
from scripts.edit_tex import apply, prepare
from scripts.review_pdf import review
from scripts import transcribe


class TeXEditingTests(unittest.TestCase):
    def test_changed_source_and_ambiguous_match_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / '讲义.tex'
            raw = b'old old\r\n'
            tex.write_bytes(raw)
            plan = {'source_sha256': 'outdated', 'edits': [{'before': 'old', 'after': 'new'}]}
            with self.assertRaises(ValueError):
                prepare(tex, plan)
            plan['source_sha256'] = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ValueError):
                prepare(tex, plan)
            self.assertEqual(tex.read_bytes(), raw)

    def test_apply_preserves_bom_and_detects_intervening_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / '讲义.tex'
            raw = b'\xef\xbb\xbf' + '旧内容\r\n'.encode('utf-8')
            tex.write_bytes(raw)
            plan = {'source_sha256': hashlib.sha256(raw).hexdigest(),
                    'edits': [{'before': '旧内容', 'after': '新内容'}]}
            original, result, _, _ = prepare(tex, plan)
            self.assertEqual(tex.read_bytes(), raw)  # Preparation/preview is read-only.
            apply(tex, original, result)
            self.assertEqual(tex.read_bytes(), b'\xef\xbb\xbf' + '新内容\r\n'.encode('utf-8'))
            tex.write_bytes(b'changed by editor')
            with self.assertRaises(ValueError):
                apply(tex, original, result)
            self.assertEqual(tex.read_bytes(), b'changed by editor')


class AudioCuttingTests(unittest.TestCase):
    def test_timestamp_validation(self):
        self.assertEqual(timestamp('00:01:02.5'), 62.5)
        for value in ('NaN', 'inf', '-1', '00:60:00', '1:2', '0.5:00:00'):
            with self.assertRaises(argparse.ArgumentTypeError):
                timestamp(value)

    def test_real_cut_preserves_samples_offset_and_prior_evidence(self):
        config = activate()
        tools = config.get('tools', {})
        if not tools.get('ffmpeg') or not tools.get('ffprobe'):
            self.skipTest('Integration test requires installed media tools')
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / '原音.wav'
            out = Path(tmp) / '片段.wav'
            samples = b''.join(struct.pack('<h', (i % 2000) - 1000) for i in range(48000))
            with wave.open(str(source), 'wb') as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(16000)
                stream.writeframes(samples)
            mapping = cut(source, out, 0.5, 1.75, tools)
            with wave.open(str(out), 'rb') as stream:
                self.assertEqual(stream.getnframes(), 20000)
                self.assertEqual(stream.readframes(20000), samples[16000:56000])
            self.assertEqual(mapping['source_start_seconds'], 0.5)
            self.assertEqual(json.loads(out.with_suffix('.clip.json').read_text(encoding='utf-8'))['read_status'], 'unread')
            before = out.read_bytes()
            with self.assertRaises(ValueError):
                cut(source, out, 0, 1, tools)
            self.assertEqual(out.read_bytes(), before)
            bad = Path(tmp) / '超界.wav'
            with self.assertRaises(ValueError):
                cut(source, bad, 2, 4, tools)
            self.assertFalse(bad.exists())


class PDFReviewTests(unittest.TestCase):
    def test_render_flags_clues_without_claiming_visual_approval(self):
        activate()
        try:
            import pymupdf as fitz
        except ImportError:
            self.skipTest('Integration test requires installed PyMuPDF')
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / 'sample.pdf'
            out = Path(tmp) / 'review'
            with fitz.open() as doc:
                page = doc.new_page()
                page.insert_text((40, 40), 'small text', fontsize=5)
                doc.new_page()
                doc.save(pdf)
            data = review(pdf, out, dpi=50)
            self.assertEqual(data['pages'], 2)
            self.assertEqual(len(list(out.glob('page_*.png'))), 2)
            self.assertEqual(len(data['small_spans_under_6pt']), 1)
            self.assertEqual(data['visual_review'], 'not_performed')
            self.assertIsNone(data['log_clues'])
            with self.assertRaises(ValueError):
                review(pdf, out)


class ClipTranscriptionTests(unittest.TestCase):
    def test_original_times_are_retained_and_wrong_map_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / 'clip.wav'
            audio.write_bytes(b'test audio content')
            mapping = Path(tmp) / 'clip.clip.json'
            data = {'source_start_seconds': 130, 'clip_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(),
                    'source_file': 'original.m4a', 'source_sha256': 'recorded-original-hash'}
            mapping.write_text(json.dumps(data), encoding='utf-8')
            out = Path(tmp) / 'transcript.json'
            segment = SimpleNamespace(start=3.2, end=4.5, text='核对公式', avg_logprob=-0.2, no_speech_prob=0.01)
            model = SimpleNamespace(transcribe=lambda *a, **k: (iter([segment]), SimpleNamespace(duration=25)))
            package = SimpleNamespace(WhisperModel=lambda *a, **k: model)
            argv = ['transcribe.py', '--audio', str(audio), '--out', str(out), '--clip-map', str(mapping)]
            with patch.object(sys, 'argv', argv), patch.dict(sys.modules, {'faster_whisper': package}):
                transcribe.main()
            result = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(result['segments'][0]['start'], 3.2)
            self.assertEqual(result['segments'][0]['original_start'], 133.2)
            self.assertEqual(result['segments'][0]['original_end'], 134.5)
            self.assertEqual(result['read_status'], 'unread')
            data['clip_sha256'] = 'wrong-clip'
            mapping.write_text(json.dumps(data), encoding='utf-8')
            argv[argv.index('--out') + 1] = str(Path(tmp) / 'wrong.json')
            with patch.object(sys, 'argv', argv), self.assertRaises(ValueError):
                transcribe.main()


if __name__ == '__main__':
    unittest.main()
