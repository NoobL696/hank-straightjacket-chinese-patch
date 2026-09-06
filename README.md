# Hank: Straightjacket 汉化补丁

一款 Unity 小品级叙事解谜游戏 [Hank: Straightjacket](https://store.steampowered.com/app/2277670/)（My Next Games，免费游玩）的非官方简体中文补丁，支持**全文本汉化**：界面、剧情对白、玩家选项、动态加载字幕，并保留游戏的文字动效（打字机逐字显示、台词重点词标红等）。

> **免责声明**：本项目为同人汉化，仅供个人学习交流使用。游戏文本版权归开发商 My Next Games 所有，请支持正版（Steam 免费游玩）。请勿将本项目内容用于商业用途。

## 汉化原理

游戏文本以明文键值对（`KEY = TEXT`）存放在 `Hank_Straightjacket_Data\resources.assets` 的两个 TextAsset（`en` / `seq_en`）中。本补丁：

1. **资产级替换**：用 [UnityPy](https://github.com/K0lb3/UnityPy) 将两个 TextAsset 的值改写为中文（原文件自动备份为 `resources.assets.bak`），静态与动态加载的文本全部生效；
2. **字体覆盖**：游戏自带 TMP 字体（LiberationSans SDF）不含中文字形，通过 [BepInEx](https://github.com/BepInEx/BepInEx) + [XUnity.AutoTranslator](https://github.com/bbepis/XUnity.AutoTranslator) 在运行时用系统字体 **Noto Sans SC** 动态创建 TMP 字体渲染中文；
3. **幂等安装**：始终从英文备份读取原文重新替换，重复安装安全。

## 使用方法

### 方式一：一键补丁程序（推荐）

```bash
# 构建单文件 exe（约 150 MB，内含 BepInEx/XUnity 框架与翻译数据）
cd src
pyinstaller --onefile --noconsole --name "Hank汉化补丁" \
    --collect-data UnityPy \
    --add-data "../data/translations.json;." \
    --add-data "../data/en_text;en_text" \
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

### 方式二：仅替换文本（无需框架）

如果目标游戏目录已有 BepInEx/XUnity 框架（且字体配置正确），也可以只用脚本替换文本资产：

```bash
pip install UnityPy
python tools/extract_text.py          # 提取游戏文本（hank_text/）
python tools/replace_assets.py        # 备份并替换为中文（需设置 HANK_GAME_DIR 或自动定位）
python tools/make_patch.py            # 生成人工校对用的翻译对照表 CSV
```

## 已知限制

- Steam「验证文件完整性」会还原英文，重新运行补丁即可；
- XUnity 未钩住 `TMP_Text.SetCharArray` 的个别重载（日志有警告），已通过资产级替换绕过，不影响使用；
- 字体依赖系统安装 **Noto Sans SC**（Google Fonts 免费下载），缺字会显示方块。

## 项目结构

```
├── src/patcher_hank_cn.py   # 一键补丁程序（GUI + 控制台模式）
├── data/translations.json   # 196 条人工翻译（英文原文 -> 中文）
├── data/en_text/            # 游戏原始英文文本（en.txt / seq_en.txt）
├── tools/extract_text.py    # 从 resources.assets 提取游戏文本
├── tools/replace_assets.py  # 直接替换文本资产（无框架场景）
└── tools/make_patch.py      # 生成翻译对照表 CSV
```

## 环境

- Windows（Steam 版游戏）
- Python 3.10+：`pip install UnityPy pyinstaller`
- 游戏版本：Unity 2023.2.20f1（Mono / TMP 1.4.0）
