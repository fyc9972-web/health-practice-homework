"""Build a two-page journal-style layout proof from course concepts and CSV audit."""
from pathlib import Path
import csv
import hashlib
import html as html_module
import json
import os
import re
import subprocess

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "journal-style-sample"
ASSETS = OUT / "figures"
ASSETS.mkdir(parents=True, exist_ok=True)
SONG = FontProperties(fname="C:/Windows/Fonts/simsun.ttc")
HEI = FontProperties(fname="C:/Windows/Fonts/simhei.ttf")
NAVY, TEAL, GRAY = "#24445C", "#568C85", "#74808A"
plt.rcParams.update({
    "font.family": SONG.get_name(), "axes.unicode_minus": False,
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "axes.linewidth": .65,
    "svg.fonttype": "path", "pdf.fonttype": 42,
    "mathtext.fontset": "stix",
})

with (ROOT / "data/heart.csv").open(encoding="utf-8-sig", newline="") as f:
    records = list(csv.DictReader(f))
features = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
            "thalach", "exang", "oldpeak", "slope", "ca", "thal"]
missing_tokens = {"", "NA", "NaN", "?", "nan"}
missing = {c: sum(r[c].strip() in missing_tokens for r in records) for c in features}
positive = sum(int(r["heart_disease_present"]) for r in records)
negative = len(records) - positive
assert (len(records), positive, negative) == (270, 120, 150)
metadata = {
    "source": "data/heart.csv", "audit_date": "2026-11-03",
    "source_sha256": hashlib.sha256((ROOT / "data/heart.csv").read_bytes()).hexdigest(),
    "n": len(records), "positive": positive, "negative": negative,
    "missing_by_feature": missing, "mode": "layout proof; file audit and simulated mechanisms",
}
(OUT / "sample-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def prettify(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(width=.65, length=3)
    ax.grid(axis="y", color="#E5E9EB", linewidth=.5, zorder=0)
    ax.set_axisbelow(True)


def save_figure(fig, name):
    for extension in ("svg", "png"):
        fig.savefig(ASSETS / f"{name}.{extension}", dpi=260, facecolor="white")
    plt.close(fig)


# Figure 1: simulated mechanisms, explicitly distinct from fitted model results.
fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.0))
fig.subplots_adjust(left=.075, right=.985, top=.85, bottom=.24, wspace=.32)
x = np.linspace(-2.5, 4.5, 500)
f0 = np.exp(-x*x/2) / np.sqrt(2*np.pi)
f1 = np.exp(-(x-2)**2/2) / np.sqrt(2*np.pi)
a, b = axes
a.plot(x, f0, c=TEAL, lw=1.6, label="未患病组")
a.plot(x, f1, c=NAVY, lw=1.6, label="患病组")
a.fill_between(x, f0, color=TEAL, alpha=.08)
a.fill_between(x, f1, color=NAVY, alpha=.06)
a.axvline(1, c=GRAY, ls="--", lw=.7)
a.set(xlim=(-2.5, 4.5), ylim=(0, .46), xlabel="检查指标 x", ylabel="类条件密度")
a.set_xticks([-2, 0, 1, 2, 4])
a.set_yticks([0, .2, .4])
a.legend(frameon=False, fontsize=7, loc="upper right", handlelength=1.6)
a.set_title("a  两类中心不同，方差相同", fontproperties=HEI, fontsize=9, loc="left", pad=8)
b.plot(x, 1/(1+np.exp(-(2*x-2))), color=NAVY, lw=1.8)
b.axvline(1, c=GRAY, ls="--", lw=.7)
b.axhline(.5, c=GRAY, ls=":", lw=.7)
b.scatter([1], [.5], s=17, color=TEAL, zorder=4)
b.text(1.15, .39, "x = 1，p = 0.5", fontsize=7, color=GRAY)
b.set(xlim=(-2.5, 4.5), ylim=(-.02, 1.02), xlabel="检查指标 x", ylabel="患病后验概率")
b.set_xticks([-2, 0, 1, 2, 4])
b.set_yticks([0, .5, 1], ["0", "0.5", "1.0"])
b.set_title("b  同一设定得到线性评分与概率", fontproperties=HEI, fontsize=9, loc="left", pad=8)
for ax in axes:
    prettify(ax)
save_figure(fig, "figure-1-mechanism")

# Figure 2: direct descriptive audit of the current project CSV.
fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.18), gridspec_kw={"width_ratios": [1, 1.35]})
fig.subplots_adjust(left=.095, right=.955, top=.83, bottom=.22, wspace=.43)
a, b = axes
a.barh([1, 0], [negative, positive], color=["#B5C2C9", NAVY], height=.42)
a.set_yticks([1, 0], ["未患病", "患病"])
a.set(xlim=(0, 185), xlabel="记录数")
a.set_xticks([0, 50, 100, 150])
for y, n in [(1, negative), (0, positive)]:
    a.text(n+3, y, f"{n} ({n/len(records):.1%})", va="center", fontsize=7)
a.set_title("a  结局构成（n = 270）", fontproperties=HEI, fontsize=9, loc="left", pad=8)
top_missing = sorted(missing.items(), key=lambda pair: pair[1], reverse=True)[:6]
ys = np.arange(len(top_missing))
b.barh(ys, [n for _, n in top_missing], color=TEAL, height=.55)
b.set_yticks(ys, [name for name, _ in top_missing])
b.invert_yaxis()
b.set(xlim=(0, 225), xlabel="缺失记录数")
b.set_xticks([0, 50, 100, 150, 200])
for y, (_, n) in zip(ys, top_missing):
    b.text(n+3, y, f"{n} ({n/len(records):.1%})", va="center", fontsize=6.8)
b.set_title("b  缺失数最高的六个输入变量", fontproperties=HEI, fontsize=9, loc="left", pad=8)
for ax in axes:
    prettify(ax)
    ax.grid(False, axis="y")
    ax.grid(axis="x", color="#E5E9EB", linewidth=.5, zorder=0)
save_figure(fig, "figure-2-audit")

CONTENT = {
    "title": "线性分类模型的概率建模与决策边界",
    "subtitle": "以心脏病教学数据为例比较 Logistic 回归与线性判别分析",
    "abstract": "Logistic 回归与线性判别分析（LDA）均可产生线性分类边界，但概率来源与估计目标不同。本简报从线性评分、类条件分布和错误代价建立比较框架，并审计当前心脏病教学文件。270 条记录中，阳性 120 条、阴性 150 条；部分输入存在较高缺失比例。方法选择应综合编码维度、假设压力、概率质量及验证稳定性，避免将内部排序优势直接解释为临床效用。本样稿展示原理图、原文件审计与验证方案。",
    "intro": "简单模型的价值在于把输入、概率与行动之间的关系明确化。对疾病二分类，研究者既要识别阳性个体，也要判断概率是否可信，以及漏诊与误报是否符合任务代价。线性边界因此是建模结构，模型选择仍需结合验证证据。[1,2]",
    "linear": "评分 z 由截距与特征加权和组成。固定评分门槛在二维特征空间对应直线。Logistic 将评分经 sigmoid 转成概率；其线性假设作用于 log-odds。训练通过条件交叉熵估计系数，L2 惩罚可限制过大的系数。",
    "lda": "LDA 先估计各类均值、共享协方差和先验，再用 Bayes 规则计算后验。共享协方差允许类内相关；两类对数密度的共同二次项相减抵消，留下线性判别分数。若允许各类使用不同协方差，则通常形成 QDA 的二次边界。",
    "contrast": "两类方法可得到相同形式的 sigmoid 评分，但 Logistic 直接拟合条件概率，LDA 则从生成分布推导评分。图 1 用一维设定展示这种联系。对二元或 one-hot 输入，高斯假设属于近似，应检查其预测和校准后果。",
    "fig1": "图 1 | 从类条件分布到后验概率。设两类均值为 0、2，共同方差为 1，先验各半；分数差为 2x−2，因此 p＝sigmoid(2x−2)，默认边界为 x＝1。曲线为机制示意，不代表教学数据的拟合结果。",
    "deck": "围绕当前 CSV 的描述性审计，建立后续模型比较的证据边界。",
    "fig2": "图 2 | 当前教学文件的直接审计。左：结局分布；右：仅展示缺失记录数最高的六个输入，百分比分母均为 270。统计来自 data/heart.csv，未据此选择模型或阈值。",
    "methods": "按主标签分层划分 80% 开发集与 20% 锁定测试集，固定随机种子 2026。开发集交叉验证中，在每个训练折拟合数值填补、标准化、分类填补、one-hot 编码与模型；验证折仅转换并预测。模型与阈值在开发数据中选择，完整方案冻结后评价测试集。[2]",
    "compare": "患病比例基线检查个人特征增益，Gaussian NB 提供类内条件独立参照。Logistic 与 LDA 则比较条件概率和生成分布两条路线。编码后维度决定参数计数；全水平指示列的冗余须单独处理。",
    "discussion": "本次审计确认：样本构成为 120／150，ca 与 thal 分别缺失 181、151 条。课程文字中的“无缺失”与当前文件不一致，应以输入版本核对和训练折内处理为前提。高比例缺失会增加解释压力；填补可使算法运行，但不等同于恢复真实观测。",
    "evaluation": "评价应分别报告排序（ROC-AUC、AP）、概率质量（Brier、log loss、校准）和阈值错误。代价 5×FN＋FP 连接漏诊与误报；AUC 较高并不自动意味着代价更低。Bootstrap 表达抽样不确定性，系数稳定性与预测稳定性需要分别检查。",
    "boundary": "OR 解释需明确单位、参照与其他变量固定。模型系数为条件关联；内部评价不能自动支持因果效应、跨医院泛化或临床部署。完整分析应使主张、证据、推理与适用边界一致。",
    "data_note": "数据与图示：图 1 为设定分布的机制图；图 2 为项目当前 CSV 的基础审计。模型性能比较需在统一开发协议下另行报告。",
}

css = r"""
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html,body { margin:0; padding:0; background:#fff; color:#171B20; }
body { font-family:'SimSun','Times New Roman',serif; font-size:10pt; }
.page { width:210mm; height:297mm; padding:14mm 17mm 17mm; position:relative;
        overflow:hidden; break-after:page; background:#fff; }
.page:last-child { break-after:auto; }
.running { display:flex; justify-content:space-between; font-size:7.1pt; color:#516372;
           letter-spacing:.08em; border-bottom:.35pt solid #A6B3BC; padding-bottom:3mm; }
h1 { font-family:'SimHei',Arial,sans-serif; font-size:19pt; font-weight:400;
     line-height:1.34; margin:6mm 0 2mm; letter-spacing:.01em; }
.subtitle { font-size:10.2pt; line-height:1.5; margin:0 0 2mm; color:#344957; }
.meta { font-size:7.6pt; color:#65717A; margin:0; line-height:1.5; }
.abstract { border-top:1pt solid #24445C; border-bottom:.35pt solid #A6B3BC;
            padding:3mm 0 2.5mm; margin-top:4mm; font-size:9pt; line-height:1.6; }
.abstract strong { font-family:'SimHei',Arial,sans-serif; font-weight:400; }
.keywords { font-size:7.8pt; margin:2mm 0 0; color:#4F5F6C; line-height:1.5; }
.columns { display:grid; grid-template-columns:1fr 1fr; gap:7mm; margin-top:4mm; }
h2 { font-family:'SimHei',Arial,sans-serif; font-weight:400; font-size:10.8pt;
     margin:0 0 1.6mm; color:#1F3444; line-height:1.4; }
h3 { font-family:'SimHei',Arial,sans-serif; font-weight:400; font-size:9.6pt;
     margin:3mm 0 1mm; line-height:1.4; }
p { margin:0 0 2mm; line-height:1.65; text-align:justify; }
.equation { font-family:'Times New Roman','SimSun',serif; font-size:10.3pt;
            text-align:center; margin:2.1mm 0; line-height:1.5; white-space:nowrap; }
.eqnumber { color:#7C858C; font-size:7pt; margin-left:3mm; }
figure { margin:3.5mm 0 0; }
figure img { display:block; width:100%; height:auto; }
figcaption { font-size:7.7pt; line-height:1.52; color:#44515D; margin-top:1mm; text-align:justify; }
.p2 h1 { font-size:16.5pt; margin-top:5mm; }
.p2 .deck { font-size:9pt; color:#5C6972; line-height:1.55; margin:1.5mm 0 0; }
.p2 figure { margin-top:4mm; }
.p2 .columns { margin-top:4mm; }
.compact p { font-size:9.6pt; line-height:1.65; }
.compact h2 { font-size:10.3pt; }
table { border-collapse:collapse; width:100%; font-size:7.8pt; line-height:1.55; margin:2mm 0; }
th { border-top:.8pt solid #233C4D; border-bottom:.4pt solid #81909B;
     font-family:'SimHei',Arial,sans-serif; font-weight:400; text-align:left; padding:1.3mm 1mm; }
td { padding:1.2mm 1mm; vertical-align:top; }
tbody tr:last-child td { border-bottom:.8pt solid #233C4D; }
.note { font-size:7.3pt!important; color:#62707A; line-height:1.5!important; }
.endmatter { margin-top:4mm; padding-top:2mm; border-top:.4pt solid #A6B3BC;
             font-size:7.3pt; line-height:1.55; color:#586570; }
.endmatter p { margin-bottom:1mm; line-height:1.55; }
.folio { position:absolute; bottom:9mm; left:17mm; right:17mm; display:flex;
         justify-content:space-between; border-top:.35pt solid #A6B3BC; padding-top:2mm;
         font-family:'Times New Roman','SimSun',serif; color:#66747D; font-size:7pt; }
@media screen { body { width:210mm; } }
@media print { .page { -webkit-print-color-adjust:exact; print-color-adjust:exact; } }
"""

c = CONTENT
html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>线性模型研究简报｜双栏版式样稿</title><style>{css}</style></head><body>
<article class="page p1">
<div class="running"><span>生物医学数据科学 · 方法简报</span><span>双栏版式预览 · 2026</span></div>
<h1>{c['title']}</h1><p class="subtitle">{c['subtitle']}</p>
<p class="meta">知识框架与实践审计　|　排版样稿 v0.1　|　2026 年 11 月</p>
<div class="abstract"><strong>摘要　</strong>{c['abstract']}</div>
<p class="keywords">关键词：Logistic 回归；线性判别分析；概率校准；无泄漏验证；错误代价</p>
<div class="columns">
<section><h2>引言</h2><p>{c['intro']}</p><h3>线性评分与条件概率</h3><p>{c['linear']}</p>
<div class="equation">z = β₀ + xᵀβ<span class="eqnumber">(1)</span></div>
<div class="equation">p = 1 / [1 + exp(−z)]<span class="eqnumber">(2)</span></div></section>
<section><h2>从类条件分布到后验</h2><p>{c['lda']}</p>
<div class="equation">X | Y = k ∼ N(μₖ, Σ)<span class="eqnumber">(3)</span></div>
<p>{c['contrast']}</p>
<p class="note">模型对象、概率来源与估计目标应一起解释；线性形式本身不能决定方法优劣。</p></section>
</div>
<figure><img src="figures/figure-1-mechanism.svg" alt="相同方差的高斯分布及其后验概率"><figcaption>{c['fig1']}</figcaption></figure>
<div class="folio"><span>LINEAR CLASSIFICATION · METHODS</span><span>01</span></div>
</article>
<article class="page p2">
<div class="running"><span>线性模型：从假设到证据</span><span>数据审计与讨论</span></div>
<h1>数据审计与评价框架</h1><p class="deck">{c['deck']}</p>
<figure><img src="figures/figure-2-audit.svg" alt="当前教学数据的类别构成和缺失分布"><figcaption>{c['fig2']}</figcaption></figure>
<div class="columns compact">
<section><h2>实践设计</h2><p>{c['methods']}</p>
<h3>比较对象与估计负担</h3><p>{c['compare']}</p>
<table><thead><tr><th>模型</th><th>主要建模对象</th></tr></thead><tbody>
<tr><td>Logistic</td><td>条件概率与线性 logit</td></tr>
<tr><td>LDA</td><td>类条件高斯与共享协方差</td></tr>
<tr><td>Gaussian NB</td><td>类内条件独立的各特征分布</td></tr>
</tbody></table><p class="note">参考编码后维度为 q：Logistic 的系数计数为 q＋1；LDA 还需估计共享协方差。</p></section>
<section><h2>审计发现与讨论</h2><p>{c['discussion']}</p><p>{c['evaluation']}</p>
<h3>解释边界</h3><p>{c['boundary']}</p></section>
</div>
<div class="endmatter"><p><b>数据与图示说明　</b>{c['data_note']}</p>
<p><b>资料来源　</b>[1]《线性模型、LDA 与 Logistic Regression》课程课件，第 4–13 页。<br>
[2] student-worksheet.md：建模目标、实验协议与评价框架。<br>
[3] data/heart.csv：当前项目教学文件，审计日期 2026-11-03。</p></div>
<div class="folio"><span>COURSE RESEARCH BRIEF · LAYOUT PROOF</span><span>02</span></div>
</article><script>
window.addEventListener('load', async () => {{
  await document.fonts.ready;
  const checks = [...document.querySelectorAll('.page')].map((page, index) => {{
    const last = page.querySelector('.endmatter') || page.querySelector('figure');
    const footer = page.querySelector('.folio');
    return {{page:index+1, clearance_px:Math.round(footer.getBoundingClientRect().top-last.getBoundingClientRect().bottom)}};
  }});
  document.body.dataset.layoutCheck = JSON.stringify(checks);
}});
</script></body></html>"""
(OUT / "report-preview.html").write_text(html, encoding="utf-8")


def make_word():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.5), Cm(1.7)
    sec.left_margin = sec.right_margin = Cm(1.7)
    sec.header_distance = Cm(.7)
    sec.footer_distance = Cm(.8)
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Caption"]:
        st = doc.styles[name]
        st.font.name = "Times New Roman"
        st.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal = doc.styles["Normal"]
    normal.font.size = Pt(9.8)
    normal.paragraph_format.line_spacing = 1.45
    normal.paragraph_format.space_after = Pt(5)
    for name, size in [("Title", 19), ("Heading 1", 11), ("Heading 2", 10)]:
        st = doc.styles[name]
        st.font.size = Pt(size)
        st.font.bold = False
        st.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "黑体")
        st.font.color.rgb = RGBColor.from_string("24445C")
        st.paragraph_format.space_before = Pt(7)
        st.paragraph_format.space_after = Pt(4)
    doc.styles["Caption"].font.size = Pt(7.5)
    doc.styles["Caption"].paragraph_format.line_spacing = 1.2
    doc.styles["Caption"].paragraph_format.space_after = Pt(5)
    hp = sec.header.paragraphs[0]
    hp.text = "生物医学数据科学 · 方法简报                                      双栏版式样稿"
    hp.style = doc.styles["Caption"]

    def p(container, text, style=None):
        para = container.add_paragraph(text, style)
        para.paragraph_format.widow_control = True
        return para

    def cols(left_blocks, right_blocks):
        table = doc.add_table(rows=1, cols=3)
        table.autofit = False
        for cell, width in zip(table.rows[0].cells, [8.45, .7, 8.45]):
            cell.width = Cm(width)
            tcpr = cell._tc.get_or_add_tcPr()
            mar = OxmlElement("w:tcMar")
            for edge in ["top", "left", "bottom", "right"]:
                elem = OxmlElement("w:" + edge)
                elem.set(qn("w:w"), "0")
                elem.set(qn("w:type"), "dxa")
                mar.append(elem)
            tcpr.append(mar)
        for cell, blocks in [(table.cell(0, 0), left_blocks), (table.cell(0, 2), right_blocks)]:
            cell._element.remove(cell.paragraphs[0]._element)
            for kind, text in blocks:
                p(cell, text, {"h": "Heading 1", "sub": "Heading 2", "note": "Caption"}.get(kind))
        return table

    p(doc, c["title"], "Title")
    p(doc, c["subtitle"], "Subtitle")
    p(doc, "知识框架与实践审计  |  排版样稿 v0.1  |  2026 年 11 月", "Caption")
    p(doc, "摘要  " + c["abstract"])
    p(doc, "关键词：Logistic 回归；线性判别分析；概率校准；无泄漏验证；错误代价", "Caption")
    cols([
        ("h", "引言"), ("p", c["intro"]), ("sub", "线性评分与条件概率"),
        ("p", c["linear"]), ("p", "z = β₀ + xᵀβ                         (1)"),
        ("p", "p = 1 / [1 + exp(−z)]             (2)"),
    ], [
        ("h", "从类条件分布到后验"), ("p", c["lda"]),
        ("p", "X | Y = k ∼ N(μₖ, Σ)              (3)"), ("p", c["contrast"]),
    ])
    doc.add_picture(str(ASSETS / "figure-1-mechanism.png"), width=Cm(17.6))
    p(doc, c["fig1"], "Caption")
    doc.add_page_break()
    p(doc, "数据审计与评价框架", "Title")
    p(doc, c["deck"])
    doc.add_picture(str(ASSETS / "figure-2-audit.png"), width=Cm(17.6))
    p(doc, c["fig2"], "Caption")
    cols([
        ("h", "实践设计"), ("p", c["methods"]),
        ("sub", "比较对象与估计负担"), ("p", c["compare"]),
        ("note", "Logistic：条件概率与线性 logit。"),
        ("note", "LDA：类条件高斯与共享协方差。"),
        ("note", "Gaussian NB：类内条件独立的各特征分布。"),
    ], [
        ("h", "审计发现与讨论"), ("p", c["discussion"]), ("p", c["evaluation"]),
        ("sub", "解释边界"), ("p", c["boundary"]),
    ])
    p(doc, "数据与图示说明  " + c["data_note"], "Caption")
    p(doc, "资料来源  [1] 课程课件，第 4–13 页。[2] student-worksheet.md。[3] data/heart.csv，审计日期 2026-11-03。", "Caption")
    footer = sec.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run("版式样稿  |  ")
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer._p.append(fld)
    for run in footer.runs:
        run.font.size = Pt(7)
    doc.core_properties.title = c["title"]
    doc.core_properties.subject = "双栏期刊风格版式样稿；机制图与教学数据审计"
    doc.save(OUT / "report-preview.docx")


make_word()

# Render the local HTML using the installed browser, with all browser state in the workspace.
chrome = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
profile = ROOT / ".tmp" / "journal-sample-browser"
profile.mkdir(parents=True, exist_ok=True)
flags = [str(chrome), "--headless", "--disable-gpu", "--disable-background-networking",
         "--disable-extensions", "--disable-sync", "--no-first-run", "--no-default-browser-check",
         f"--user-data-dir={profile}", "--virtual-time-budget=2500", "--no-pdf-header-footer"]
uri = (OUT / "report-preview.html").resolve().as_uri()
for extra in [
    [f"--print-to-pdf={OUT / 'report-preview.pdf'}"],
    [f"--screenshot={OUT / 'spread-preview.png'}", "--window-size=794,2246", "--force-device-scale-factor=1", "--hide-scrollbars"],
    ["--dump-dom"],
]:
    result = subprocess.run(flags + extra + [uri], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    print("Browser exit:", result.returncode)
    if result.returncode:
        print(result.stderr[-1800:])
    if "--dump-dom" in extra and result.returncode == 0:
        match = re.search(r'data-layout-check="([^"]+)"', result.stdout)
        if match:
            checks = json.loads(html_module.unescape(match.group(1)))
            print("Content/footer clearances:", checks)
            assert all(check["clearance_px"] > 12 for check in checks), checks

spread_path = OUT / "spread-preview.png"
if spread_path.exists():
    im = Image.open(spread_path)
    half = 1123
    im.crop((0, 0, 794, half)).save(OUT / "page-1.png")
    im.crop((0, half, 794, min(2246, im.height))).save(OUT / "page-2.png")
    # Compact side-by-side contact sheet, independent of browser UI.
    sheet = Image.new("RGB", (794*2+36, half+24), "#E4E8EB")
    sheet.paste(Image.open(OUT / "page-1.png"), (12, 12))
    sheet.paste(Image.open(OUT / "page-2.png"), (818, 12))
    sheet.save(OUT / "two-page-preview.png")

pdf_path = OUT / "report-preview.pdf"
if pdf_path.exists():
    raw = pdf_path.read_bytes()
    print("PDF page objects:", len(re.findall(rb"/Type\s*/Page\b", raw)))
print("Outputs:")
for path in sorted(OUT.iterdir()):
    if path.is_file():
        print(path.name, path.stat().st_size)
