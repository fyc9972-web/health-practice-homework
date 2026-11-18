# 本次学习与提交材料

**当前提交版：论文式实验报告《基于 Bernoulli 朴素贝叶斯的膀胱炎症预测实验》。**

按最新要求重新组织为摘要、引言、数据与方法、实验结果、讨论、结论和参考文献，不再按工作单逐题排列。覆盖课程七项知识重点，包含两幅配套Notebook原图、六张数据表、手算过程及结果分析。不填写姓名、学号及日期，AI辅助说明集中放在文末。

| 当前报告 | 链接 |
|---|---|
| 可编辑Word | [naive-bayes-paper.docx](naive-bayes-paper.docx) |
| 打印PDF（7页） | [naive-bayes-paper.pdf](naive-bayes-paper.pdf) |
| 浏览版 | [naive-bayes-paper.html](naive-bayes-paper.html) |
| Markdown源文件 | [naive-bayes-paper.md](naive-bayes-paper.md) |

已检查原Notebook未改动、两幅图片与Notebook输出字节一致、手算及实验结果、附件链接与PDF分页。Word、PDF和HTML已嵌入图片，可以单独打开。课堂操作说明与纯知识清单继续分开保留。

## 既有学习材料与旧版作业

下列工作单和旧图文报告保留供对照；当前提交请使用上方论文式报告。

先完成报告与操作内容，再整理知识清单。按要求不填写姓名、学号及日期；初始预想、反思和应用例子注明AI辅助拟答。本人尚未亲自核验或确认掌握，材料没有代为勾选能力自查。

| 材料 | 可编辑Word | 打印PDF | 浏览版 | Markdown |
|---|---|---|---|---|
| 旧版：逐题填写的作业工作单 | [DOCX](student-worksheet.docx) | [PDF](student-worksheet.pdf) | [HTML](student-worksheet.html) | [MD](student-worksheet.md) |
| 旧版：图文实验报告 | [DOCX](experiment-report.docx) | [PDF](experiment-report.pdf) | [HTML](experiment-report.html) | [MD](experiment-report.md) |
| 课堂操作说明与实际结果解读 | [DOCX](operation-guide.docx) | [PDF](classroom-operations.pdf) | [HTML](operation-guide.html) | [MD](operation-guide.md) |
| 纯知识清单、概念讲解与自测 | [DOCX](knowledge-guide.docx) | [PDF](knowledge-concepts.pdf) | [HTML](knowledge-guide.html) | [MD](knowledge-guide.md) |

原路径的 [student-worksheet.md](student-worksheet.md) 已按空白模板逐题填写，保留原题顺序。正文采用简短的学生作答表达，列出计算过程，AI帮助说明统一放在文末。图文实验报告单独保留。[原空白工作单备份](reference/student-worksheet.blank.md)可供对照。

## 实验附件

- [已运行Notebook](naive-bayes-lab-completed.ipynb)：A、A2、B、C、冻结、D均实际运行，未运行选做E。保留了 [原Notebook](../notebooks/naive-bayes-lab.ipynb)。
- [固定方案](fixed-protocol.json)：目标、输入、α、训练ID、阈值和不合并验证集重训的设置。
- [Bayes手算明细](bayes-handcheck.csv)、[完整验证阈值表](validation-thresholds.csv)、[机器可读数值证据](experiment-evidence.json)。证据中的null表示未定义指标或无记录空箱。
- [ROC/PR原图](images/B-ranking.png)、[可靠性原图](images/C-reliability.png)：直接提取自Notebook运行输出，已检查图片字节一致。

提交工作单或图文报告、带输出Notebook及报告7.4综合说明即可构成核心材料；固定方案与CSV可作为核验附件。操作说明和知识清单供学习，不必当作实验结果提交。Markdown需要保留图片相对路径；Word、HTML和PDF已嵌入图片。

知识清单仅包含七项重点的定义、联系、教学小例子和概念自测，不包含课堂文件、代码、运行步骤或实测成绩。课堂中的具体操作、计算核对和结果解读集中放在操作说明中。

新版PDF名称为knowledge-concepts.pdf和classroom-operations.pdf。knowledge-guide.pdf为先前版本，被占用而未覆盖；operation-guide.pdf也是先前导出版本，请以上表链接为准。Word、HTML和Markdown已在原路径更新。

已检查：原Notebook未被改动；核心执行无报错；冻结单元先于D执行；图表来自指定Notebook；手算与程序后验一致；附件相对链接有效。PDF为独立排版导出，和Word的分页可能不同。

测试结果24/24全对、log loss0.074492；测试24条症状组合全在train出现，不能把内部成绩当作跨医院临床证据。本次实际环境版本见报告及操作说明，部分低于项目建议依赖范围，不声称已在全部建议版本复测。

学习建议：先打开知识清单的总表及第一部分，弄清模型、输入和输出的含义；有不懂的概念直接按章节问。需要了解课堂中具体怎样做时，再查看操作说明。理解并能上台讲解后，再回看报告修改为自己的表达。
