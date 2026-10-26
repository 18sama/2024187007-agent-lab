# 数据格式要求

## 输入文件

### 1. 基因表达矩阵 `gene_counts.tsv`
- 分隔符：制表符（tab）。
- 第一列：`gene_id`（Ensembl 基因 ID，如 `ENSG00000000003.15`）。
- 其余列：样本 ID（如 `TCGA-A3-3358-11A`），每个样本一列。
- 数值：**原始整数 read counts**，不允许小数或已归一化的值（如 TPM/CPM）。
- 允许存在 0 值（表示该基因在该样本中无 reads），不允许缺失值（NaN）。

### 2. 样本分组信息 `sample_info.csv`
- 分隔符：逗号。
- 必需列：
  - `sample_id`：与 counts 矩阵列名完全一致。
  - `group`：分组标签，本 Skill 支持 `Normal` 与 `Tumor` 两组。
- 样本顺序可与 counts 列顺序不同，脚本会自动按列名重排并校验一一对应。

### 3. 基因注释 `gene_annotation.tsv`
- 分隔符：制表符。
- 必需列：
  - `gene_id`：与 counts 矩阵行名一致。
  - `gene_name`：基因符号（如 `TSPAN6`）。
  - `gene_type`：基因类型（可选，用于过滤蛋白编码基因）。

## 数据检查要点
1. counts 的列集合与 sample_info 的 sample_id 集合应完全相同。
2. 每个基因行名都能在注释表中找到对应条目。
3. 分组为二分类（Normal/Tumor），且两组均有生物学重复（本实验各 10 例）。
