# -*- coding: utf-8 -*-
"""Hank: Straightjacket — 直接替换文本资产为中文（适合已装好 BepInEx/XUnity
框架、只想更新文本的场景）

用法：
    python tools/replace_assets.py                # 自动定位 Steam 游戏目录
    python tools/replace_assets.py "D:\\游戏目录"  # 手动指定

行为：
    1. 首次运行备份 resources.assets -> resources.assets.bak
    2. 从备份读取英文原文，按 data/translations.json 替换为中文后写回
    3. 重复运行安全（幂等）

依赖：pip install UnityPy
"""
import json
import os
import shutil
import sys

import UnityPy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def to_chinese_bytes(en_text, table):
    out = []
    for line in en_text.splitlines():
        if not line.strip():
            continue
        k, sep, v = line.partition(" = ")
        if not sep:
            continue
        en = v.strip()
        if en not in table:
            raise KeyError("缺少翻译: %r" % en)
        out.append(k + " = " + table[en])
    return ("\n".join(out) + "\n").encode("utf-8")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    game = args[0] if args else find_game()
    asset = os.path.join(game, DATA_SUB, ASSET_NAME)
    if not os.path.isfile(asset):
        raise SystemExit("目录无效：%s" % game)

    exe = os.path.join(game, "Hank_Straightjacket.exe")
    if os.path.exists(exe):
        r = os.popen('tasklist /FI "IMAGENAME eq Hank_Straightjacket.exe" /FO CSV /NH')
        if "Hank_Straightjacket" in r.read():
            raise SystemExit("游戏正在运行，请先关闭")

    table = json.load(open(os.path.join(ROOT, "data", "translations.json"), encoding="utf-8"))

    bak = asset + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(asset, bak)
        print("已备份 -> resources.assets.bak")

    env = UnityPy.load(bak)  # 始终从备份读英文，保证幂等
    new = {}
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            ta = obj.read()
            if ta.m_Name in ("en", "seq_en"):
                data = ta.m_Script
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                new[ta.m_Name] = to_chinese_bytes(data, table)
    missing = {"en", "seq_en"} - set(new)
    if missing:
        raise SystemExit("备份中缺少文本资产: %s" % missing)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            ta = obj.read()
            if ta.m_Name in new:
                ta.m_Script = new[ta.m_Name].decode("utf-8")
                ta.save()
    with open(asset, "wb") as f:
        f.write(env.file.save())
    print("[OK] 已替换 en / seq_en 为中文（%s）" % game)


if __name__ == "__main__":
    main()
