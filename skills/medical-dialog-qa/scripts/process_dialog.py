#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
process_dialog.py — 将原始医疗对话整理为结构化问答记录。

只做格式转换与归类，不增补、不推断、不改写原始内容。
"""
from __future__ import annotations

import argparse
import re

# 说话人同义映射
SPEAKER_ALIASES = {
    "doctor": {"医生", "大夫", "doctor", "dr", "dr.", "医师"},
    "patient": {"患者", "病人", "patient"},
}


def classify_speaker(label: str) -> str:
    """将说话人标签归一化为 doctor / patient / other。"""
    key = label.strip().lower()
    for role, aliases in SPEAKER_ALIASES.items():
        if key in aliases:
            return role
    return "other"


def parse_turns(text: str):
    """解析对话为 [(speaker_role, content), ...]。"""
    turns = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([^：:]{1,10})[：:]\s*(.*)$", line)
        if m:
            label, content = m.group(1).strip(), m.group(2).strip()
            role = classify_speaker(label)
            if content:
                turns.append((role, content))
        else:
            # 无说话人标识：视为上一句的续句
            if turns:
                prev_role, prev_content = turns[-1]
                turns[-1] = (prev_role, prev_content + " " + raw)
            else:
                turns.append(("other", raw))
    return turns


def build_qa(turns):
    """将 turn 流配对为问答记录。"""
    qa = []
    i = 0
    n = len(turns)
    while i < n:
        role, _ = turns[i]
        if role != "patient":
            i += 1
            continue
        # 收集连续的 patient 发言
        q_parts = []
        while i < n and turns[i][0] == "patient":
            q_parts.append(turns[i][1])
            i += 1
        # 收集紧跟的连续 doctor 发言
        a_parts = []
        while i < n and turns[i][0] == "doctor":
            a_parts.append(turns[i][1])
            i += 1
        question = " ".join(q_parts)
        answer = " ".join(a_parts) if a_parts else None
        qa.append((question, answer))
    return qa


def render(qa, out_path: str):
    lines = ["# 医疗对话问答记录", ""]
    if not qa:
        lines.append("（未检测到有效对话）")
    for idx, (q, a) in enumerate(qa, 1):
        lines.append(f"## 问题 {idx}")
        lines.append(f"- **患者问**：{q}")
        lines.append(f"- **医生答**：{a if a else '（未回答）'}")
        lines.append("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description="整理医疗对话为问答记录")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()
    turns = parse_turns(text)
    qa = build_qa(turns)
    render(qa, args.out)
    print(f"共生成 {len(qa)} 条问答记录 -> {args.out}")


if __name__ == "__main__":
    main()
