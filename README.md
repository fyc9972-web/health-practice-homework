# 健康实践课程作业

本仓库按课次整理 lesson_2 至 lesson_10 的课程重点、已填写工作单或报告，以及配套数据、PPT 和代码。课次以文件夹编号为准。

## 课程导航

| 课程 | 课程重点 | 作业 / 报告入口 |
| --- | --- | --- |
| [lesson_2：理解数据](lesson_2/) | [课堂重点](lesson_2/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [已填写 worksheet](lesson_2/results/v2_pbl-data-types-student-worksheet_done.docx) |
| [lesson_3：高维数据与降维](lesson_3/) | [课堂重点](lesson_3/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [已填写 worksheet](lesson_3/results/%E9%AB%98%E7%BB%B4%E6%95%B0%E6%8D%AE%E4%B8%8E%E9%99%8D%E7%BB%B4-worksheet%E5%AE%8C%E6%88%90%E7%89%88.docx) |
| [lesson_4：统计方法与假设检验](lesson_4/) | [课堂重点](lesson_4/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [已有汇报与方法整理](lesson_4/results/%E6%B1%87%E6%8A%A5.md) |
| [lesson_5：多重检验](lesson_5/) | [课堂重点](lesson_5/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [任务 3、4 完成稿](lesson_5/results/student-worksheet-tasks-3-4-completed.md) |
| [lesson_6：朴素贝叶斯](lesson_6/) | [课堂重点](lesson_6/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [朴素贝叶斯论文式报告](lesson_6/results/naive-bayes-paper.docx) |
| [lesson_7：线性模型](lesson_7/) | [课堂重点](lesson_7/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [线性模型课程报告](lesson_7/results/journal-formal/%E7%BA%BF%E6%80%A7%E5%88%86%E7%B1%BB%E6%A8%A1%E5%9E%8B%E8%AF%BE%E7%A8%8B%E6%8A%A5%E5%91%8A_%E5%90%8C%E7%89%88%E5%BC%8FWord%E5%9B%BE%E7%89%88.docx) |
| [lesson_8：SVM](lesson_8/) | [课堂重点](lesson_8/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [SVM 课堂实践报告](lesson_8/results/svm-report/SVM_%E8%AF%BE%E5%A0%82%E5%AE%9E%E8%B7%B5%E5%AE%8C%E6%95%B4%E6%8A%A5%E5%91%8A.docx) |
| [lesson_9：集成学习](lesson_9/) | [课堂重点](lesson_9/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [集成学习课堂实践报告](lesson_9/results/ensemble-report/%E9%9B%86%E6%88%90%E5%AD%A6%E4%B9%A0_%E8%AF%BE%E5%A0%82%E5%AE%9E%E8%B7%B5%E5%AE%8C%E6%95%B4%E6%8A%A5%E5%91%8A.docx) |
| [lesson_10：Git 与 GitHub](lesson_10/) | [课堂重点](lesson_10/results/%E8%AF%BE%E5%A0%82%E9%87%8D%E7%82%B9.md) | [仓库管理实践记录](lesson_10/results/%E4%BB%93%E5%BA%93%E5%AE%9E%E8%B7%B5%E8%AE%B0%E5%BD%95.md) |

各课 README 标明 PDF 位置与具体材料状态。第 4 课目前是汇报与方法整理，第 5 课已有任务 3、4 完成稿。

## AI 学习过程记录

[AI 学习对话总结](AI%E5%AD%A6%E4%B9%A0%E5%AF%B9%E8%AF%9D%E6%80%BB%E7%BB%93.md)：选取第 4、6、7、8 课的真实概念问答，保留提问、时间、答复节选与学习逻辑。

## 目录约定

```text
health-practice-homework/
├── README.md
├── .gitignore
├── lesson_2/
│   ├── README.md
│   ├── results/       # 课堂重点、已填写工作单或报告
│   ├── slides/        # PPT
│   ├── assets/        # 原有课堂数据与资源
│   ├── notebook/      # 代码与实验
│   ├── scripts/
│   └── materials/    # 空白模板、说明和参考材料
├── lesson_3/
├── lesson_4/
├── lesson_5/
├── lesson_6/
├── lesson_7/
├── lesson_8/
├── lesson_9/
└── lesson_10/
```

其他课也以 results/ 作为成果入口；数据、代码和参考资料目录按各课实际内容保留。data/、assets/ 与 Notebook 之间的运行关系优先保持完整。

## 运行与复现

进入具体课程目录，先阅读该课 README 与 Notebook。提供 requirements.txt 的课程应在独立 Python 环境安装对应依赖，再按单元格顺序运行。已有报告和 PDF 可直接阅读，不必重跑构建脚本。

数据来源、字段、划分和使用边界见各课 data/README.md 或原有说明。保留第三方材料的署名与许可；本仓库不另行授予第三方材料使用权。

## 分课提交

每课核对完成后，明确选择该课路径并检查暂存内容：

```powershell
git add -- lesson_2
git diff --cached --stat
git commit -m "lesson_2：整理课堂重点、已填写工作单与配套材料"
```

其余课程换用相应目录和提交说明。提交使用实际操作时间；多条本地提交可以统一 push。

## 本地归档

放错位置的其他课程资料和整理前文本备份保存在本地 `.local_archive/`，通过 .gitignore 排除。整理前历史已完整备份于本地归档；当前历史重新建立，只按实际整理进度记录课程内容。
