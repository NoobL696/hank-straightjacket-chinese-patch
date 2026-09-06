# -*- coding: utf-8 -*-
"""Hank: Straightjacket 一键汉化补丁 — 翻译对照表生成工具

用法：在补丁项目根目录运行
    python tools/make_patch.py
读取 hank_text/en.txt、hank_text/seq_en.txt，生成 hank_翻译对照表.csv
（来源文件 | 键名 | 英文原文 | 中文翻译 四列）。

注意：hank_text/ 目录（游戏文本提取结果）不随仓库分发，需自行用
tools/extract_text.py 从游戏 resources.assets 中提取。
"""
import csv
import os
import re

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hank_text")
OUT = os.path.join(os.path.dirname(SRC), "hank_翻译对照表.csv")

def main():
    entries = []
    for fname in ("en.txt", "seq_en.txt"):
        path = os.path.join(SRC, fname)
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            m = re.match(r"^(\S+)\s*=\s*(.*)$", line)
            if m:
                entries.append([fname, m.group(1), m.group(2), ""])
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["来源文件", "键名", "英文原文", "中文翻译"])
        w.writerows(entries)
    print("%d 条 -> %s" % (len(entries), OUT))

if __name__ == "__main__":
    main()
