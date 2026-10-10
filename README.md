# B站公开视频课程炼化工作流

[中文](README.md) · [English](README.en.md)

## 一条Git命令安装、配置并启动

**Windows 10/11 x64，已安装Git，可联网：**

```powershell
git -c 'alias.refine=!cd "${GIT_PREFIX:-.}" && git clone https://github.com/dingzhongmai-spec/bili-course-refinery.git bili-course-refinery && cd bili-course-refinery && powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1' refine
```

安装器将复用已有Python；缺少时从python.org取得并验证签名后安装。采集器源码、Python包、small ASR模型、缺少的FFmpeg/FFprobe和Tectonic PDF编译器保存于项目`.runtime/`；Codex CLI缺少时安装项目内副本（需要时准备Node）。已有XeLaTeX可直接复用，缺少它也能通过Tectonic输出中文PDF。

安装后执行媒体工具、模型加载、采集器导入和中文PDF实际检查。只有全部检查通过才记录“ready”；失败保留日志，不把“网页可打开”当作环境齐备。首次需下载数百MB以上，时间取决于网络。下载的便携工具校验SHA-256；不修改系统PATH，不使用Python虚拟环境。

Codex首次登录会打开本人认证流程；已有登录直接复用。安装配置能自动完成，账号认证、验证码、源站访问限制不能由脚本代替。软件与源站可用性仍影响实际课程任务，安装自检不代表课程内容已经通过五轮审阅。

**macOS/Linux目前保留手动依赖模式（已安装Python 3与相应工具）：**

```sh
git -c 'alias.refine=!cd "${GIT_PREFIX:-.}" && git clone https://github.com/dingzhongmai-spec/bili-course-refinery.git bili-course-refinery && cd bili-course-refinery && python3 launch.py' refine
```

执行后自动打开本地截图上传页面，支持文件选择、拖入和粘贴。上传截图，填写可选要求，点击“开始整理”，启动器会将截图和项目约束传给本机已登录的Codex CLI，后台执行并显示日志、结果和生成后的PDF/TeX链接。

这是临时Git别名实现的“克隆＋安装＋启动”，不会修改全局Git设置；普通`git clone`本身不会运行仓库程序。目标目录需尚不存在。已有Git仓库先`git pull --ff-only`，再运行`powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1`；可重复执行，复用已经下载的工具。仅安装和验证而不启动：加`-NoLaunch`。安装日志和完整配置见`.runtime/install.log`、`.runtime/config.json`。

仅启动页面仍只依赖Python标准库：`py -3 launch.py`。完整安装会准备上方运行依赖。自动AI执行使用现有Codex模型和账号额度；桌面版任务生成仍可独立使用，页面会显示当前安装与工具状态。

后台执行使用workspace-write沙箱、网络访问和自动审批审查，保留工具限制。现有CLI版本需支持这些选项，不支持时显示日志。任务运行时保持启动终端开启，完成后可用Ctrl+C停止。

中英文skill位于 [.agents/skills/bili-course-refinery/SKILL.md](.agents/skills/bili-course-refinery/SKILL.md)，项目内可发现，无需更改全局设置；可复制整个skill文件夹到其他项目的`.agents/skills/`复用。

Skill新增[讲义教学设计](.agents/skills/bili-course-refinery/references/handout.zh.md)：材料可读性与原图处理、知识结构和学习行动覆盖、例题/练习功能、篇幅预算及可选多版本验收。选择性参考`potergh/build-tutoring-handout`，已保留[固定来源与MIT声明](.agents/skills/bili-course-refinery/references/upstream-notice.md)，按本项目的截图起点、LaTeX/PDF和已有授权适配。

## 工作流

从用户上传的一张截图开始，把课程转成能独立学习、回查和复算的讲义：**上传截图 → 识别线索并定位课程 → 建立范围清单 → 工具采集 → 口述与板书核对 → 方法解释 → 例题推导 → 五轮审阅 → LaTeX/PDF → 验收与清理**。

核心原则：**事实和数学受证据约束；解释、组织与实现允许 AI 发挥；简单优先于直接；所有完成声明必须对应实际检查。**

本仓库依据一次数学竞赛课程整理任务的完整可读取用户对话、执行记录、最终 TeX，以及经用户授权读取的回收站脚本整理。适用于数学、物理、工程等有板书和推导的公开课程。其他学科可替换内容核验规则。

## 你会得到什么

- [完整流程与验收规则](docs/WORKFLOW.md)
- [工具依赖和故障处理](docs/DEPENDENCIES.md)
- [历史复盘：规则为什么产生](docs/RETROSPECTIVE.md)
- [Codex 适配与分阶段提示词](docs/CODEX.md)
- [LaTeX辅助编辑、音频裁切与PDF检查](docs/EDITING.md)：带主稿哈希的精确编辑、保留原课时间映射的裁切、逐页渲染排查。
- [项目约束指令](AGENTS.md)
- [最小方法与例题范例](examples/method.md)、[带编号公式的独立 TeX](templates/lecture.tex)
- `scripts/workflow.py`：环境检查、初始化工作目录、结构检查、明确时间点抽帧。
- `scripts/transcribe.py`：可选的本地中文 ASR。

这是**有人核对证据的工作流**。脚本不会自动看懂板书、完成证明或宣布审阅通过，也不内置下载器、课程材料、API 密钥或登录信息。历史脚本含个人路径和课程硬编码，本仓库重新提供便携的最小工具，未将原脚本原样当作产品发布。

`scripts/acquire.py`已提供可执行的公开讲次采集适配器，按BV与分P调用固定提交的上游解析器，检查音视频时长；`scripts/compile_pdf.py`按安装配置选择XeLaTeX或Tectonic。它们由Codex使用，并保留可单独运行的入口，详见 [安装说明](docs/INSTALL.md)。

## 从一张截图开始

在 Codex 对话中上传一张B站课程页、作者主页、合集目录或相关工具仓库的截图，并说明“整理截图中这套公开视频课程”。AI读取截图中可见的作者、标题、合集名、BV号或仓库名，再检索实际页面，核实作者与目标系列，建立来源清单。用户无需先填写BV列表或准备字幕。

截图中存在多个候选课程时，先列出候选和区别，只询问不能从上下文确定的范围。截图只能作为定位线索，讲解仍需后续取得并核对。工具仓库截图只能确认工具，课程目标从此前课程截图或对话确定；若对话也没有目标，则询问课程对象。

本次示例的工具仓库截图可识别出 `NANblogink / bilibilidownloadtool`，对应下方采集工具；它本身没有指定待整理的课程。截图识别由当前AI的视觉能力完成，本仓库脚本不内置OCR或截图自动下载功能。截图可能有账号头像等信息，默认本地保留，上传流程仓库无需附带原图。

## 使用的公开源码采集工具

课程采集使用 **[NANblogink/bilibilidownloadtool](https://github.com/NANblogink/bilibilidownloadtool)**，用于解析B站课程链接、作者/合集与分P，并取得可访问的字幕及公开音视频。它是历史任务实际使用的外部工具；具体使用和分发许可按上游说明。

配合 **[FFmpeg](https://www.ffmpeg.org/)** 做音轨处理和板书抽帧；字幕不足时使用 **[SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)** 做本地中文转写。Wolfram用于数学核验，LaTeX用于讲义输出，二者不承担课程采集。

工具安装与启动见 [依赖说明](docs/DEPENDENCIES.md)。用户提供截图后，AI可在已授权工作范围内完成来源检索、工具检查和采集，无需让用户手工整理整套链接。

## 最小脚本演示：无需虚拟环境、无需账号、无需联网

真实课程从上传截图开始；以下是独立验证工具骨架的离线演示，不包含截图识别、在线检索与真实采集。

安装可用的 Python 3（脚本使用标准库；目标 Python 3.10+），在仓库根目录运行：

```powershell
python scripts/workflow.py doctor
python scripts/workflow.py init --work work/demo
python scripts/workflow.py check --work work/demo
```

如果 Windows 的 `python` 指向了不合适的解释器，用 `py -3` 替换上述 `python`，并保证安装依赖和执行脚本使用同一个解释器。初始化生成范围清单、进度表和 `final/lecture.tex`。检查成功仅表示结构完整；进度默认全部待审。

已安装 TeX Live 或 MiKTeX、具备 `ctex` 与 Fandol 字体时：

```powershell
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=work/demo/final work/demo/final/lecture.tex
```

也可进入 `work/demo/final` 执行两次 `xelatex -interaction=nonstopmode -halt-on-error lecture.tex`，检查目录、引用是否稳定。PDF 阅读器可用 SumatraPDF；它负责查看，编译由 LaTeX 引擎执行。

## 用一节真实课程跑通

1. 在 Codex 中打开本仓库，上传课程截图并使用 [启动指令](docs/CODEX.md)。AI先定位课程，选一节跑通，再扩大范围。
2. AI核实实际页面并填写 `work/demo/manifest.json`：真实作者、标题、BV、分P、CID（如已取得）、时长和范围；同时更新 `progress.json` 的讲次ID并移除演示条目。
3. AI使用 `NANblogink/bilibilidownloadtool` 取得可访问字幕和公开音视频，放入 `work/demo/media/<lesson-id>/`，记录上游版本与采集状态。已有本地材料也可作为输入；不要求导入下载器内部API。
4. 没有字幕时可运行：

```powershell
python -m pip install -r requirements-asr.txt
python scripts/transcribe.py --audio work/demo/media/lesson-001/audio.m4a --out work/demo/transcripts/lesson-001.json --model small --device cpu
```

模型名称在首次使用时可能下载模型；离线使用本地 CTranslate2 模型目录。先用一小段验证中文与公式识别质量，再决定模型规模。

5. 对板书按明确秒数抽帧，输出旁置时间索引：

```powershell
python scripts/workflow.py frames --video work/demo/media/lesson-001/video.mp4 --out work/demo/boards/lesson-001 --times 60 180 300 --ffmpeg ffmpeg
```

6. 阅读完整口述，查看板书，逐条写方法与例题；疑点缩小抽帧间隔或回看片段。五轮实际审阅后更新进度，编译并查看 PDF。

## GitHub 上传边界

上传流程、自己编写的工具、模板、提示词及原创示例。真实课程的音视频、整份转写、板书与讲义默认留在本地，公开发布另行确认材料的发布权限。不要把“公开可看”作为“允许任意再分发”的依据。本包不附带原课程最终 PDF/TeX。

`.gitignore` 默认排除整个 `work/`、模型、媒体和本地凭据。忽略规则不会移除已经被 Git 跟踪的文件，上传前检查实际暂存清单。外部下载器按其原仓库使用条件运行，不随本包重分发。

本项目发布地址为 [dingzhongmai-spec/bili-course-refinery](https://github.com/dingzhongmai-spec/bili-course-refinery)。本仓库原创代码、文档与skill使用 [MIT许可](LICENSE)。外部采集器、FFmpeg、模型和其他依赖按各自许可使用；MIT不覆盖课程材料。不要顺带上传上级目录中的参考书或下载器配置，见 [发布说明](docs/RELEASE.md)。
