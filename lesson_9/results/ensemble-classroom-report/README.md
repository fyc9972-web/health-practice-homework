# 集成学习课堂实践报告

这是一份面向零基础课堂讲解的研究报告：先解释知识，再展示对应实践，最后讨论证据范围。WDBC 与 CTG 两套方案均保留，覆盖工作单 A–H。

## 从哪里开始

- `index.html`：推荐先看。图表已内嵌，可离线打开；左侧目录可跳转，图表可点击放大，顶部可切换讲解提示和大字阅读。
- `report.pdf`：固定排版，适合分享、打印、课堂投屏。
- `report.docx`：可编辑版本，含原生可编辑公式与全部图表。
- `report.md`：正文源文稿，便于检索与修改；动态图表数表由模板与结果生成。
- `figures/`：12 幅原始图，每幅同时提供 SVG 与 220 dpi PNG。11 幅主图和 1 幅补充图。
- `results/`：本次真实开发实验结果，含逐折指标、逐轮结果和预测稳定性记录。

报告约 2.6 万字符，使用分点讲解、公式注释、实例读图、10 条课堂讲解提示、20 分钟展示路线和两套研究备忘录示例。它不替代个人实验记录。

## 实验范围

本次只使用学生 train 与 validation，未读取教师目录或任何锁定测试文件。CTG 主验证和交叉验证按录音分组；LR、SVM 使用折内标准化。七类模型的主参数沿用原演示脚本。报告中区分了课堂主实验、补充诊断与探索性指标区间，没有把教师参考数字当作新实测结果。

主稳定性比较采用 30 份共享训练行 bootstrap；另补充 CTG 30 次整录音训练 bootstrap。固定模型区间也只在验证集上展示，并明确不涵盖重训、选模或外部人群变化。

## 如何重现

从 `lesson_9` 根目录运行，建议使用独立课程 Python 环境：

```powershell
python -m pip install -r ensemble-classroom-report/requirements-report.txt
python ensemble-classroom-report/scripts/run_experiments.py
python ensemble-classroom-report/scripts/make_figures.py
python ensemble-classroom-report/scripts/build_report.py
```

若仅修改文字或版式，无须重新跑实验；修改 `report.template.md` 后直接运行 `build_report.py`。该脚本从已保存的 CSV 生成主表，从 SVG 内嵌网页图，再生成 Word 与 PDF。

PDF 导出使用本机 Chrome 或 Edge 的无窗口打印。若环境不允许启动浏览器，可加 `--no-pdf` 先生成 HTML 和 Word，随后在浏览器中打开 `index.html` 并打印为 PDF。网页不请求外部字体、脚本或图表服务。

本机可选依赖位于项目 `.tmp/ensemble_report_deps`，脚本会在存在时优先使用。原课程课件、工作单、数据和演示脚本均未改动；报告驱动程序调用原模型定义，但使用自身输出目录，避免原 `main()` 的父目录索引问题。

## 主要结果文件

每个数据目录 `results/wdbc`、`results/ctg` 中：

| 文件 | 内容 |
|---|---|
| `model-comparison.csv` | 固定验证集七模型指标与混淆矩阵计数 |
| `cv-folds.csv`、`cross-validation.csv` | 逐折指标与共享五折汇总 |
| `tree-depth.csv`、`bootstrap-roots.csv` | 深度实验及 10 次根节点变化 |
| `tree-count-curve.csv` | 树数、验证 AUC 与 OOB accuracy |
| `prediction-stability-row.csv` | 30 次共享行重训的 SD 与翻转率 |
| `prediction-stability-recording.csv` | CTG 整录音重训结果，仅 CTG 提供 |
| `stability-*.npz` | 逐次、逐个验证样本的概率，用于核查稳定性 |
| `boosting-curves.csv` | 三种学习率各 500 个阶段的训练／验证结果 |
| `adaboost-weight-trace.csv` | 前 10 轮错分样本权重占比变化 |
| `feature-importance.csv`、`training-correlation.csv` | 重要性与训练相关矩阵 |
| `matched-feature-randomization.csv` | 同一 RF 实现改变候选特征策略 |
| `conditional-validation-bootstrap.csv` | 固定 RF/LR 验证预测的配对条件抽样结果 |
| `ctg-row-cv-diagnostic.csv` | CTG 忽略分组的诊断对照，仅 CTG 提供 |

`results/manifest.json` 记录输入 SHA-256、软件版本与实验设置；`review/quality-check.json` 记录结构与结果一致性检查。`report.template.md` 的叙述围绕本次结果编写，若将来更换数据、参数或软件使结论变化，需同步审阅文字，不能只更新表格。
