# 安装与配置 / Installation

完整自动安装目标：Windows 10/11 x64，Git和可用网络。无需预装Python、Node、FFmpeg或LaTeX。其他系统保留手动依赖路线，不能把它们称为自动安装已支持。

Full automatic setup targets Windows 10/11 x64 with Git and Internet. Python, Node, FFmpeg and LaTeX need not be preinstalled. Other operating systems currently require manually prepared dependencies.

## 实际准备项 / Prepared components

|项目 / Component|行为 / Behavior|
|---|---|
|Python|复用Windows Python；缺少时安装python.org签名版本，项目路径，无系统PATH更改 / Reuse Python, otherwise install a signed python.org build locally|
|Python依赖 / Packages|pip官方PyPI安装到`.runtime/packages`，不建venv / Official PyPI, local target, no venv|
|采集器 / Downloader|Git固定提交`ad6a40f75a66082dd7884fec3cf01decf927021f`，稀疏取得所需源码 / Pinned sparse checkout|
|媒体 / Media|优先已有FFmpeg/FFprobe，缺少时下载Gyan发布的便携版本，SHA-256校验 / Reuse or verified portable build|
|ASR|faster-whisper CPU/int8，下载Systran small模型并记录revision / Local small model with recorded revision|
|PDF|已有XeLaTeX优先；否则安装Tectonic并自动取得需要的TeX资源 / XeLaTeX or portable Tectonic|
|Codex|已有CLI优先，缺少时npm项目内安装；必要时准备Node / Reuse CLI or local npm installation|

`.runtime/config.json`登记实际路径、解释器、工具下载摘要、模型revision、项目提交（ZIP则标未知）、安装状态和自检结果。`.runtime/package-versions.json`记录解析后的包版本。`.runtime/install.log`记录安装失败原因，不保存登录凭据。

发布源码包的`BUILD_INFO.txt`由Git archive写入提交ID，`VERSION`记录版本；没有`.git`时安装器尝试读取该信息，普通副本无法取得提交时保持未知。TeX资源使用编译器缓存，首次编译可能需要较多网络请求。

## 安装重试 / Retry

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
```

不启动页面 / Install without launching:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -NoLaunch
```

强制使用下载工具验证缺少系统工具的路径 / Exercise portable tools:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -NoLaunch -PortableTools
```

`-Refresh`重新解析和安装Python包。可重复运行，保留已验证工具与模型缓存；失败不会宣布ready。ExecutionPolicy Bypass只作用于此进程，不修改系统策略。

## 可运行适配器 / Executable adapters

使用config.json里登记的Python（以下`py -3`仅为已有Windows Python示例）。

```powershell
py -3 scripts/acquire.py --bvid BV1LvovBvERW --page 1 --work work/course --probe-only
py -3 scripts/acquire.py --bvid BV1LvovBvERW --page 1 --work work/course
py -3 scripts/transcribe.py --audio work/course/media/BV1LvovBvERW-p01/audio.m4a --out work/course/transcripts/lesson-001.json
py -3 scripts/compile_pdf.py --tex work/course/final/lecture.tex
```

第一条仅检查元信息。采集入口检查公开流、分P及媒体时长，不处理DRM或付费限制。语音模型默认采用安装好的本地small；复杂数学口述仍需板书核验。编译入口根据配置选择引擎，不能假装Tectonic就是xelatex。

The first acquisition command checks metadata only. Acquisition validates the page and media duration; protected/restricted material is outside scope. ASR defaults to the installed local small model. PDF compilation selects the configured engine explicitly.

## 仍需本人完成 / User actions

Codex首次登录、源站要求的登录/验证码、网络代理的个人配置，不能由安装脚本代填或绕过。若登录或下载服务不可用，报告实际原因。安装成功仅证明指定自检，不证明任意课程都能取得或五轮内容审阅已经完成。

First Codex sign-in, source-site authentication/CAPTCHA and personal proxy settings require the owner. Setup validation does not guarantee access to every course or completion of content review.
