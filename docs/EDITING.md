# LaTeX辅助编辑与音频裁切 / LaTeX editing and audio clipping

[中文](#中文) · [English](#english)

## 中文

这三个工具复用一键安装准备的依赖：音频裁切使用FFmpeg/FFprobe，PDF渲染使用PyMuPDF，TeX精确编辑只用Python标准库。裁切和PDF工具读取项目`.runtime/config.json`，不要求系统PATH另行配置。支持本地音视频文件，不承担课程下载；GUI编辑器不是必需依赖。

实现参考：[FFmpeg atrim与时间戳重置](https://ffmpeg.org/ffmpeg-filters.html#atrim)、[PyMuPDF页面渲染](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_pixmap)。

### 针对疑点裁切音频

从已核实讲次中截取疑点前后的一小段，默认生成16kHz单声道PCM WAV，避免包复制产生不精确的边界。支持秒数或`HH:MM:SS.sss`；结束时间不得超过输入时长。原文件保留，已有输出不覆盖。

```powershell
python scripts/cut_audio.py --input work/course/media/lesson/audio.m4a --start 00:02:10 --end 00:02:35 --out work/course/clips/lesson-130-155.wav
python scripts/transcribe.py --audio work/course/clips/lesson-130-155.wav --clip-map work/course/clips/lesson-130-155.clip.json --out work/course/transcripts/lesson-130-155.json
```

输出`.clip.json`保存原文件与片段的哈希、原始起止时间、实际片段时长、音频参数、工具版本和时间映射。转写时`start/end`仍表示片段内时间，新增`original_start/original_end`表示原输入时间。根据哈希确认映射属于当前音频，避免误用另一片段的时间轴；移动片段后仍可凭内容哈希关联。

例如从130秒开始的片段中，ASR的3.2秒位置对应原音频133.2秒。二次裁切时映射只指向本次输入，若输入已是片段，须组合之前的偏移并记录；工具不会自动推断多级来源。原课BV/分P仍从manifest关联。裁切成功、ASR结束均不代表已经听过或核对板书。裁切范围不能代替整节读取，也不能凭短片段宣称整课覆盖。

### 按明确改动修订当前TeX

先读取主TeX，得到当前原始字节的SHA-256：

```powershell
python scripts/edit_tex.py --tex work/course/final/lecture.tex
```

由AI或编辑者准备UTF-8 JSON计划，例如`work/course/edits.json`：

```json
{
  "source_sha256": "填入刚取得的64位哈希 / insert the current 64-character hash",
  "edits": [
    {"before": "需要更正的完整原文", "after": "核验后的完整新文", "count": 1}
  ]
}
```

精确匹配包含空白和换行；JSON内TeX反斜杠写成`\\`。默认`count=1`，匹配太多或太少都会终止；多项改动按顺序应用于候选稿。哈希变化时重新读取当前主稿，不恢复旧备份来强行通过。

```powershell
python scripts/edit_tex.py --tex work/course/final/lecture.tex --plan work/course/edits.json
python scripts/edit_tex.py --tex work/course/final/lecture.tex --plan work/course/edits.json --apply
python scripts/compile_pdf.py --tex work/course/final/lecture.tex
```

首条只预览差异；第二条应用已检查改动，保留未修改文本、UTF-8 BOM及已有换行。`--apply`是脚本写入开关，AI可以在用户已授权修订范围内检查差异后调用，无需另设人工批准流程。它不判断数学正确性、不会自动给所有公式编号，也不是TeX语法解析器；编号与长式分行由AI按核实内容编辑，再用实际编译检查。

### 渲染并查看实际PDF

```powershell
python scripts/review_pdf.py --pdf work/course/final/lecture.pdf --log work/course/final/lecture.log --out work/course/review/revision-01
```

没有当前编译日志时省略`--log`。生成每页PNG和`report.json`，记录页外文字、6pt以下文字、日志中的缺字、溢出和未定义引用线索。输出目录必须尚不存在，修订后使用新的检查目录。

自动线索可能漏掉图片、重叠和已经裁掉的内容，也可能产生误报。报告始终将视觉审阅标为`not_performed`；AI必须实际查看页面，再在progress中登记查看范围与发现。旧日志、旧PDF和旧截图不能替代当前主稿的验收。页数多时先看首尾、目录、长式、图像和修订页，再按用户交付要求完成其余检查。需要逐页验收则逐页查看。

### 从回收站提炼的做法

经用户授权只读查看历史`revise_in_place.py`、`review_pdf.py`、`transcribe.py`、`extract_boards.py`与`acquire.py`。吸收主稿哈希保护、编号与分行的编辑约束、PDF逐页渲染、未完成视觉审阅的边界，以及FFmpeg音轨处理方法。未找到独立的历史音频裁切器，本仓库为局部回听新写了裁切与时间映射工具。

历史脚本中的个人路径、固定课程ID、课程正文、旧备份恢复逻辑和GPU硬编码未加入公开工具；没有执行、恢复、删除或清空回收站文件。来源路径与课程素材不进入Git，裁切、转写、编辑计划和检查结果放在忽略的`work/`中。需要回滚时使用已有Git或用户选定的版本管理，不自动覆盖主稿。

## English

The helpers reuse the one-command installation: FFmpeg/FFprobe for clips, PyMuPDF for PDF rendering, and Python's standard library for exact TeX edits. Media/PDF helpers activate `.runtime/config.json`; no additional global PATH setup or GUI editor is required. These tools operate on local files; acquisition remains a separate step.

### Audio clipping and source timing

Use `scripts/cut_audio.py --input INPUT --start 130 --end 155 --out work/course/clips/clip.wav`. Times accept seconds or `HH:MM:SS.sss`. The tool decodes and trims to mono 16 kHz PCM WAV, checks the actual duration, retains the source and refuses existing outputs. Its `.clip.json` records source/clip hashes, source interval, actual duration, parameters, tool version and timing relation.

Run `scripts/transcribe.py --audio work/course/clips/clip.wav --clip-map work/course/clips/clip.clip.json --out work/course/transcripts/clip.json`. Hash verification binds the map to the actual clip. Segment `start/end` remain clip-local; `original_start/original_end` add the source offset. A clip-local 3.2s position from a clip beginning at 130s maps to 133.2s in the input. For nested clips, explicitly compose prior offsets; automatic ancestry is not implemented. Relate BV/page identities through the manifest. Cutting or transcription does not establish listening, board verification or full-lesson coverage.

### TeX revision

Use `scripts/edit_tex.py --tex MAIN.tex` to obtain its raw-byte SHA-256. Prepare a UTF-8 JSON plan with `source_sha256` and an `edits` array containing exact `before`, `after` and optional `count` (default 1), as illustrated above. Escape TeX backslashes in JSON. Matches include whitespace/newlines; edits run sequentially on the candidate text. Ambiguous counts or changed source hashes abort without changing the main file.

Use `scripts/edit_tex.py --tex MAIN.tex --plan PLAN.json` to preview the diff, then add `--apply` to write the checked edits. Existing user authorization permits the AI to inspect and apply ordinary revisions without an additional approval gate. The helper retains untouched content, UTF-8 BOM and existing line endings. It is not a mathematical verifier or TeX parser and does not automatically number displays. Edit numbering and equation breaks based on verified content, then compile the actual main file with `scripts/compile_pdf.py --tex MAIN.tex`.

### PDF inspection

Use `scripts/review_pdf.py --pdf MAIN.pdf --out work/course/review/revision-01`, optionally with `--log CURRENT.log`. A new output directory is required. It renders every page and records page-boundary/small-text clues and optional compiler-log clues in `report.json`. Such checks can miss image issues, overlap and clipped content, or produce false positives. `visual_review` remains `not_performed`: inspect actual pages and record the real inspection scope in progress. Do not inherit approval from old PDFs, logs or images; honor any requirement for page-by-page review.

### Historical basis

With user authorization, historical recycling-bin scripts were read for hash-protected main-source editing, formula layout constraints, page rendering, ASR evidence limits and FFmpeg audio handling. No standalone historic clipping tool was found; precise clipping and source-time mapping are new implementations. Private paths, fixed course IDs, lecture content, old-backup regeneration and GPU-specific settings are excluded. Recycled files were not executed, restored or deleted. Local clips, transcripts, edit plans and review artifacts belong in ignored `work/`.
