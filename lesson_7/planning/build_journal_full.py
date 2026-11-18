"""Create an editable, six-part journal-style Word report with native columns/math."""
from pathlib import Path
import csv
import hashlib
import json
import shutil

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, Rectangle
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from journal_report_content import TITLE, SUBTITLE, ABSTRACT, KEYWORDS, PAGES, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "linear-models-report"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
DEST = OUT / "linear-models-report.docx"
SONG = FontProperties(fname="C:/Windows/Fonts/simsun.ttc")
HEI = FontProperties(fname="C:/Windows/Fonts/simhei.ttf")
NAVY, TEAL, GRAY = "#24445C", "#568C85", "#74808A"
plt.rcParams.update({"font.family": SONG.get_name(), "axes.unicode_minus": False,
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "axes.linewidth": .65,
    "mathtext.fontset": "stix", "svg.fonttype": "path"})

with (ROOT / "data/heart.csv").open(encoding="utf-8-sig", newline="") as f:
    data = list(csv.DictReader(f))
features = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"]
missing_tokens = {"", "NA", "NaN", "?", "nan"}
missing = {c: sum(r[c].strip() in missing_tokens for r in data) for c in features}
positive = sum(int(r["heart_disease_present"]) for r in data)
negative = len(data)-positive
any_missing = sum(any(r[c].strip() in missing_tokens for c in features) for r in data)
assert (len(data), positive, negative, any_missing, sum(missing.values())) == (270, 120, 150, 183, 557)
metadata = {"source": "data/heart.csv", "source_sha256": hashlib.sha256((ROOT/"data/heart.csv").read_bytes()).hexdigest(),
    "audit_date": "2026-11-03", "rows": len(data), "positive": positive, "negative": negative,
    "rows_with_missing": any_missing, "missing_by_feature": missing,
    "scope": "descriptive file audit; theoretical and controlled-simulation figures; no fitted performance results"}
(OUT / "report-provenance.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def clean(ax, grid=True):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(width=.65, length=3)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(axis="y", color="#E6EAED", linewidth=.5)


def save(fig, name):
    fig.savefig(FIG / name, dpi=320, facecolor="white")
    plt.close(fig)


def two_panels(height=1.85):
    fig, axes = plt.subplots(1, 2, figsize=(6.9, height))
    fig.subplots_adjust(left=.085, right=.975, top=.83, bottom=.25, wspace=.34)
    return fig, axes


# 1: logistic scale and OR transformation; formula illustration only.
fig, (a,b) = two_panels()
z = np.linspace(-4,4,400)
a.plot(z,1/(1+np.exp(-z)),c=NAVY,lw=1.7)
a.axhline(.5,c=GRAY,lw=.65,ls=":"); a.axvline(0,c=GRAY,lw=.65,ls="--")
a.scatter([0],[.5],s=18,c=TEAL,zorder=4)
a.set(xlabel="线性评分 z",ylabel="预测概率 p",xlim=(-4,4),ylim=(0,1))
a.set_yticks([0,.5,1]); a.set_xticks([-4,-2,0,2,4])
a.set_title("a  线性评分与 S 形概率",fontproperties=HEI,fontsize=9,loc="left",pad=7)
p = np.linspace(0,1,300)
b.plot(p,2*p/(1+p),c=NAVY,lw=1.7,label="OR = 2")
b.plot(p,p,c=GRAY,lw=.85,ls="--",label="概率不变")
b.scatter([.2],[1/3],s=20,c=TEAL,zorder=4)
b.annotate("20% → 33.3%",(.2,1/3),xytext=(.38,.25),fontsize=7,color=GRAY,
           arrowprops={"arrowstyle":"-","color":GRAY,"lw":.6})
b.set(xlabel="起始概率",ylabel="odds 翻倍后的概率",xlim=(0,1),ylim=(0,1))
b.set_xticks([0,.5,1]);b.set_yticks([0,.5,1]);b.legend(frameon=False,fontsize=7,loc="lower right")
b.set_title("b  OR 相同，概率增幅依赖起点",fontproperties=HEI,fontsize=9,loc="left",pad=7)
for ax in (a,b):clean(ax)
save(fig,"figure-1-logistic-or.png")

# 2: class distributions and posterior; same assumptions used in the manuscript.
fig, (a,b) = two_panels()
x=np.linspace(-2.5,4.5,400)
f0=np.exp(-x*x/2)/np.sqrt(2*np.pi);f1=np.exp(-(x-2)**2/2)/np.sqrt(2*np.pi)
a.plot(x,f0,c=TEAL,lw=1.6,label="未患病组");a.plot(x,f1,c=NAVY,lw=1.6,label="患病组")
a.axvline(1,c=GRAY,lw=.7,ls="--")
a.set(xlabel="检查指标 x",ylabel="类条件密度",xlim=(-2.5,4.5),ylim=(0,.46))
a.set_xticks([-2,0,1,2,4]);a.set_yticks([0,.2,.4]);a.legend(frameon=False,fontsize=7)
a.set_title("a  两类高斯密度",fontproperties=HEI,fontsize=9,loc="left",pad=7)
b.plot(x,f1/(f0+f1),c=NAVY,lw=1.7)
b.axvline(1,c=GRAY,lw=.7,ls="--");b.axhline(.5,c=GRAY,lw=.7,ls=":")
b.scatter([1],[.5],c=TEAL,s=18,zorder=4)
b.set(xlabel="检查指标 x",ylabel="患病后验概率",xlim=(-2.5,4.5),ylim=(0,1))
b.set_xticks([-2,0,1,2,4]);b.set_yticks([0,.5,1])
b.set_title("b  Bayes 归一化后的概率",fontproperties=HEI,fontsize=9,loc="left",pad=7)
for ax in (a,b):clean(ax)
save(fig,"figure-2-lda-posterior.png")

# 3: current-file descriptive audit, including all nine missing-input columns.
fig, axes = plt.subplots(1,2,figsize=(6.9,2.2),gridspec_kw={"width_ratios":[1,1.35]})
fig.subplots_adjust(left=.095,right=.965,top=.84,bottom=.22,wspace=.44)
a,b=axes
a.barh([1,0],[negative,positive],color=["#B4C1C8",NAVY],height=.4)
a.set_yticks([1,0],["未患病","患病"]);a.set_xlim(0,205);a.set_xlabel("记录数")
for y,n in [(1,negative),(0,positive)]:a.text(n+3,y,f"{n} ({n/270:.1%})",va="center",fontsize=7)
a.set_title("a  结局构成",fontproperties=HEI,fontsize=9,loc="left",pad=7)
order=sorted([(k,v) for k,v in missing.items() if v],key=lambda kv:kv[1],reverse=True)
b.barh(range(len(order)),[v for _,v in order],color=TEAL,height=.57)
b.set_yticks(range(len(order)),[k for k,_ in order]);b.invert_yaxis()
b.set_xlim(0,215);b.set_xlabel("缺失记录数")
for y,(_,n) in enumerate(order):b.text(n+3,y,str(n),va="center",fontsize=6.8)
b.set_title("b  全部存在缺失的输入",fontproperties=HEI,fontsize=9,loc="left",pad=7)
for ax in axes:clean(ax,False);ax.grid(axis="x",color="#E6EAED",lw=.5)
save(fig,"figure-3-data-audit.png")

# 4: same four-person ranking illustration and theoretical cost threshold.
fig,(a,b)=two_panels(1.8)
a.bar(range(4),[.9,.8,.6,.2],color=[NAVY,"#BAC4CB",NAVY,"#BAC4CB"],width=.52)
a.set_xticks(range(4),["甲（阳）","乙（阴）","丙（阳）","丁（阴）"])
a.set_yticks([0,.5,1]);a.set_ylim(0,1.05);a.set_ylabel("预测患病概率")
a.axhline(.5,c=TEAL,lw=.75,ls="--");a.axhline(.85,c=GRAY,lw=.75,ls=":")
a.set_title("a  排序固定，分类随阈值改变",fontproperties=HEI,fontsize=9,loc="left",pad=7)
r=np.linspace(0,.5,300)
b.plot(r,1-r,c=NAVY,lw=1.6,label="判阳性：1-p")
b.plot(r,5*r,c=TEAL,lw=1.6,label="判阴性：5p")
b.axvline(1/6,c=GRAY,lw=.7,ls="--");b.scatter([1/6],[5/6],c=NAVY,s=18,zorder=4)
b.set(xlabel="校准风险 p",ylabel="期望成本",xlim=(0,.5),ylim=(0,2.6))
b.set_xticks([0,1/6,.3,.5],["0","1/6","0.3","0.5"])
b.legend(frameon=False,fontsize=7,loc="upper left")
b.set_title("b  概率与行动成本",fontproperties=HEI,fontsize=9,loc="left",pad=7)
for ax in (a,b):clean(ax)
save(fig,"figure-4-evaluation-cost.png")

# 5: controlled near-duplicate-feature illustration, not fitted disease results.
fig,(a,b)=two_panels(1.85)
g=np.arange(2); w=.28
a.bar(g-w/2,[.4,1.2],width=w,color=NAVY,label="原变量系数")
a.bar(g+w/2,[.1,-.7],width=w,color=TEAL,label="近重复变量系数")
a.axhline(0,c=GRAY,lw=.6);a.set_xticks(g,["组合 A","组合 B"])
a.set_ylim(-.9,1.75);a.set_ylabel("系数")
a.text(.5,1.5,"两组合计均为 0.5",ha="center",fontsize=7,color=GRAY)
a.legend(frameon=False,fontsize=6.7,loc="lower left")
a.set_title("a  单个系数分配可以变化",fontproperties=HEI,fontsize=9,loc="left",pad=7)
rng=np.random.default_rng(2026);t=np.linspace(-3,3,90);near=t+rng.normal(0,.05,len(t))
pa=1/(1+np.exp(-(.4*t+.1*near)));pb=1/(1+np.exp(-(1.2*t-.7*near)))
b.plot(t,pa,c=NAVY,lw=1.6,label="组合 A")
b.scatter(t,pb,c=TEAL,s=5,alpha=.7,label="组合 B")
b.set(xlabel="原始模拟特征",ylabel="预测概率",ylim=(0,1));b.set_yticks([0,.5,1])
b.legend(frameon=False,fontsize=7,loc="upper left")
b.set_title("b  组合后的预测仍可接近",fontproperties=HEI,fontsize=9,loc="left",pad=7)
for ax in (a,b):clean(ax)
save(fig,"figure-5-stability.png")

# 6: publication-style workflow, a methods diagram rather than a product interface.
fig,ax=plt.subplots(figsize=(6.9,1.05));fig.subplots_adjust(left=.005,right=.995,bottom=.02,top=.98)
ax.set(xlim=(0,10),ylim=(-.35,2));ax.axis("off")
boxes=[(.1,1.02,2.1,.7,"开发数据"),(2.85,1.02,3.1,.7,"训练折拟合 → 验证折预测"),
       (6.6,1.02,3.1,.7,"OOF 比较与模型／阈值选择"),
       (.1,.03,2.1,.63,"锁定测试数据"),(3.05,.03,2.5,.63,"冻结完整方案"),(6.7,.03,2.9,.63,"一次性内部评价")]
for xx,yy,ww,hh,label in boxes:
    ax.add_patch(Rectangle((xx,yy),ww,hh,fc="white",ec=NAVY,lw=.7))
    ax.text(xx+ww/2,yy+hh/2,label,ha="center",va="center",fontsize=7.3,color=NAVY)
for start,end in [((2.2,1.37),(2.85,1.37)),((5.95,1.37),(6.6,1.37)),
                  ((8.15,1.02),(5.55,.5)),((5.55,.35),(6.7,.35))]:
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle="-|>",mutation_scale=8,lw=.7,color=GRAY))
ax.plot([2.2,2.55,2.55,8.15],[.35,.35,-.18,-.18],color=GRAY,lw=.7)
ax.add_patch(FancyArrowPatch((8.15,-.18),(8.15,.03),arrowstyle="-|>",mutation_scale=8,lw=.7,color=GRAY))
save(fig,"figure-6-validation.png")


def set_font(style, name="宋体", latin="Times New Roman", size=10, color=None):
    style.font.name=latin
    style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),name)
    style.font.size=Pt(size)
    if color:style.font.color.rgb=RGBColor.from_string(color)


doc=Document()
CURRENT=doc
sec=doc.sections[0]
sec.page_width,sec.page_height=Cm(21),Cm(29.7)
sec.top_margin,sec.bottom_margin=Cm(1.6),Cm(1.55)
sec.left_margin,sec.right_margin=Cm(1.7),Cm(1.7)
sec.header_distance,sec.footer_distance=Cm(.7),Cm(.75)
for name in ["Normal","Title","Subtitle","Heading 1","Heading 2","Caption","Header","Footer"]:
    set_font(doc.styles[name])
normal=doc.styles["Normal"]
normal.paragraph_format.line_spacing=1.23
normal.paragraph_format.space_after=Pt(4)
normal.paragraph_format.widow_control=True
normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
snap=OxmlElement("w:snapToGrid");snap.set(qn("w:val"),"0")
normal.element.get_or_add_pPr().append(snap)
for name,size in [("Heading 1",11),("Heading 2",10.2)]:
    st=doc.styles[name];set_font(st,"黑体",size=size,color="24445C")
    st.font.bold=False
    st.paragraph_format.space_before=Pt(7)
    st.paragraph_format.space_after=Pt(4)
    st.paragraph_format.keep_with_next=True
    st.paragraph_format.keep_together=True
set_font(doc.styles["Title"],"黑体",size=18.5,color="172D3D")
doc.styles["Title"].font.bold=False
doc.styles["Title"].paragraph_format.space_after=Pt(5)
doc.styles["Title"].paragraph_format.line_spacing=1.15
set_font(doc.styles["Subtitle"],size=10.4,color="526471")
doc.styles["Subtitle"].paragraph_format.space_after=Pt(7)
set_font(doc.styles["Caption"],size=8,color="4F626F")
doc.styles["Caption"].paragraph_format.line_spacing=1.12
doc.styles["Caption"].paragraph_format.space_after=Pt(4)
doc.styles["Caption"].paragraph_format.keep_together=True
for name in ["Header","Footer"]:
    set_font(doc.styles[name],size=7,color="657580")
hp=sec.header.paragraphs[0]
hp.text="生物医学数据科学 · 方法与实践报告"
hp.paragraph_format.space_after=Pt(3)
border=OxmlElement("w:pBdr");bt=OxmlElement("w:bottom")
for key,val in [("val","single"),("sz","4"),("color","A4B1BB"),("space","4")]:bt.set(qn("w:"+key),val)
border.append(bt);hp._p.get_or_add_pPr().append(border)
fp=sec.footer.paragraphs[0]
fp.text="LINEAR CLASSIFICATION · METHODS AND EVIDENCE"
fp.paragraph_format.tab_stops.add_tab_stop(Cm(17.6),2)
fp.add_run("\t")
field=OxmlElement("w:fldSimple");field.set(qn("w:instr"),"PAGE");fp._p.append(field)


def set_columns(section,count):
    cols=section._sectPr.find(qn("w:cols"))
    if cols is None:cols=OxmlElement("w:cols");section._sectPr.append(cols)
    for child in list(cols):cols.remove(child)
    cols.set(qn("w:num"),str(count));cols.set(qn("w:space"),"397")
    cols.set(qn("w:equalWidth"),"1")


def new_section(start,count):
    s=doc.add_section(start)
    set_columns(s,count)
    # End-of-section marker paragraphs must not create extra layout gaps.
    for p in doc.paragraphs[-2:]:
        if p._p.find(".//"+qn("w:sectPr")) is not None and not p.text:
            p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
            p.paragraph_format.line_spacing=Pt(1)
            for run in p.runs:run.font.size=Pt(1)
    return s


def para(text,style=None):
    p=CURRENT.add_paragraph(text,style)
    p.paragraph_format.widow_control=True
    return p


def math_run(text):
    r=OxmlElement("m:r")
    wrpr=OxmlElement("w:rPr");fonts=OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"),"Cambria Math");fonts.set(qn("w:hAnsi"),"Cambria Math")
    wrpr.append(fonts);sz=OxmlElement("w:sz");sz.set(qn("w:val"),"18");wrpr.append(sz);r.append(wrpr)
    t=OxmlElement("m:t");t.text=text;r.append(t)
    return r


def fraction(numerator,denominator):
    f=OxmlElement("m:f")
    num=OxmlElement("m:num");num.append(math_run(numerator));f.append(num)
    den=OxmlElement("m:den");den.append(math_run(denominator));f.append(den)
    return f


equations={
    "linear":("z = β₀ + xᵀβ",None,None,1),
    "sigmoid":("p = σ(z) = ","1","1 + exp(−z)",2),
    "loss":("ℒ = −∑ᵢ [ yᵢ ln pᵢ + (1−yᵢ) ln(1−pᵢ) ]",None,None,3),
    "odds_ratio":("OR(Δ) = exp(βⱼ Δ)",None,None,4),
    "lda_assumption":("X | Y=k ∼ N(μₖ, Σ),  P(Y=k)=πₖ",None,None,5),
    "bayes":("P(Y=k | x) = ","πₖ fₖ(x)","∑ₗ πₗ fₗ(x)",6),
    "lda_score":("δ₁(x)−δ₀(x) = a + xᵀw",None,None,7),
    "brier":("Brier = ","∑ᵢ (pᵢ−yᵢ)²","n",8),
    "cost":("Cost(t) = 5 FN(t) + FP(t)",None,None,9),
    "optimal_threshold":("t* = ","C_FP","C_FN + C_FP",10),
}


def equation(key):
    text,num,den,idx=equations[key]
    p=CURRENT.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(2);p.paragraph_format.space_after=Pt(4)
    p.paragraph_format.keep_together=True
    p.paragraph_format.line_spacing=1.0
    m=OxmlElement("m:oMath");m.append(math_run(text))
    if num:m.append(fraction(num,den))
    p._p.append(m)
    rr=p.add_run(f"  ({idx})");rr.font.size=Pt(7.5)


def image(name,caption):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(1)
    p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(FIG/name),width=Cm(17.6))
    para(caption,"Caption")


def border_cell(cell,edge,size):
    pr=cell._tc.get_or_add_tcPr();b=pr.find(qn("w:tcBorders"))
    if b is None:b=OxmlElement("w:tcBorders");pr.append(b)
    for old in list(b):
        if old.tag==qn("w:"+edge):b.remove(old)
    el=OxmlElement("w:"+edge);el.set(qn("w:val"),"single" if size else "nil")
    el.set(qn("w:sz"),str(size));el.set(qn("w:color"),"687E8E");b.append(el)


def table(key,caption):
    cp=para(caption,"Caption");cp.paragraph_format.keep_with_next=True
    if key=="descriptives":
        headers=["输入变量","有效 n","中位数［Q1，Q3］","缺失 n（%）"]
        rows=[]
        for c in ["age","trestbps","chol","thalach","oldpeak"]:
            vals=np.array([float(r[c]) for r in data if r[c].strip() not in missing_tokens])
            q1,med,q3=np.quantile(vals,[.25,.5,.75])
            def fmt(v):return f"{v:.2f}".rstrip("0").rstrip(".")
            rows.append([c,str(len(vals)),f"{fmt(med)} [{fmt(q1)}, {fmt(q3)}]",f"{missing[c]} ({missing[c]/270:.1%})"])
        widths=[3.1,2.1,7.2,5.2]
    elif key=="metrics":
        headers=["指标","定义／对象","主要职责"]
        rows=[
            ["Sensitivity","TP／(TP＋FN)","真实阳性中检出比例"],
            ["Specificity","TN／(TN＋FP)","真实阴性中正确排除比例"],
            ["Precision","TP／(TP＋FP)","预测阳性中的实际阳性比例"],
            ["ROC-AUC","阳性高于阴性，同分计一半","排序区分，不指定阈值"],
            ["AP","PR 表现的汇总评分","检出与阳性预测质量"],
            ["Brier／log loss","概率与标签的综合评分","概率质量，越低通常越好"],
        ]
        widths=[3.2,6.5,7.9]
    else:
        headers=["模型","均值／系数","协方差与先验","q＝20 时总数"]
        rows=[
            ["Logistic","q＋1","—","21"],
            ["LDA","2q","q(q＋1)／2＋1","251"],
            ["QDA","2q","q(q＋1)＋1","461"],
        ]
        widths=[3.0,3.8,7.1,3.7]
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    for col,width in zip(t.columns,widths):col.width=Cm(width)
    for j,val in enumerate(headers):t.rows[0].cells[j].text=val
    for row in rows:
        cells=t.add_row().cells
        for j,val in enumerate(row):cells[j].text=val
    for row_i,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr();cant=OxmlElement("w:cantSplit");trpr.append(cant)
        for j,cell in enumerate(row.cells):
            cell.width=Cm(widths[j])
            for edge in ["top","left","bottom","right"]:border_cell(cell,edge,0)
            if row_i==0:
                border_cell(cell,"top",6);border_cell(cell,"bottom",4)
            if row_i==len(t.rows)-1:border_cell(cell,"bottom",6)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                p.paragraph_format.line_spacing=1.08
                for r in p.runs:
                    r.font.size=Pt(8.3)
                    if row_i==0:
                        rpr=r._element.get_or_add_rPr()
                        rf=rpr.rFonts
                        if rf is None:rf=OxmlElement("w:rFonts");rpr.insert(0,rf)
                        rf.set(qn("w:eastAsia"),"黑体")
    repeat=OxmlElement("w:tblHeader");repeat.set(qn("w:val"),"true");t.rows[0]._tr.get_or_add_trPr().append(repeat)


set_columns(sec,1)
for page_i,page in enumerate(PAGES):
    CURRENT=doc
    if page_i:
        doc.add_page_break()
    if page_i==0:
        para(TITLE,"Title");para(SUBTITLE,"Subtitle")
        para("方法学比较与实践分析  |  2026 年 11 月","Caption")
        p=para("摘要  "+ABSTRACT)
        p.paragraph_format.space_after=Pt(6)
        for r in p.runs:r.font.size=Pt(9)
        para("关键词："+KEYWORDS,"Caption")
    else:
        p=para(page["heading"],"Title")
        for r in p.runs:r.font.size=Pt(14)
    if page.get("figure_top"):
        image(page["figure_top"],page["caption_top"])
    blocks=page["blocks"]
    def block_weight(block):
        kind,text=block
        if kind in {"h2","h3"}:return 2.0
        if kind=="eq":return 2.2
        han=sum('\u4e00'<=ch<='\u9fff' for ch in text)
        return (han+(len(text)-han)*.5)/23+1.1
    total=sum(block_weight(b) for b in blocks)
    choices=[i for i in range(1,len(blocks)) if blocks[i][0] in {"h2","h3"}]
    split=min(choices,key=lambda i:abs(sum(block_weight(b) for b in blocks[:i])-total/2))
    layout=doc.add_table(rows=1,cols=3);layout.autofit=False
    for col,width in zip(layout.columns,[8.45,.7,8.45]):col.width=Cm(width)
    for cell,width in zip(layout.rows[0].cells,[8.45,.7,8.45]):
        cell.width=Cm(width)
        pr=cell._tc.get_or_add_tcPr()
        mar=OxmlElement("w:tcMar")
        for edge in ["top","left","bottom","right"]:
            el=OxmlElement("w:"+edge);el.set(qn("w:w"),"0");el.set(qn("w:type"),"dxa");mar.append(el)
            border_cell(cell,edge,0)
        pr.append(mar)
    for cell,part in [(layout.cell(0,0),blocks[:split]),(layout.cell(0,2),blocks[split:])]:
        CURRENT=cell
        cell._element.remove(cell.paragraphs[0]._element)
        for kind,text in part:
            if kind=="eq":equation(text)
            elif kind=="h2":para(text,"Heading 1")
            elif kind=="h3":para(text,"Heading 2")
            elif kind=="thought":
                p=para(text)
                for r in p.runs:r.font.color.rgb=RGBColor.from_string("24445C")
            elif kind=="note":para(text,"Caption")
            else:para(text)
    CURRENT=doc
    if page.get("table"):table(page["table"],page["table_caption"])
    if page.get("figure"):image(page["figure"],page["caption"])
    if page.get("references"):
        para("参考资料与数据说明","Heading 1")
        for reference in REFERENCES:
            p=para(reference)
            p.paragraph_format.line_spacing=1.1;p.paragraph_format.space_after=Pt(3)
            for r in p.runs:r.font.size=Pt(8)
        p=para("图示说明：图 1、2、4 为公式或机制演算，图 5 为受控模拟；图 3 与表 1 是当前文件审计。其他表格为方法学定义或参数计数。本报告未将示例当作模型实测性能。","Caption")

settings=doc.settings.element
upd=OxmlElement("w:updateFields");upd.set(qn("w:val"),"false");settings.append(upd)
doc.core_properties.title=TITLE
doc.core_properties.subject=SUBTITLE
doc.core_properties.author=""
doc.core_properties.keywords="Logistic; LDA; 概率校准; 数据审计; 阈值; 稳定性"
doc.save(DEST)
print("Saved:",DEST)
print("Native columns sections:",len(doc.sections))
print("Figures:",len(doc.inline_shapes),"Tables:",len(doc.tables))
print("Native equations:",len(doc.element.findall(".//"+qn("m:oMath"))))
