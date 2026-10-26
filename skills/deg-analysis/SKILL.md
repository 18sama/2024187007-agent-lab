---
name: deg-analysis
description: 对 RNA-seq 原始 read counts 数据（基因 × 样本）进行两组间的差异表达分析。当用户需要对表达矩阵做两组比较、输出差异基因结果表与火山图时使用本 Skill。它读取样本分组信息，自动检查样本与分组是否对应，采用 DESeq2 风格的负二项模型完成归一化、离散度估计、显著性检验与 BH 校正，输出包含 gene name/ID、log2FoldChange、P 值、校正后 P 值的结果表以及火山图。
---

# 差异表达分析（deg-analysis）

## 适用任务
- 输入：原始整数 read counts 矩阵（TSV，行 = 基因，列 = 样本）、样本分组表（CSV，含 sample_id 与 group）、基因注释表（TSV，含 gene_id 与 gene_name）。
- 输出：差异基因结果表（TSV/CSV）、火山图（PNG）、简短说明文本。
- 适用场景：两组样本（如 Tumor vs Normal）的基因表达比较。

## 输入输出
| 类型 | 路径约定 | 说明 |
| --- | --- | --- |
| 输入 | `--counts` | 原始 counts，行为基因、列为样本，`gene_id` 为第一列 |
| 输入 | `--info` | 样本分组，需含 `sample_id` 与 `group`（取值 Normal/Tumor） |
| 输入 | `--annot` | 基因注释，需含 `gene_id` 与 `gene_name` |
| 输出 | `--out` | 输出目录，生成 `deg_results.tsv/.csv`、`volcano_plot.png`、`deg_summary.txt` |

## 参考资料的读取条件
- 处理前先读 `references/data_format.md` 确认数据格式与列名要求。
- 需要了解统计方法细节时读 `references/method.md`。
- 需要确认筛选标准时读 `references/screening_criteria.md`。

## 脚本调用方法
```bash
python scripts/run_analysis.py \
  --counts <gene_counts.tsv> \
  --info <sample_info.csv> \
  --annot <gene_annotation.tsv> \
  --out <输出目录> \
  [--min-total 10]
```
脚本为纯 Python，依赖 numpy / pandas / scipy / matplotlib，无需联网。

## 结果核验要求
1. 样本与分组必须一一对应：脚本内会断言分组集合恰为 {Normal, Tumor}，并按样本列顺序重排分组。
2. 结果表必须包含 `gene_name`、`gene_id`、`log2FoldChange`、`pvalue`、`padj`。
3. 火山图 x 轴为 log2FoldChange、y 轴为 -log10(padj)，并标注阈值线。
4. 用已知肾癌标志基因（如 CA9、VEGFA、EGLN3）交叉验证方向是否合理。
