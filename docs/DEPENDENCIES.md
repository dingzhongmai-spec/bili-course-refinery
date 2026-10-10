# 工具依赖

Windows完整安装优先使用根目录`install.ps1`，自动准备下表中需要的采集、媒体、ASR与PDF运行依赖，并记录在`.runtime/config.json`。缺少XeLaTeX时用便携Tectonic；不要求用户另装完整TeX Live。详见[安装说明](INSTALL.md)。下面的手动安装方法仍适用于最小脚本、其他操作系统和自定义工具。

## 按需求安装

|层级|工具|用途|是否必须|
|---|---|---|---|
|最小骨架|Python 标准库|初始化、结构检查、进度记录|必须|
|内容输入|已有字幕、音视频或浏览器播放器|取得原课内容|真实整理必须有一种可核对渠道|
|下载|bilibilidownloadtool 或其他适配器|公开课程本地取得|可选；不内嵌本仓库|
|媒体|FFmpeg，建议同时装 FFprobe|音轨转换、明确时间抽帧、时长核对|使用相应步骤时需要|
|转写|faster-whisper/CTranslate2/PyAV、模型|本地ASR|无字幕且需转写时需要|
|排版|TeX Live/MiKTeX、XeLaTeX、ctex、Fandol、amsmath、hyperref|可编辑中文TeX与PDF|PDF路线需要|
|编译管理|latexmk|多轮编译、引用更新|可选，可直接用XeLaTeX|
|验收|SumatraPDF或其他PDF阅读器；可选PyMuPDF|看真实PDF、辅助渲染和文字检查|PDF阅读能力必须，指定阅读器可选|
|数学计算|本地Wolfram/WolframScript；可替换SymPy|选定公式、反例、图像|可选，证明不能依赖未运行的工具|
|HTML路线|Node、KaTeX、Markdown渲染器|离线阅读和公式渲染|可选，本包最小路线不使用|
|AI执行|Codex桌面版或CLI；其他AI也可|按约束整理和核验|AI辅助路线需要，脚本演示不需要|

无需为了这项工作把全部工具一次安装。依赖版本影响平台兼容性，运行后在私有审阅记录登记实际版本；`requirements-asr.txt` 是可选安装清单，不是历史环境锁文件。

## 下载器适配

本流程从上传截图起步。截图识别使用当前AI的视觉能力，来源定位使用当前可用的网页检索/浏览能力；本仓库不另装OCR，也不要求用户先写完课程清单。截图仅包含工具仓库时，结合对话取得课程目标。

历史任务使用 [NANblogink/bilibilidownloadtool](https://github.com/NANblogink/bilibilidownloadtool) 的本地仓库，先启动检查，再以其解析器辅助采集。通用使用先按该仓库当前 README 安装依赖并运行 `main.py`；本仓库不保证其私有方法 `_get_play_info` 在后续版本稳定。记录下载器提交/版本、分P映射与公开流检查。不要复制个人 `app_config.json` 或账号状态。

历史脚本用了 `PyQt5/requests/curl_cffi/orjson/Pillow/psutil/qrcode/cryptography/pywin32` 等下载器依赖；这些不是本仓库最小依赖。原工具的使用与分发条件以其上游为准。

## ASR

执行 `python -m pip install -r requirements-asr.txt`，默认示例 `small + cpu + int8`。历史任务使用 large-v3-turbo 的 CTranslate2 模型、CUDA、int8_float16，批量16；这是当时机器的选择，不是通用最低配置。

模型首次下载与推理是两阶段；离线推理传本地模型路径。本包转写不会主动发送音频到云端，首次模型下载仍需联网。GPU依赖按 [faster-whisper官方说明](https://github.com/SYSTRAN/faster-whisper#requirements) 匹配 CTranslate2、CUDA、cuBLAS、cuDNN；默认CPU路径避免这组依赖。ASR通过PyAV解码，不要求系统FFmpeg；本包抽帧另需FFmpeg。

## 常见问题

- `python` 与 `pip` 指向不同环境：始终使用同一解释器的 `-m pip`。本地曾存在MSYS Python与Windows Python并存，应先核对。
- GPU DLL 缺失：检查官方匹配要求；用CPU跑通。不要复用另一个人的 `torch/lib` 绝对路径。
- 只有标题、播放器打不开：尝试已授权的字幕或本地取得路线；仍无内容则列缺失，不能据标题生成原课总结。
- 有文件却音视频不全：检查媒体时长、解码和DASH音视频分流，失败不要标成功。
- 抽帧时间不准：本包逐个使用明确的 `-ss` 秒数；请求秒数是定位值，编码、帧率会导致帧精度误差，关键证据要回看附近帧。不要按总览第几格推断精确发言时间。[FFmpeg参数文档](https://www.ffmpeg.org/ffmpeg.html)
- CAS超时：简化表达式、先利用周期/对称性、分拆核验；记录超时，禁止以空输出当通过。
- XeLaTeX报包或字体缺失：按日志补实际缺项；Fandol减少系统中文字体依赖。
- 内置预览失败而本地成功：分别登记，不能声称修复了内置编译服务。
- 中文/空格路径出错：使用Path和参数数组；Node若使用文件URL，以 `fileURLToPath` 还原路径。
