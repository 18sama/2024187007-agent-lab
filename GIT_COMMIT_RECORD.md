# Git 提交记录（本地仓库准备说明）

> 说明：本次执行环境（Windows 沙箱）未安装 Git，无法在此处直接运行 `git init`
> 与 `git commit`。以下为已准备好的本地仓库结构与**精确可复现的命令**，
> 在有 Git 的机器上逐条执行即可生成与记录一致的提交历史。

## 仓库结构（已就绪）
```
2024187007-张力元-智能体实践实验一/
├── .gitignore
├── README.md
├── 实验报告.docx
├── 课后任务清单.md
├── skills/            # 两个自建 Skill
├── reused-skill/      # 现有 Skill 安装改造
├── outputs/           # 运行结果
├── data/              # 示例数据
├── connection_ok.txt
└── 实验记录.txt
```

## 计划提交历史（提交说明 / 内容）
1. `init: 实验一项目骨架与示例数据` — .gitignore、README、data/、示例 txt
2. `feat: 新增差异表达分析 Skill（deg-analysis）` — skills/deg-analysis/
3. `feat: 新增医疗对话整理 Skill（medical-dialog-qa）` — skills/medical-dialog-qa/
4. `results: 差异表达结果表与火山图、对话整理输出` — outputs/
5. `reuse: 安装改造 scientific-writing Skill` — reused-skill/
6. `docs: 实验报告与课后任务清单` — 实验报告.docx、课后任务清单.md

## 精确命令（在有 Git 的机器上执行）
```bash
cd "2024187007-张力元-智能体实践实验一"
git init
git add .gitignore README.md data connection_ok.txt 实验记录.txt
git commit -m "init: 实验一项目骨架与示例数据"

git add skills/deg-analysis
git commit -m "feat: 新增差异表达分析 Skill（deg-analysis）"

git add skills/medical-dialog-qa
git commit -m "feat: 新增医疗对话整理 Skill（medical-dialog-qa）"

git add outputs
git commit -m "results: 差异表达结果表与火山图、对话整理输出"

git add reused-skill
git commit -m "reuse: 安装改造 scientific-writing Skill"

git add 实验报告.docx 课后任务清单.md
git commit -m "docs: 实验报告与课后任务清单"

# 发布到 GitHub（示例仓库名，按实际修改）
# git remote add origin https://github.com/<用户名>/medical-dialog.git
# git push -u origin main
```

## 复现问题记录
- 本机无 Git：需在装有 Git 的环境按上述命令补齐提交与推送。
- 示例数据体积较大（gene_counts.tsv 约 4.3MB），推送前确认仓库容量与 .gitignore 策略。
