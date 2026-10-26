# 智能体实践实验一：Agent 环境配置与 Skill 开发

- **姓名**：张力元
- **学号**：2024187007
- **专业**：智能医学工程（2024 级）
- **GitHub 仓库**：`https://github.com/<用户名>/<仓库名>`　（发布后填写真实链接）

## 目录结构

```
├── skills/
│   ├── deg-analysis/          # Skill 一：差异表达分析（DESeq2 风格）
│   │   ├── SKILL.md
│   │   ├── references/        # data_format / method / screening_criteria
│   │   └── scripts/run_analysis.py
│   └── medical-dialog-qa/     # Skill 二：医疗对话整理
│       ├── SKILL.md
│       ├── references/processing_rules.md
│       ├── scripts/process_dialog.py
│       └── examples/input_dialog.txt
├── outputs/                   # 运行结果
│   ├── deg_results.tsv / .csv # 差异基因结果表
│   ├── volcano_plot.png       # 火山图
│   ├── deg_summary.txt        # 简要说明
│   └── dialog_qa_output.md    # 对话整理输出
├── data/                      # 示例数据（TCGA-KIRC）
├── connection_ok.txt          # API 连接验证
├── 实验记录.txt                # 文件操作体验
└── 实验报告.docx               # 完整实验报告
```

## 复现差异表达分析

```bash
python skills/deg-analysis/scripts/run_analysis.py \
  --counts data/gene_counts.tsv \
  --info data/sample_info.csv \
  --annot data/gene_annotation.tsv \
  --out outputs
```

依赖：Python 3.10+，`numpy`、`pandas`、`scipy`、`matplotlib`（`pip install numpy pandas scipy matplotlib`）。

## 复现对话整理

```bash
python skills/medical-dialog-qa/scripts/process_dialog.py \
  --input skills/medical-dialog-qa/examples/input_dialog.txt \
  --out outputs/dialog_qa_output.md
```

## 分析结论摘要

TCGA-KIRC 肿瘤 vs 正常组织（各 10 例），预过滤后 36,307 个基因，采用 DESeq2 风格
负二项模型（median-of-ratios 归一化 + 离散度 MAP 收缩 + Wald 检验 + BH 校正），
以 |log2FoldChange| ≥ 1 且 padj < 0.05 为筛选标准，共鉴定 **5,485** 个上调、
**4,313** 个下调差异基因。CA9、VEGFA、EGLN3 等缺氧通路标志基因显著上调，UMOD、
AQP2、SLC12A1 等肾小管功能基因显著下调，与肾透明细胞癌分子特征一致。
