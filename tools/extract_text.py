# -*- coding: utf-8 -*-
"""Hank: Straightjacket — 从游戏 resources.assets 提取全部文本（翻译前置步骤）

用法：
    python tools/extract_text.py                 # 自动定位 Steam 游戏目录
    python tools/extract_text.py "D:\\游戏目录"   # 手动指定
    python tools/extract_text.py --out 输出目录   # 默认输出到 ../hank_text

输出：
    hank_text/en.txt      界面与交互文案（键值对，每行 KEY = TEXT）
    hank_text/seq_en.txt  剧情对白（Dialogator 对话系统）
    以及其他 TextAsset（多为开发模板，可忽略）

依赖：pip install UnityPy
"""
import os
import sys

import UnityPy

MANIFEST = "appmanifest_2277670.acf"
DATA_SUB = "Hank_Straightjacket_Data"
ASSET_NAME = "resources.assets"


def find_game():
    """自动定位游戏目录（扫描 Steam 各库）。"""
    import re
    import winreg

    roots = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            roots.append(winreg.QueryValueEx(k, "SteamPath")[0])
    except OSError:
        pass
    roots += [r"C:\Program Files (x86)\Steam", r"D:\Steam", r"E:\Steam"]
    libs = []
    for r in roots:
        if os.path.isdir(r) and r not in libs:
            libs.append(r)
        vdf = os.path.join(r, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding="utf-8", errors="ignore").read()):
                p = p.replace("\\\\", "\\")
                if p not in libs:
                    libs.append(p)
    for lib in libs:
        p = os.path.join(lib, "steamapps", "common", "Hank Straightjacket")
        if os.path.isfile(os.path.join(p, DATA_SUB, ASSET_NAME)):
            return p
    raise SystemExit("未找到游戏目录，请用第一个参数手动指定")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    game = args[0] if args else find_game()
    out_idx = sys.argv.index("--out") + 1 if "--out" in sys.argv else None
    outdir = os.path.abspath(sys.argv[out_idx]) if out_idx else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hank_text")
    os.makedirs(outdir, exist_ok=True)

    asset = os.path.join(game, DATA_SUB, ASSET_NAME)
    if not os.path.isfile(asset):
        raise SystemExit("目录无效：%s" % game)
    print("游戏目录:", game)

    env = UnityPy.load(asset)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            ta = obj.read()
            data = ta.m_Script
            if isinstance(data, str):
                data = data.encode("utf-8", "surrogateescape")
            path = os.path.join(outdir, ta.m_Name + ".txt")
            with open(path, "wb") as f:
                f.write(data)
            print("导出 %s (%d bytes)" % (ta.m_Name, len(data)))


if __name__ == "__main__":
    main()
