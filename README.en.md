# Bilibili Course Refinery

[中文](README.md) · English

Start from a screenshot, verify the course, acquire public accessible lecture evidence, explain methods and derivations, perform five real reviews, and deliver editable LaTeX/PDF.

## One Git command to start locally

On **Windows PowerShell with Git and Python installed**:

```powershell
git -c 'alias.refine=!cd "${GIT_PREFIX:-.}" && git clone https://github.com/dingzhongmai-spec/bili-course-refinery.git bili-course-refinery && cd bili-course-refinery && py -3 launch.py' refine
```

On **macOS/Linux with Git and Python 3 installed**:

```sh
git -c 'alias.refine=!cd "${GIT_PREFIX:-.}" && git clone https://github.com/dingzhongmai-spec/bili-course-refinery.git bili-course-refinery && cd bili-course-refinery && python3 launch.py' refine
```

This temporary Git alias clones the project and launches the local app; it does not change global Git settings. Plain `git clone` does not execute project code. Use a directory where `bili-course-refinery` does not yet exist. For an existing checkout run `python launch.py` (or `py -3 launch.py`). No Python packages or virtual environment are needed for the launcher. Press Ctrl+C to stop the server after a running task completes.

## Use the app

1. The browser opens a local page. Choose English if desired.
2. Upload, drag in, or paste a course screenshot. Add scope or learning requirements if needed.
3. Click **Start refining**. The launcher passes the image and project instructions to your installed, signed-in Codex CLI using `codex exec`. It uses your configured model/account and may consume your normal Codex allowance. It does not embed API keys.
4. Follow logs and results on the page. Tasks survive page refresh and are saved under `work/<task-id>/`. Final PDF and TeX links appear when generated.

Codex CLI must be installed and signed in for automatic execution. If it is absent, the local app still works: choose **Prepare desktop task**, copy the prompt and attach the original screenshot in Codex desktop. This fallback is explicitly shown, not presented as an automatic AI run.

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

`launch.py` and `ui/` implement the local application. `scripts/` provides standalone structure checks, frame extraction and optional ASR. `templates/` and `examples/` contain original teaching examples. Chinese detailed workflow, dependencies, retrospectives and validation records are in `docs/`.

Raw screenshots, course media, transcripts, generated notes, credentials and execution logs remain in the ignored `work/` directory. The repository does not distribute third-party course materials or the upstream downloader. Cleanup and public redistribution require the relevant user authorization. A software license has not yet been selected; upstream licenses are separate.
