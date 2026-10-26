# 现有 Skill 安装改造记录

## 一、原始来源
- Skill 名称：`scientific-writing`（科学写作）
- 来源：课程随附资料（第1次实验课/skills/scientific-writing/），原始作者 K-Dense Inc.
- 许可：MIT License（见 SKILL.md 头部的 `license: MIT license`）
- 版本 / 记录：随课程资料提供，无独立版本号

## 二、安装前的阅读与核查
- 阅读 `SKILL.md`：确认其适用任务（科学论文/报告写作、IMRAD 结构、引用、图表规范）。
- 阅读 `references/`：imrad_structure、citation_styles、figures_tables、
  writing_principles、reporting_guidelines、professional_report_formatting。
- 核查依赖：`scripts/generate_image.py`、`generate_schematic.py` 需图片生成能力；
  本实验仅复用其写作规范部分，未调用图片生成脚本。
- 确认许可：MIT，允许复制、修改与再分发（保留版权与许可声明）。

## 三、安装位置
- 安装到当前 Agent 支持的 skills 目录，本提交包中为
  `reused-skill/scientific-writing/`（原样保留 + 本次改造新增文件）。

## 四、本次改造内容
| 项目 | 改动 |
| --- | --- |
| 新增 `references/chinese_adaptation.md` | 将面向英文期刊的规范适配为中文课程报告场景 |
| 保留 | SKILL.md、references/、scripts/、assets/ 原样保留，未删除任何内容 |
| 未改动 | 图片/示意图生成脚本（本实验未用到，未触碰） |

改造的核心：把"IMRAD 期刊论文写作"中的语言与结构要求，转译为中文课程实验报告
可用的规范（保留 IMRAD 骨架与图表/引用红线，放开语言与结构上的期刊约束）。

## 五、前后输出对比
- **改造前（原 skill）**：面向英文期刊，强调 Abstract 不加小节标签、禁止列表、
  需图形摘要（graphical abstract）等期刊要求，中文课程报告直接套用会显得生硬。
- **改造后（本次）**：新增中文适配文档，明确中文报告可用"实验目的/环境/步骤/结果/
  讨论/结论"结构、允许第一人称叙述、术语首次出现附英文原文；同时保留"不编造数据、
  结果与讨论分离"的核验红线。

## 六、复现记录
- 安装：将原 skill 文件夹复制到 Agent 支持的 skills 目录即可被识别。
- 使用：在新会话中用 `/scientific-writing` 或明确要求"使用 scientific-writing 规范
  撰写报告"。
- 核验：确认输出报告包含 IMRAD 骨架、图表有标题与单位、数值可溯源、结论不夸大。
