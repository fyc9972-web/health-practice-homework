# 集成学习课堂实践报告

本版参照用户提供的 `lesson_8/outputs/svm-report/SVMlesson_8.pdf` 重写并排版。保留 WDBC、CTG 两套数据，依据 `slides/ensemble-pbl.pptx` 与 `student-worksheet.md` 的 A—H 实践内容组织论述。

## 阅读与修改

- `Ensemblelesson_9.pdf`：14 页固定版式，适合阅读与课堂展示。
- `集成学习_课堂实践完整报告.docx`：可修改正文、表格及原生 Word 公式。
- `index.html`：自包含网页，图形已嵌入，可离线阅读。
- `集成学习_课堂实践完整报告_文字稿.md`：完整文字、结果表与线性公式。
- `article.source.md`：排版源稿，包含双栏、公式及结果表占位符。
- `figures/`：12 幅图的 SVG 与 PNG 原图。

正文按“概念定义—机制与公式—实验对照—结果解释”展开。第 2—4 节建立单树、投票和方差基础，第 5—9 节解释抽样集成、特征随机化和顺序提升，第 10—13 节讨论解释、评价及选型，第 14 节记录方法与参考文献。各公式附近说明符号，公式下方另列注释。

## 实验与复现

本次修订使用已完成实验的逐折结果、逐阶段损失、预测及重抽样记录，未重新挑选模型。只使用学生训练、验证输入；未读取锁定测试标签。

实验文件位于项目根目录下的 `ensemble-classroom-report/results/`，输入哈希见其中的 `manifest.json`。相应脚本位于 `ensemble-classroom-report/scripts/`：

1. `run_experiments.py`：生成实验结果；已有结果，无须为阅读报告重新运行。
2. `revise_academic_figures.py`：从已保存结果绘制本版图形。
3. `build_academic_revision.py`：构建 HTML、Word 和 Markdown；参数 `--check-layout` 检查分页，`--pdf` 导出 PDF。
4. `check_academic_revision.py`：核对保存的预测与报告指标、公式、图表及 PDF 结构，不重新拟合。

本机脚本使用 `.tmp/ensemble_report_deps/` 中的依赖及本地 Chrome。质量核查结果见 `review/quality-check.json`，逐页预览与文本提取亦保存在 `review/` 中。
