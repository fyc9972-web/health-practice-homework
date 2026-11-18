"""Build a three-page journal-style classroom report using course source data."""
from pathlib import Path
import csv
import json
import math
import os
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'svm-report-preview'
ASSETS = OUT / 'figures'
ASSETS.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(ROOT / '.tmp' / 'report-layout' / 'matplotlib')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

TEAL = '#167B83'
OCHRE = '#BA6435'
INK = '#252B30'
GRAY = '#68727A'
ACCENT = '8C2F3C'

plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 8, 'text.color': INK,
    'axes.labelcolor': INK, 'axes.edgecolor': '#7C858A',
    'xtick.color': GRAY, 'ytick.color': GRAY,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': .6, 'xtick.major.width': .6, 'ytick.major.width': .6,
    'xtick.major.size': 3, 'ytick.major.size': 3,
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'savefig.facecolor': 'white', 'figure.facecolor': 'white',
})


def export(fig, name):
    for ext in ['png', 'svg', 'pdf']:
        fig.savefig(ASSETS / f'{name}.{ext}', dpi=360)
    plt.close(fig)


def tag(ax, s):
    ax.text(-.12, 1.065, s, transform=ax.transAxes, fontweight='bold',
            fontsize=11, color=INK)


def figures():
    with (ROOT / 'data/student/train.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    names = ['pelvic_incidence', 'degree_spondylolisthesis']
    mean = np.array([statistics.mean(float(r[c]) for r in rows) for c in names])
    sd = np.array([statistics.pstdev(float(r[c]) for r in rows) for c in names])
    chosen = []
    for label, condition in [('0', lambda x: float(x[names[1]]) < 5),
                             ('1', lambda x: float(x[names[1]]) > 30)]:
        chosen += sorted([r for r in rows if r['abnormal'] == label and condition(r)],
                         key=lambda r: r['sample_id'])[:4]
    z = (np.array([[float(r[c]) for c in names] for r in chosen]) - mean) / sd
    labels = np.array([int(r['abnormal']) for r in chosen])
    ids = [r['sample_id'] for r in chosen]
    p, n = z[ids.index('V061')], z[ids.index('V217')]
    delta = p - n
    w = 2 * delta / (delta @ delta)
    b = -w @ ((p + n) / 2)
    norm = np.linalg.norm(w)
    assert np.min((2 * labels - 1) * (z @ w + b)) > 1 - 1e-8

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.62),
                             gridspec_kw={'width_ratios': [1.35, 1]})
    fig.subplots_adjust(left=.09, right=.975, bottom=.22, top=.86, wspace=.47)
    ax = axes[0]
    xx = np.linspace(-1.95, 1.7, 300)
    ax.fill_between(xx, (-1-w[0]*xx-b)/w[1], (1-w[0]*xx-b)/w[1], color='#EAF3F3')
    for level, ls in [(-1, '--'), (0, '-'), (1, '--')]:
        ax.plot(xx, (level-w[0]*xx-b)/w[1], color=INK if level == 0 else '#809496',
                linewidth=1.2 if level == 0 else .7, linestyle=ls)
    for cls, color, marker, label in [(0, TEAL, 'o', 'NO'), (1, OCHRE, '^', 'AB')]:
        sel = labels == cls
        ax.scatter(z[sel, 0], z[sel, 1], c=color, s=28, marker=marker,
                   label=label, edgecolors='white', linewidths=.5, zorder=3)
    sv = [ids.index('V217'), ids.index('V061')]
    ax.scatter(z[sv, 0], z[sv, 1], s=88, facecolors='none', edgecolors=INK,
               linewidth=.85, zorder=4, label='Support vectors')
    for idx, offset in [(sv[0], (-34, -14)), (sv[1], (5, 7))]:
        ax.annotate(ids[idx], z[idx], xytext=offset, textcoords='offset points', fontsize=7)
    ax.set(xlim=(-1.95, 1.7), ylim=(-1.1, 2.0), xlabel='z1  Pelvic incidence',
           ylabel='z2  Spondylolisthesis')
    ax.set_aspect('equal', adjustable='box')
    ax.legend(loc='upper right', frameon=False, fontsize=6.8, handlelength=1.2)
    tag(ax, 'a')
    ax.set_title('Separable teaching subset', fontsize=8.5, loc='left', pad=8)
    ax = axes[1]
    values = []
    for off in [-.6, 0, .6]:
        values.append(float(np.min((2*labels-1)*(z@w+b+off)/norm)))
    bars = ax.bar(['−0.6', '0', '+0.6'], values,
                  color=['#C1CBCE', TEAL, '#C1CBCE'], width=.58)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, v+.035, f'{v:.3f}',
                ha='center', fontsize=8)
    ax.set(ylim=(0, 1.16), ylabel='Minimum signed distance', xlabel='Intercept offset')
    ax.set_yticks([0, .5, 1])
    ax.text(.5, .91, 'Training errors: 0 for all', transform=ax.transAxes,
            ha='center', color=GRAY, fontsize=7)
    ax.set_title('Zero errors, different margins', fontsize=8.5, loc='left', pad=8)
    tag(ax, 'b')
    export(fig, 'figure_1_margin')

    fig = plt.figure(figsize=(7.0, 2.65))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.5, 1, 1, .065],
                          left=.075, right=.955, bottom=.24, top=.85, wspace=.55)
    ax = fig.add_subplot(gs[0])
    r = np.linspace(0, 4, 400)
    for gamma, color in [(.1, TEAL), (1, OCHRE), (10, INK)]:
        ax.plot(r, np.exp(-gamma*r*r), color=color, linewidth=1.5,
                label=f'γ = {gamma:g}')
    ax.axhline(math.exp(-1), color='#AFB8BB', linewidth=.7, linestyle=':')
    ax.set(xlim=(0, 4), ylim=(0, 1.04), xlabel='Distance r', ylabel='Kernel similarity K')
    ax.set_xticks([0, 1, 2, 3, 4]); ax.set_yticks([0, .5, 1])
    ax.legend(frameon=False, fontsize=7, loc='upper right')
    ax.set_title('Similarity decay', loc='left', fontsize=8.5, pad=8); tag(ax, 'a')
    grid = np.linspace(-4, 4, 250)
    X, Y = np.meshgrid(grid, grid)
    for col, gamma, letter in [(1, .1, 'b'), (2, 1, 'c')]:
        ax = fig.add_subplot(gs[col])
        K = np.exp(-gamma*(X*X+Y*Y))
        im = ax.imshow(K, origin='lower', extent=[-4, 4, -4, 4],
                       cmap='YlGnBu', vmin=0, vmax=1, interpolation='bilinear')
        ax.add_patch(Circle((0, 0), 1/math.sqrt(gamma), edgecolor='white',
                            facecolor='none', linestyle='--', linewidth=.9))
        ax.scatter([0], [0], s=13, c='white', edgecolors=INK, linewidth=.4)
        ax.set_xticks([-4, 0, 4]); ax.set_yticks([-4, 0, 4]); ax.set_xlabel('Δz1')
        ax.set_title(f'γ = {gamma:g}', fontsize=8.5, loc='left', pad=8)
        tag(ax, letter)
    cax = fig.add_subplot(gs[3]); cb = fig.colorbar(im, cax=cax, ticks=[0, .5, 1])
    cb.outline.set_linewidth(.5); cb.ax.tick_params(labelsize=7, width=.5)
    export(fig, 'figure_2_gamma')

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5))
    fig.subplots_adjust(left=.09, right=.975, bottom=.23, top=.83, wspace=.38)
    series = [([.01, .1, 1, 10], [.5, .848016, .864286, .870238],
               [.5, .772619, .784524, .769048], 'γ  (C = 1)', 'Changing similarity range'),
              ([1, 10, 100], [.870238, .870238, .910317],
               [.769048, .804762, .669048], 'C  (γ = 10)', 'Changing violation cost')]
    for ax, data, letter in zip(axes, series, ['a', 'b']):
        x, tr, va, xlabel, title = data
        ax.semilogx(x, tr, color=GRAY, marker='o', markersize=3.7,
                    linewidth=1.1, linestyle='--', label='Training')
        ax.semilogx(x, va, color=TEAL, marker='o', markersize=4,
                    linewidth=1.5, label='Validation')
        ax.set(ylim=(.45, .97), xlabel=xlabel, ylabel='Balanced accuracy')
        ax.set_yticks([.5, .7, .9]); ax.set_xticks(x)
        ax.set_xticklabels([f'{v:g}' for v in x]); ax.minorticks_off()
        ax.grid(axis='y', color='#E7EAEB', linewidth=.5)
        ax.set_title(title, fontsize=8.5, loc='left', pad=9); tag(ax, letter)
    axes[0].legend(frameon=False, fontsize=7, loc='lower right')
    axes[1].annotate('Training ↑\nValidation ↓', xy=(100, .669048),
                      xytext=(13, .54), fontsize=7, color=OCHRE,
                      arrowprops={'arrowstyle':'-', 'color':OCHRE, 'lw':.7})
    export(fig, 'figure_3_validation')
    manifest = {'geometry': {'w': w.tolist(), 'b': float(b),
                'minimum_distances': values, 'ids': ids},
                'figure_1': 'Reconstructed from student train.csv; no optimizer used.',
                'figure_2': 'Analytical RBF values, not patient measurements.',
                'figure_3_and_table_1': 'Course teacher-reference.md; not refitted.',
                'test_labels': 'Not read or evaluated.'}
    (OUT / 'source-notes.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')


def font(run, size=9.5, bold=False, face='宋体', color='252B30', italic=False):
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement('w:rFonts'); rpr.insert(0, fonts)
    fonts.set(qn('w:eastAsia'), face)
    fonts.set(qn('w:ascii'), 'Times New Roman')
    fonts.set(qn('w:hAnsi'), 'Times New Roman')
    return run


def para(container, text='', size=9.5, after=5, before=0, bold=False,
         face='宋体', color='252B30', indent=False, align=None):
    p = container.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.line_spacing = Pt(size*1.5)
    p.paragraph_format.widow_control = True
    if align is not None: p.alignment = align
    elif size >= 9 and not bold: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent: p.paragraph_format.first_line_indent = Pt(size*2)
    font(p.add_run(text), size, bold, face, color)
    return p


def heading(container, text, size=11):
    p = para(container, text, size, after=6, before=4, bold=True, face='黑体')
    p.paragraph_format.keep_with_next = True
    return p


def equation(container, text, number=None, size=11):
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = Pt(20)
    def mr(text, upright=False):
        r=OxmlElement('m:r')
        if upright:
            pr=OxmlElement('m:rPr');st=OxmlElement('m:sty');st.set(qn('m:val'),'p')
            pr.append(st);r.append(pr)
        t=OxmlElement('m:t');t.text=text;r.append(t)
        return r
    def script(base, index, kind='sSub'):
        el=OxmlElement('m:'+kind);e=OxmlElement('m:e');e.append(mr(base));el.append(e)
        sub=OxmlElement('m:sub' if kind=='sSub' else 'm:sup');sub.append(mr(index));el.append(sub)
        return el
    math_obj = OxmlElement('m:oMath')
    if number==1 or number=='1':
        math_obj.append(script('min','w,b'));math_obj.append(mr('  '))
        frac=OxmlElement('m:f')
        for name,value in [('num','1'),('den','2')]:
            part=OxmlElement('m:'+name);part.append(mr(value));frac.append(part)
        math_obj.append(frac);math_obj.append(script('‖w‖','2','sSup'))
        math_obj.append(mr('    s.t.  ',True));math_obj.append(script('y','i'))
        math_obj.append(mr('('));math_obj.append(script('w','T','sSup'))
        math_obj.append(script('z','i'));math_obj.append(mr('+b) ≥ 1'))
    elif number==2 or number=='2':
        math_obj.append(mr('f(z) = '))
        nary=OxmlElement('m:nary');pr=OxmlElement('m:naryPr')
        ch=OxmlElement('m:chr');ch.set(qn('m:val'),'∑');pr.append(ch)
        loc=OxmlElement('m:limLoc');loc.set(qn('m:val'),'subSup');pr.append(loc)
        hide=OxmlElement('m:supHide');hide.set(qn('m:val'),'1');pr.append(hide)
        nary.append(pr)
        sub=OxmlElement('m:sub');sub.append(mr('i∈SV'));nary.append(sub)
        nary.append(OxmlElement('m:sup'))
        e=OxmlElement('m:e');e.append(script('α','i'));e.append(script('y','i'))
        e.append(mr(' K('));e.append(script('z','i'));e.append(mr(',z)'));nary.append(e)
        math_obj.append(nary);math_obj.append(mr(' + b'))
    elif number==3 or number=='3':
        math_obj.append(mr('K(z,u) = '));math_obj.append(mr('exp',True))
        math_obj.append(mr('(−γ'));math_obj.append(script('‖z−u‖','2','sSup'))
        math_obj.append(mr('),    γ > 0'))
    else:
        math_obj.append(mr(text))
    p._p.append(math_obj)
    if number: font(p.add_run('   ('+str(number)+')'), 9, color='68727A')
    return p


def rule(p, color='AAB1B4', size=5):
    ppr = p._p.get_or_add_pPr(); borders = OxmlElement('w:pBdr')
    el = OxmlElement('w:bottom'); el.set(qn('w:val'), 'single')
    el.set(qn('w:sz'), str(size)); el.set(qn('w:color'), color)
    el.set(qn('w:space'), '6'); borders.append(el); ppr.append(borders)


def columns(doc, left, right):
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [8.25, .7, 8.25]
    for col, width in zip(table.columns, widths): col.width = Cm(width)
    for cell, width in zip(table.rows[0].cells, widths):
        cell.width = Cm(width); cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        cell.paragraphs[0].paragraph_format.space_after = Pt(0)
        cell.paragraphs[0].paragraph_format.line_spacing = Pt(1)
        cell.paragraphs[0].add_run().font.size = Pt(1)
        tcpr = cell._tc.get_or_add_tcPr()
        margin = OxmlElement('w:tcMar')
        for key in ['top', 'left', 'bottom', 'right']:
            e=OxmlElement('w:'+key);e.set(qn('w:w'),'0');e.set(qn('w:type'),'dxa');margin.append(e)
        tcpr.append(margin)
    left(table.cell(0, 0)); right(table.cell(0, 2))
    # Content tables deliberately have no rules; table 1 below uses three horizontal rules.
    return table


def picture(doc, name, caption):
    p = doc.add_paragraph(); p.paragraph_format.space_after=Pt(1)
    p.paragraph_format.space_before=Pt(4)
    p.add_run().add_picture(str(ASSETS/f'{name}.png'), width=Cm(17.2))
    p.paragraph_format.keep_with_next=True
    para(doc, caption, size=8, after=8, color='485158')


def new_page(doc):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=Pt(1)
    p.add_run().add_break(WD_BREAK.PAGE)


def build_doc():
    d=Document()
    sec=d.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(1.65);sec.bottom_margin=Cm(1.65)
    sec.left_margin=Cm(1.9);sec.right_margin=Cm(1.9)
    sec.header_distance=Cm(.7);sec.footer_distance=Cm(.75)
    for sty in ['Normal','Caption']:
        s=d.styles[sty];s.font.name='Times New Roman';s.font.size=Pt(9.5)
        s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
        s.paragraph_format.space_after=Pt(5)
    for sty in ['Header','Footer']:
        d.styles[sty].paragraph_format.tab_stops.clear_all()
    h=sec.header.paragraphs[0]
    h.paragraph_format.tab_stops.add_tab_stop(Cm(17.2), WD_ALIGN_PARAGRAPH.RIGHT)
    font(h.add_run('METHODS & PRACTICE'),8,bold=True,color=ACCENT)
    font(h.add_run('\tSVM · 课堂研究报告'),8,color='68727A')
    rule(h,color=ACCENT,size=7)
    f=sec.footer.paragraphs[0]
    f.paragraph_format.tab_stops.add_tab_stop(Cm(17.2), WD_ALIGN_PARAGRAPH.RIGHT)
    font(f.add_run('生物医学数据科学  |  版式预览 · 2026.11'),7.5,color='68727A')
    font(f.add_run('\t'),8)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
    rule(f,color='C7CCCE',size=4)

    para(d,'方法与实践  /  SUPPORT VECTOR MACHINES',8,after=8,bold=True,face='黑体',color=ACCENT)
    p=para(d,'支持向量机的间隔、对偶与核机制',22,after=4,bold=True,face='黑体')
    p.paragraph_format.line_spacing=Pt(30)
    para(d,'从几何约束到局部相似度的课堂实践',12,after=4,face='黑体',color='485158')
    p=para(d,'Geometry, duality and kernels in support vector machines',10.5,after=9,color='68727A')
    p.runs[0].italic=True
    p=para(d,'摘要  支持向量机以间隔原则选择分类边界，并通过软间隔在复杂度与训练违例之间权衡。本报告依托脊柱生物力学课堂实践，将几何解释、对偶表示与核相似度连接为一条方法主线。八点教学子集说明零训练错误不足以唯一确定边界；RBF 解析图进一步区分相似度、局部作用范围与概率。受控参数切片表明，更强训练贴合不保证验证表现改善。本文为三页版式样稿，实验数值引用随附课程参考，未重新拟合模型。',9,after=5)
    para(d,'关键词  支持向量机；最大间隔；对偶表示；RBF 核；gamma；受控实验',8,after=10,color='68727A')
    picture(d,'figure_1_margin',
            '图 1｜零错误边界仍有几何差异。a，来自训练集的八点可分教学子集，圆圈标识支撑当前解的两条记录，浅色区域为 f=±1 之间的参考带。b，固定法向量、仅平移截距时，三个候选均零错误，但最近点的带标签几何距离不同。坐标采用全训练集标准化；八点不用于估计总体性能。')
    def left(c):
        heading(c,'1  从最大间隔到可优化目标')
        para(c,'线性模型以 f(z)=wᵀz+b 给出评分，符号确定预测类别。分数的数值依赖方程表示；除以权重范数后，|f(z)|/‖w‖ 才是该输入空间中的垂直距离。可分情形下，将最小带标签分数规范为 1，最大化间隔等价于最小化半个权重范数平方。',10.5)
        equation(c,'min  ½‖w‖²    s.t.  yᵢ(wᵀzᵢ+b) ≥ 1','1')
        para(c,'这里的约束不可省略，否则 w=0 即可使目标最小。软间隔进一步允许违例，以 hinge=max(0,1−yf) 衡量代价，C 决定其相对权重。',10.5)
    def right(c):
        heading(c,'研究对象与实验协议')
        para(c,'UCI Vertebral Column 含 310 条记录。本课预先指定骨盆入射角与脊椎滑脱程度两项输入，将正常 NO 与异常 AB 作为二分类标签；AB 合并椎间盘突出与脊椎滑脱。[1,2]',10.5)
        para(c,'训练、验证与测试分别为 186、62、62 条；StandardScaler 仅在训练集拟合。八点子集按可分规则有意选取，正式参数实验使用全部训练记录。sample_id 仅用于追踪，不进入模型。',10.5)
        para(c,'实验问题  多条线都能分对时，哪条具有更大的最近点余量？图 1 将边界选择与训练错误区分开来。',9,face='黑体',color='485158')
    columns(d,left,right)

    new_page(d)
    heading(d,'2  对偶表示如何连接核相似度',13)
    def left(c):
        heading(c,'2.1  从求边界到求样本系数')
        para(c,'将分类约束引入拉格朗日函数，对 w 求一阶条件，可得 w=Σᵢαᵢyᵢzᵢ。原问题直接寻找边界参数；对偶问题则求样本系数 α。在线性可分的标准硬间隔问题中，强对偶性保证两者最优目标值一致。',10.5)
        para(c,'αᵢ>0 的训练样本称为支持向量。将 w 的展开式代入预测函数后，计算只涉及样本内积；对偶训练目标也具有相同的内积结构。',10.5)
    def right(c):
        heading(c,'2.2  特征变换与核技巧')
        para(c,'若原输入中的关系不适合线性分隔，可先映射为 φ(z)，再在新表示中寻找线性边界。核函数 K(z,u)=〈φ(z),φ(u)〉直接计算映射后的内积，避免显式展开全部坐标。[3]',10.5)
        para(c,'例如，一维两端为正类、中间为负类的结构，可由 φ(x)=x² 重新表示。RBF 对应另一种隐式特征映射；它不等同于这个平方变换示例。',10.5)
    columns(d,left,right)
    equation(d,'f(z) = ∑ᵢ∈SV αᵢyᵢ K(zᵢ,z) + b','2')
    equation(d,'K(z,u) = exp(−γ‖z−u‖²),    γ > 0','3')
    picture(d,'figure_2_gamma',
            '图 2｜gamma 调节核相似度的空间衰减。a，RBF 相似度随距离下降，较大 gamma 对应更快衰减。b、c，以单个支持向量为中心的核值分布，采用相同坐标范围与色标；白色虚线表示 K=e⁻¹，对应半径 r*=1/√γ。热图为公式计算的机制示意，不是患者风险图，也不是完整模型的分类边界。')
    def left(c):
        heading(c,'相似度：进入预测的核权重')
        para(c,'RBF 相似度 K 表示两个标准化输入在当前核规则下有多接近。K=1 对应坐标相同；距离增大时 K 趋近 0。预测中，每个支持向量贡献 αᵢyᵢK(zᵢ,z)：在其系数固定时，K 越大，贡献的绝对值越大。',10.5)
        para(c,'这种相似度比较的是输入特征，不保证疾病标签相同。K=0.9 不表示 90% 的患病概率，模型分数 f 也不天然具有概率含义。',10.5)
    def right(c):
        heading(c,'作用范围：局部贡献的衰减尺度')
        para(c,'作用范围描述一个支持向量能在多大距离上保持明显的核权重。γ 从 0.1 增至 1 时，距离为 2 处的 K 从约 0.670 降至 0.018，说明影响更集中于附近。RBF 没有严格截断半径。',10.5)
        para(c,'gamma 改变相似度，C 改变训练违例的代价。两者需通过固定切片分别解释；RBF 图中的 f=±1 也不能直接当作原二维平面上的等距线。',10.5)
    columns(d,left,right)

    new_page(d)
    heading(d,'3  受控实践：训练目标与验证表现为何不同步',13)
    para(d,'课堂实践采用“先预测—再运行—用机制解释”的顺序。下面保留两类证据：线性 C 实验呈现范数与违例的权衡，RBF 切片则区分相似度范围和违例代价。所有结果均限定在既定两输入、训练标准化与固定划分条件下。[1,2]',10.5,after=7)
    para(d,'表 1｜只改变线性 SVM 的 C：参考带变窄并不保证验证改善。',8.5,after=5,bold=True,face='黑体')
    table=d.add_table(rows=1,cols=6);table.alignment=WD_TABLE_ALIGNMENT.CENTER
    table.autofit=False
    widths=[1.4,3.1,3.0,2.7,2.0,5.0]
    for col,width in zip(table.columns,widths):col.width=Cm(width)
    values=[['C','参考带总宽度','平均 hinge','训练错误数','SV 数','验证 BA'],
            ['0.01','12.413632','0.631206','60','121','0.500000'],
            ['0.1','1.241363','0.505605','40','121','0.734524'],
            ['1','0.605240','0.405765','37','89','0.759524'],
            ['10','0.491488','0.398717','36','77','0.709524'],
            ['100','0.489468','0.398692','35','76','0.709524']]
    for idx,row_values in enumerate(values):
        cells=table.rows[0].cells if idx==0 else table.add_row().cells
        for j,(cell,value) in enumerate(zip(cells,row_values)):
            cell.width=Cm(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(3)
            p.paragraph_format.line_spacing=Pt(12)
            font(p.add_run(value),8.5,bold=(idx==0 or idx==3),face='黑体' if idx==0 else '宋体')
            tcpr=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'nil')
                if (idx==0 and edge in ['top','bottom']) or (idx==5 and edge=='bottom'):
                    e.set(qn('w:val'),'single');e.set(qn('w:sz'),'7' if edge=='top' or idx==5 else '4')
                    e.set(qn('w:color'),'39464B')
                borders.append(e)
            tcpr.append(borders)
    para(d,'注：宽度为标准化空间中的 2/‖w‖，软间隔带内允许存在样本。BA 为 balanced accuracy。粗体仅标识此线性家族按验证 BA 保留的配置。数值来自课程教师参考，未重新拟合。',7.8,after=5,color='68727A')
    picture(d,'figure_3_validation',
            '图 3｜RBF 的两组单因素切片。a，固定 C=1，只改变 gamma；b，固定 gamma=10，只改变 C。C 从 10 增至 100 时，训练 BA 从约 0.870 升至 0.910，验证 BA 却从约 0.805 降至 0.669。连线仅辅助比较预定离散配置，不表示连续搜索结果。来源：课程教师参考。')
    def left(c):
        heading(c,'3.1  机制解释与尺度控制')
        para(c,'在固定数据与精确最优解条件下，增大 C 会使总 hinge 不增加、范数不减小；训练错误数和验证指标没有相同的单调保证。表 1 中极小 C 的宽带伴随 BA=0.5，说明宽度不能脱离分类能力评价。',10.5)
        para(c,'尺度实验保持信息不变，仅将首个输入乘 100。未标准化时，最大验证分数差约 1.538；训练标准化后约为 1.8×10⁻¹⁴。这检验单位变换的不变性，并不证明标准化消除了所有噪声。',10.5)
    def right(c):
        heading(c,'3.2  评价边界与报告结论')
        para(c,'验证集含 42 个 AB、20 个 NO；始终预测 AB 的 accuracy 已达 0.677，但 BA 仅为 0.5。故本课各家族按验证 BA 冻结配置，再按安排评价测试；不得根据测试追加特征、阈值或参数搜索。',10.5)
        para(c,'SVM 的优势来自明确的间隔目标及可扩展的特征表示；局限包括尺度与参数敏感、核计算成本及概率解释需求。有限同源留出不能直接确认新医院表现。本样稿不读取测试标签。',10.5)
    columns(d,left,right)
    heading(d,'资料与来源',9)
    para(d,'[1] 课堂课件《SVM 与 Margin》：svm-pbl-intro-with-kernel.pptx；学生工作单与 svm-lab.ipynb。\n[2] 本课 data/README.md、teacher-reference.md 及 scripts/lab_utils.py；实验表与图 3 为课程参考值。\n[3] scikit-learn. Support Vector Machines, Mathematical formulation. scikit-learn.org/stable/modules/svm.html。\n[4] Barreto G, Neto A. Vertebral Column. UCI Machine Learning Repository. DOI: 10.24432/C5K89B。',7.2,after=0,color='68727A')

    core=d.core_properties
    core.title='支持向量机的间隔、对偶与核机制'
    core.subject='课堂实践报告：三页期刊式排版样稿'
    core.author='';core.keywords='SVM; margin; duality; kernel; gamma'
    path=OUT/'SVM_期刊风格简易样稿.docx';d.save(path)
    print(path)


if __name__=='__main__':
    figures()
    build_doc()
