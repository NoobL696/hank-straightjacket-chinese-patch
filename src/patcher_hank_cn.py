# -*- coding: utf-8 -*-
"""Hank: Straightjacket 一键汉化补丁
- 自动定位 Steam 所有游戏副本（含非活动库）
- 安装中文：备份并替换 resources.assets 内的 en/seq_en 文本资产
            缺少 BepInEx/XUnity 框架的副本自动补装（内置完整框架）
            配置系统字体 Noto Sans SC 渲染中文
- 恢复英文：用各副本自己的备份还原
"""
import json
import os
import re
import shutil
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

DATA_SUB = "Hank_Straightjacket_Data"
ASSET_NAME = "resources.assets"
EXE_NAME = "Hank_Straightjacket.exe"
MANIFEST = "appmanifest_2277670.acf"
FRAMEWORK_MARK = os.path.join("BepInEx", "core", "BepInEx.dll")

def res_path(*names):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *names)

def load_translations():
    with open(res_path("translations.json"), encoding="utf-8") as f:
        return json.load(f)

# ---------- 游戏目录定位 ----------

def steam_roots():
    roots = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            roots.append(winreg.QueryValueEx(k, "SteamPath")[0])
    except OSError:
        pass
    roots += [r"C:\Program Files (x86)\Steam", r"D:\Steam", r"E:\Steam"]
    out = []
    for r in roots:
        if r and os.path.isdir(r) and r not in out:
            out.append(r)
    return out

def library_paths():
    libs = []
    for root in steam_roots():
        libs.append(root)
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            try:
                text = open(vdf, encoding="utf-8", errors="ignore").read()
                for p in re.findall(r'"path"\s+"([^"]+)"', text):
                    p = p.replace("\\\\", "\\")
                    if p not in libs:
                        libs.append(p)
            except OSError:
                pass
    return libs

def find_game_dirs():
    """返回 (排序后的游戏目录列表, 每个目录的说明)。"""
    found = {}  # normcase -> (path, has_manifest, has_framework, has_asset)
    for lib in library_paths():
        game = os.path.join(lib, "steamapps", "common", "Hank Straightjacket")
        data = os.path.join(game, DATA_SUB)
        if not os.path.isfile(os.path.join(data, ASSET_NAME)):
            continue
        key = os.path.normcase(game)
        if key in found:
            continue
        found[key] = (game,
                      os.path.isfile(os.path.join(lib, "steamapps", MANIFEST)),
                      os.path.isfile(os.path.join(game, FRAMEWORK_MARK)),
                      True)
    ranked = sorted(found.values(), key=lambda t: (not t[1], not t[2]))
    return [(t[0], {"manifest": t[1], "framework": t[2]}) for t in ranked]

def game_is_running(game_dir):
    try:
        import subprocess
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq %s" % EXE_NAME, "/FO", "CSV", "/NH"],
                           capture_output=True)
        out = r.stdout.decode("utf-8", "ignore")
    except Exception:
        return False
    return EXE_NAME.lower() in out.lower()

# ---------- 核心逻辑 ----------

def to_chinese_bytes(en_text, T):
    out = []
    for line in en_text.splitlines():
        if not line.strip():
            continue
        k, sep, v = line.partition(" = ")
        if not sep:
            continue
        en = v.strip()
        if en not in T:
            raise KeyError(en)
        out.append(k + " = " + T[en])
    return ("\n".join(out) + "\n").encode("utf-8")

def ensure_framework(game_dir, log):
    if os.path.isfile(os.path.join(game_dir, FRAMEWORK_MARK)) and \
       os.path.isfile(os.path.join(game_dir, "winhttp.dll")):
        return
    payload = res_path("payload")
    if not os.path.isdir(payload):
        log("!! 内置框架缺失，跳过（文字可能显示为方块）")
        return
    shutil.copytree(payload, game_dir, dirs_exist_ok=True)
    log("已补装 BepInEx/XUnity 汉化框架（该副本此前没有）")

def replace_assets(game_dir, T, log):
    import UnityPy
    asset = os.path.join(game_dir, DATA_SUB, ASSET_NAME)
    bak = asset + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(asset, bak)
        log("已备份原文件 -> resources.assets.bak")
    env = UnityPy.load(bak)  # 始终从备份读英文，重复安装幂等
    new = {}
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            ta = obj.read()
            if ta.m_Name in ("en", "seq_en"):
                data = ta.m_Script
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                new[ta.m_Name] = to_chinese_bytes(data, T)
    missing = {"en", "seq_en"} - set(new)
    if missing:
        raise RuntimeError("备份中缺少文本资产: %s" % missing)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            ta = obj.read()
            if ta.m_Name in new:
                ta.m_Script = new[ta.m_Name].decode("utf-8")
                ta.save()
    with open(asset, "wb") as f:
        f.write(env.file.save())
    log("已替换 resources.assets 中的 en / seq_en 为中文")

def fix_font_config(game_dir, log):
    ini = os.path.join(game_dir, "BepInEx", "config", "AutoTranslatorConfig.ini")
    if not os.path.exists(ini):
        return
    bak = ini + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(ini, bak)
    text = open(ini, encoding="utf-8").read()
    text = re.sub(r"(?m)^OverrideFont=.*$", "OverrideFont=Noto Sans SC", text)
    text = re.sub(r"(?m)^OverrideFontTextMeshPro=.*$", "OverrideFontTextMeshPro=Noto Sans SC", text)
    with open(ini, "w", encoding="utf-8") as f:
        f.write(text)
    log("字体配置已指向系统字体 Noto Sans SC")

def write_translation_backstop(game_dir, T, log):
    tdir = os.path.join(game_dir, "BepInEx", "Translation", "zh", "Text")
    os.makedirs(tdir, exist_ok=True)
    lines = ["%s=%s" % (en, cn) for en, cn in T.items() if "\n" not in en]
    with open(os.path.join(tdir, "_AutoGeneratedTranslations.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("兜底翻译文件已写入 BepInEx/Translation/zh/Text/")

def install_one(game_dir, T, log):
    log("-" * 46)
    log("副本：" + game_dir)
    if game_is_running(game_dir):
        raise RuntimeError("游戏正在运行，请先关闭游戏再安装补丁")
    ensure_framework(game_dir, log)
    replace_assets(game_dir, T, log)
    fix_font_config(game_dir, log)
    write_translation_backstop(game_dir, T, log)

def install(game_dirs, T, log):
    log("=" * 46)
    log("开始安装中文补丁，共 %d 个游戏副本" % len(game_dirs))
    for g in game_dirs:
        install_one(g, T, log)
    log("=" * 46)
    log("[OK] 安装完成！启动游戏即可游玩中文版")

def restore_one(game_dir, log):
    log("-" * 46)
    log("副本：" + game_dir)
    if game_is_running(game_dir):
        raise RuntimeError("游戏正在运行，请先关闭游戏再还原")
    asset = os.path.join(game_dir, DATA_SUB, ASSET_NAME)
    bak = asset + ".bak"
    if not os.path.exists(bak):
        log("无备份（该副本未打过补丁），跳过")
        return
    shutil.copy2(bak, asset)
    log("已用备份还原 resources.assets（英文原版）")
    ini_bak = os.path.join(game_dir, "BepInEx", "config", "AutoTranslatorConfig.ini.bak")
    if os.path.exists(ini_bak):
        shutil.copy2(ini_bak, ini_bak[:-4])
        log("已还原字体配置")

def restore(game_dirs, log):
    log("=" * 46)
    log("开始恢复英文原版，共 %d 个游戏副本" % len(game_dirs))
    for g in game_dirs:
        restore_one(g, log)
    log("=" * 46)
    log("[OK] 恢复完成")

# ---------- GUI ----------

class App:
    def __init__(self, root):
        self.root = root
        root.title("Hank: Straightjacket 汉化补丁")
        root.geometry("640x470")
        root.resizable(False, False)
        self.T = load_translations()

        top = ttk.Frame(root, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="游戏目录：").pack(side="left")
        self.var_path = tk.StringVar()
        self.entry = ttk.Entry(top, textvariable=self.var_path)
        self.entry.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(top, text="浏览…", command=self.browse, width=8).pack(side="left")

        btns = ttk.Frame(root, padding=(12, 4))
        btns.pack(fill="x")
        self.btn_install = ttk.Button(btns, text="安装中文补丁（所有副本）", command=self.do_install, width=24)
        self.btn_install.pack(side="left", padx=(0, 8))
        self.btn_restore = ttk.Button(btns, text="恢复英文原版", command=self.do_restore, width=16)
        self.btn_restore.pack(side="left")
        ttk.Label(root, text="自动备份原文件，可随时一键还原。检测到多个游戏副本时会全部处理。",
                  foreground="#666", padding=(14, 2)).pack(anchor="w")

        self.txt = tk.Text(root, height=16, state="disabled", font=("Consolas", 9))
        self.txt.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        found = find_game_dirs()
        if found:
            self.var_path.set(found[0][0])
            self.log("检测到 %d 个游戏副本：" % len(found))
            for path, info in found:
                tags = []
                tags.append("Steam活动库" if info["manifest"] else "非活动库")
                tags.append("已有汉化框架" if info["framework"] else "将自动补装框架")
                self.log("  [%s] %s" % (" | ".join(tags), path))
        else:
            self.log("未自动找到游戏目录，请点击「浏览…」手动选择。")

    def log(self, msg):
        self.txt.configure(state="normal")
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def browse(self):
        d = filedialog.askdirectory(title="选择游戏目录（包含 Hank_Straightjacket_Data）")
        if d:
            self.var_path.set(d)

    def targets(self):
        """手动填了有效目录 → 只处理该目录；否则处理所有检测到的副本。"""
        custom = self.var_path.get().strip()
        if custom and os.path.isfile(os.path.join(custom, DATA_SUB, ASSET_NAME)):
            return [custom], "指定目录"
        found = [p for p, _ in find_game_dirs()]
        if not found:
            raise RuntimeError("未找到任何有效的游戏目录（需包含 %s\\%s）" % (DATA_SUB, ASSET_NAME))
        return found, "所有检测到的副本"

    def run_bg(self, fn):
        def worker():
            self.btn_install.configure(state="disabled")
            self.btn_restore.configure(state="disabled")
            try:
                fn()
            except Exception as e:
                self.log("[错误] " + str(e))
                messagebox.showerror("汉化补丁", str(e))
            finally:
                self.btn_install.configure(state="normal")
                self.btn_restore.configure(state="normal")
        threading.Thread(target=worker, daemon=True).start()

    def do_install(self):
        try:
            targets, label = self.targets()
        except Exception as e:
            messagebox.showerror("汉化补丁", str(e))
            return
        self.run_bg(lambda: install(targets, self.T, self.log))

    def do_restore(self):
        try:
            targets, label = self.targets()
        except Exception as e:
            messagebox.showerror("汉化补丁", str(e))
            return
        self.run_bg(lambda: restore(targets, self.log))


def main_console():
    """--console 模式：无界面一键安装（供自动化测试/高级用户）。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    T = load_translations()
    found = [p for p, _ in find_game_dirs()]
    if not found:
        print("未找到游戏目录"); sys.exit(1)
    if len(sys.argv) > 2 and sys.argv[1] == "--dir":
        found = [sys.argv[2]]
    if "--restore" in sys.argv:
        restore(found, print)
    else:
        install(found, T, print)
    input("按回车键退出…")

if __name__ == "__main__":
    if "--console" in sys.argv:
        main_console()
    else:
        root = tk.Tk()
        try:
            ttk.Style().theme_use("vista")
        except Exception:
            pass
        App(root)
        root.mainloop()
