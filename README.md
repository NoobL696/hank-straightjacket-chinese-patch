# Hank: Straightjacket 汉化补丁

一款 Unity 小品级叙事解谜游戏 [Hank: Straightjacket](https://store.steampowered.com/app/2277670/)（My Next Games，免费游玩）的非官方简体中文补丁，支持**全文本汉化**：界面、剧情对白、玩家选项、动态加载字幕，并保留游戏的文字动效（打字机逐字显示、台词重点词标红等）。

## ⚠️ 本项目由 AI 生成

本项目（包括全部代码、196 条译文、文档与构建配置）**由大语言模型（GLM，经 ZCode 智能体执行）自动生成**，仅经少量真机测试，请务必了解：

- **可能存在未知 bug**：未做系统性测试，边界情况（异常游戏版本、非标准安装路径、系统缺少 Noto Sans SC 字体等）未经充分验证；
- **译文质量**：全部译文为 AI 翻译，未经专业译者审校，语气、术语、梗的处理可能有偏差或不准确；
- **使用方式**：文档可能存在描述不完整或与实际行为不一致的地方；
- **安全提示**：请自行阅读源码后再运行，一切使用风险自负；
- 遇到问题欢迎提 Issue，但作者（也是人类监督者）不承诺修复时效。

> **免责声明**：本项目为同人汉化，仅供个人学习交流使用。游戏文本版权归开发商 My Next Games 所有，请支持正版（Steam 免费游玩）。请勿将本项目内容用于商业用途。
>
> **版权说明**：为控制版权暴露面，本仓库**不分发任何游戏文本原文或游戏资源**——`data/translations.json` 仅包含补丁互操作所必需的翻译映射；补丁所需的英文原文始终来自玩家本地游戏文件（安装时自动生成的 `resources.assets.bak` 备份）；如需游戏原文文本，请用 `tools/extract_text.py` 对**你自己的**游戏副本提取，提取结果请勿分发。

## 汉化原理

游戏文本以明文键值对（`KEY = TEXT`）存放在 `Hank_Straightjacket_Data\resources.assets` 的两个 TextAsset（`en` / `seq_en`）中。本补丁：

1. **资产级替换**：用 [UnityPy](https://github.com/K0lb3/UnityPy) 将两个 TextAsset 的值改写为中文（原文件自动备份为 `resources.assets.bak`），静态与动态加载的文本全部生效；
2. **字体覆盖**：游戏自带 TMP 字体（LiberationSans SDF）不含中文字形，通过 [BepInEx](https://github.com/BepInEx/BepInEx) + [XUnity.AutoTranslator](https://github.com/bbepis/XUnity.AutoTranslator) 在运行时用系统字体 **Noto Sans SC** 动态创建 TMP 字体渲染中文；
3. **幂等安装**：始终从英文备份读取原文重新替换，重复安装安全。

## 使用方法

### 方式一：纯手动替换文件（推荐，零风险）

**不运行本仓库的任何程序**：框架从官方开源发布页下载，汉化文件手动复制，文本用开源 GUI 工具（UABEA）替换。不需要管理员权限，不涉及杀毒软件放行。

👉 详细图文步骤见 **[manual-patch/使用说明.md](manual-patch/使用说明.md)**，或直接下载 Release 附件里的 `Hank-CN-ManualPatch.zip`（内含说明与全部汉化文件）。

### 方式二：一键补丁程序（便捷，但可能被杀软误报）

未签名的 PyInstaller 单文件 exe 可能触发杀毒软件启发式误报——介意的话请用方式一，或自行从源码构建。

```bash
# 构建单文件 exe（约 150 MB，内含 BepInEx/XUnity 框架与翻译数据）
cd src
pyinstaller --onefile --noconsole --name "Hank汉化补丁" \
    --collect-data UnityPy \
    --add-data "../data/translations.json;." \
    --add-data "payload;payload" \
    patcher_hank_cn.py
```

构建前需要准备 `src/payload/` 目录（补丁运行时框架，不随仓库分发）：

| 来源 | 放置位置 |
| --- | --- |
| BepInEx 5.4.x（含 XUnity.AutoTranslator 5.6+ / XUnity.ResourceRedirector 插件） | `payload/BepInEx/` |
| Unity Doorstop：`winhttp.dll`、`doorstop_config.ini`、`.doorstop_version` | `payload/` |

> 最简单的获取方式：用任意「BepInEx + XUnity.AutoTranslator」一键工具给游戏装一遍框架，然后把游戏目录下的 `BepInEx/`、`winhttp.dll`、`doorstop_config.ini`、`.doorstop_version` 复制到 `payload/`。注意删掉 `BepInEx/cache` 和 `LogOutput.log*`。

运行 exe 后：自动扫描 Steam 各库定位游戏（支持多副本），点「安装中文补丁」即可；「恢复英文原版」一键还原。

### 方式三：脚本替换文本（无需框架）

如果目标游戏目录已有 BepInEx/XUnity 框架（且字体配置正确），也可以只用脚本替换文本资产：

```bash
pip install UnityPy
python tools/extract_text.py          # 从你自己的游戏副本提取文本（hank_text/，请勿分发）
python tools/replace_assets.py        # 备份并替换为中文（自动定位游戏目录）
python tools/make_patch.py            # 生成人工校对用的翻译对照表 CSV
```

## 已知限制

- Steam「验证文件完整性」会还原英文，重新运行补丁即可；
- XUnity 未钩住 `TMP_Text.SetCharArray` 的个别重载（日志有警告），已通过资产级替换绕过，不影响使用；
- 字体依赖系统安装 **Noto Sans SC**（Google Fonts 免费下载），缺字会显示方块。

## 项目结构

```
├── manual-patch/            # 纯手动汉化包（说明 + 汉化文件，推荐）
├── src/patcher_hank_cn.py   # 一键补丁程序（GUI + 控制台模式）
├── data/translations.json   # 196 条 AI 翻译映射（英文原文 -> 中文）
├── tools/extract_text.py    # 从你自己的游戏副本提取文本（提取结果勿分发）
├── tools/replace_assets.py  # 直接替换文本资产（无框架场景）
└── tools/make_patch.py      # 生成翻译对照表 CSV
```

> 本仓库不分发 `hank_text/`（游戏文本提取结果）。`data/translations.json` 中的英文键来自游戏原文，仅为补丁互操作所必需。

## 环境

- Windows（Steam 版游戏）
- Python 3.10+：`pip install UnityPy pyinstaller`
- 游戏版本：Unity 2023.2.20f1（Mono / TMP 1.4.0）
