# Third-party tools / 第三方工具

The MIT license in this repository covers its original code, instructions and templates. It does not relicense dependencies or course content. Tools are fetched into the ignored `.runtime/` directory and are not included in source ZIPs.

本仓库MIT许可仅覆盖原创代码、指令和模板，不改变依赖或课程内容的许可。第三方工具由安装器取得并留在本地`.runtime/`，不包含在源码压缩包中。

|Dependency / 依赖|Source / 来源|Local record / 本地记录|
|---|---|---|
|Bilibili acquisition tool|https://github.com/NANblogink/bilibilidownloadtool |Pinned commit and original upstream README; follow its use/distribution conditions|
|FFmpeg Windows build|https://github.com/GyanD/codexffmpeg ; https://www.gyan.dev/ffmpeg/builds/ |GPL build with upstream license files, verified SHA-256|
|Tectonic|https://github.com/tectonic-typesetting/tectonic |Upstream release and license files, verified SHA-256|
|Python|https://www.python.org/ |Python.org installer signature, Python's own license|
|Node.js|https://nodejs.org/ |Official archive checksum, upstream license files|
|Codex CLI|https://github.com/openai/codex |npm @openai/codex, upstream package/version|
|faster-whisper|https://github.com/SYSTRAN/faster-whisper |Installed package version|
|ASR model|https://huggingface.co/Systran/faster-whisper-small |Model repository revision|
|Other Python packages|https://pypi.org/ |`.runtime/package-versions.json` and package metadata|

If a dependency's terms do not permit the intended acquisition or redistribution scope, adapt the tool choice or scope. Merely publishing this workflow does not grant rights to redistribute lecture videos, screenshots or transcripts.

依赖使用条件与目标采集/发布范围不兼容时，应调整工具或范围；公开工作流不代表允许再分发课程视频、板书和完整转写。
