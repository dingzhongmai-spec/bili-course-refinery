# Bilibili Course Refinery

[中文](README.md) · English

Start from a screenshot, verify the course, acquire public accessible lecture evidence, explain methods and derivations, perform five real reviews, and deliver editable LaTeX/PDF.

## One Git command to install, configure and launch

On **Windows 10/11 x64 with Git installed and Internet access**:

```powershell
git -c 'alias.refine=!cd "${GIT_PREFIX:-.}" && git clone https://github.com/dingzhongmai-spec/bili-course-refinery.git bili-course-refinery && cd bili-course-refinery && powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1' refine
```

Setup reuses Python or installs a signed python.org distribution if absent. It prepares project-local Python packages, a pinned acquisition tool, a small local ASR model, FFmpeg/FFprobe, and a portable Tectonic PDF compiler when XeLaTeX is absent. Codex CLI (and Node when needed) is installed locally if missing. Runtime files stay under `.runtime/`; there is no Python virtualenv or global PATH change.

It validates media tools, ASR model loading, downloader imports and a real Chinese PDF before marking setup ready. Downloads are checksum-verified. First installation downloads several hundred MB or more; network failures are reported and logged rather than labelled success. Repeat `install.ps1` to retry with cached files. Use `-NoLaunch` to install and validate only.

Codex sign-in must be completed by the account owner; existing sign-in is reused. Installation cannot bypass source-site restrictions or certify course review. Details: [installation guide](docs/INSTALL.md).

**macOS/Linux currently use manually prepared dependencies**:

```sh
git -c 'alias.refine=!cd "${GIT_PREFIX:-.}" && git clone https://github.com/dingzhongmai-spec/bili-course-refinery.git bili-course-refinery && cd bili-course-refinery && python3 launch.py' refine
```

This temporary Git alias clones, installs and launches the project without changing global Git settings. Plain `git clone` does not execute project code. Use a directory where `bili-course-refinery` does not yet exist. Existing Windows checkouts: `git pull --ff-only`, then `powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1`. For the minimal UI only run `python launch.py` (or `py -3 launch.py`). Press Ctrl+C to stop after a running task completes.

## Use the app

1. The browser opens a local page. Choose English if desired.
2. Upload, drag in, or paste a course screenshot. Add scope or learning requirements if needed.
3. Click **Start refining**. The launcher passes the image and project instructions to your installed, signed-in Codex CLI using `codex exec`. It uses your configured model/account and may consume your normal Codex allowance. It does not embed API keys.
4. Follow logs and results on the page. Tasks survive page refresh and are saved under `work/<task-id>/`. Final PDF and TeX links appear when generated.

Automatic execution needs Codex sign-in. The full Windows installer prepares the CLI when missing; the minimal UI can also generate a desktop task, where you copy the prompt and attach the original screenshot in Codex desktop.

The launcher uses workspace-write sandboxing, network access and automatic approval review; it does not disable safeguards. Environment restrictions can still block a tool or require user action. Keep the local service running while the task executes. Screenshot-to-PDF completion depends on source availability, installed acquisition/ASR/LaTeX tools and successful content review.

## Tools and skill

- Acquisition: [NANblogink/bilibilidownloadtool](https://github.com/NANblogink/bilibilidownloadtool), the public-source tool used in the original workflow, subject to its upstream terms.
- Media/frame processing: [FFmpeg](https://www.ffmpeg.org/).
- Local ASR when needed: [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
- Mathematics: optional local Wolfram or another verification tool.
- Publishing: XeLaTeX/ctex and a PDF viewer.

The bilingual, project-discoverable skill is [.agents/skills/bili-course-refinery/SKILL.md](.agents/skills/bili-course-refinery/SKILL.md). It includes self-contained English and Chinese references. No global skill installation is required. To reuse it in other projects, copy the complete skill folder into their `.agents/skills/` directory.

Core rule: **evidence constrains facts; mathematics constrains conclusions; the user defines the goal. AI may improve explanations, organization and implementation. Prefer simple reliable methods and substantiate completion claims.**

Five reviews: coverage, mathematical validity, recalculation, method choice and presentation. Transcripts and sampled frames are evidence, not guaranteed truth. CAS only validates actually executed checks. Number displayed equations and inspect the compiled PDF.

## Repository contents

`install.ps1`/`install.py` prepare and validate the environment; `runtime.py` shares project-local paths. `launch.py` and `ui/` implement the local application. `scripts/` includes real per-lesson acquisition, frame extraction, ASR and PDF compilation adapters. `templates/` and `examples/` contain original teaching examples. Detailed workflow and validation records are in `docs/`.

Raw screenshots and course materials remain in ignored `work/`; installed tools and local configuration stay in ignored `.runtime/`. Original source, documentation and skill are [MIT licensed](LICENSE). Third-party tools, models and course materials retain their own licenses. Cleanup and public redistribution require the relevant authorization.
