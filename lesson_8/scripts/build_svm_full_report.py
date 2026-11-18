"""Typeset the full classroom report with the approved journal-style design."""
from pathlib import Path
import pickle,json,math,zipfile
from analyze_svm_report import ROOT
import build_svm_report_preview as design
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT=ROOT/'results/svm-report';FIG=OUT/'figures';TEXT=[];PAGES=[]
with (OUT/'analysis/development-results.pkl').open('rb') as f:R=pickle.load(f)
with (OUT/'analysis/figure-notes.json').open(encoding='utf-8') as f:FIG_NOTES=json.load(f)
TABLE_COUNT=0

def p(c,text,size=10.5,after=6,**kwargs):
    TEXT.append(text+'\n\n')
    return design.para(c,text,size,after=after,**kwargs)

def h(c,text,size=11.2):
    TEXT.append('### '+text+'\n\n')
    return design.heading(c,text,size)

def page(d,title):
    if PAGES:design.new_page(d)
    PAGES.append(title);TEXT.append('## '+title+'\n\n')
    design.heading(d,title,13)

def columns(d,left,right):return design.columns(d,left,right)

def picture(d,name,caption):
    pp=d.add_paragraph();pp.paragraph_format.space_after=Pt(1)
    pp.paragraph_format.space_before=Pt(5)
    pp.add_run().add_picture(str(FIG/(name+'.png')),width=Cm(17.2))
    pp.paragraph_format.keep_with_next=True
    TEXT.append(f'![{caption.split("｜")[0]}](figures/{name}.png)\n\n')
    p(d,caption,8,after=8,color='485158')

def table(d,title,headers,rows,widths=None,note='',emph=()):
    global TABLE_COUNT
    TABLE_COUNT+=1
    cap=p(d,f'表 {TABLE_COUNT}｜{title}',8.8,after=5,bold=True,face='黑体')
    cap.paragraph_format.keep_with_next=True
    t=d.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    widths=widths or [17.2/len(headers)]*len(headers)
    for col,width in zip(t.columns,widths):col.width=Cm(width)
    allrows=[headers]+[[str(a) for a in row] for row in rows]
    for idx,vals in enumerate(allrows):
        cells=t.rows[0].cells if idx==0 else t.add_row().cells
        pr=t.rows[idx]._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if idx==0:pr.append(OxmlElement('w:tblHeader'))
        for j,(cell,val) in enumerate(zip(cells,vals)):
            cell.width=Cm(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pp=cell.paragraphs[0];pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
            pp.paragraph_format.space_before=Pt(2.5);pp.paragraph_format.space_after=Pt(2.5)
            pp.paragraph_format.line_spacing=Pt(12.3)
            design.font(pp.add_run(val),8.5,bold=idx==0 or idx-1 in emph,face='黑体' if idx==0 else '宋体')
            tcpr=cell._tc.get_or_add_tcPr();bor=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                el=OxmlElement('w:'+edge);el.set(qn('w:val'),'nil')
                if (idx==0 and edge in ['top','bottom']) or (idx==len(allrows)-1 and edge=='bottom'):
                    el.set(qn('w:val'),'single');el.set(qn('w:sz'),'7' if edge=='top' or idx==len(allrows)-1 else '4');el.set(qn('w:color'),'39464B')
                bor.append(el)
            tcpr.append(bor)
    TEXT.append('| '+' | '.join(str(v).replace('|','\\|') for v in headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n')
    for row in rows:TEXT.append('| '+' | '.join(str(v).replace('|','\\|') for v in row)+' |\n')
    TEXT.append('\n')
    if note:p(d,note,7.9,after=7,color='68727A')
    return t

def mr(text,upright=False):
    el=OxmlElement('m:r')
    if upright:
        pr=OxmlElement('m:rPr');st=OxmlElement('m:sty');st.set(qn('m:val'),'p');pr.append(st);el.append(pr)
    node=OxmlElement('m:t');node.text=str(text);el.append(node);return el

def script(base,index,super=False):
    node=OxmlElement('m:sSup' if super else 'm:sSub')
    e=OxmlElement('m:e');e.append(mr(base,upright=base in ['min','max']));node.append(e)
    ix=OxmlElement('m:sup' if super else 'm:sub');ix.append(mr(index));node.append(ix);return node

def frac(a,b):
    node=OxmlElement('m:f')
    for name,text in [('num',a),('den',b)]:
        e=OxmlElement('m:'+name);e.append(mr(text));node.append(e)
    return node

def summation(index,parts):
    node=OxmlElement('m:nary');pr=OxmlElement('m:naryPr')
    for name,value in [('chr','∑'),('limLoc','subSup'),('supHide','1')]:
        e=OxmlElement('m:'+name);e.set(qn('m:val'),value);pr.append(e)
    node.append(pr);lower=OxmlElement('m:sub');lower.append(mr(index));node.append(lower)
    node.append(OxmlElement('m:sup'));body=OxmlElement('m:e')
    for a in parts:body.append(mr(a) if isinstance(a,str) else a)
    node.append(body);return node

def eq(c,parts,number=None,text=''):
    pp=c.add_paragraph();pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    pp.paragraph_format.space_before=Pt(4);pp.paragraph_format.space_after=Pt(7)
    pp.paragraph_format.line_spacing=1.15
    node=OxmlElement('m:oMath')
    for a in parts:node.append(mr(a) if isinstance(a,str) else a)
    pp._p.append(node)
    if number:design.font(pp.add_run(f'   ({number})'),8.7,color='68727A')
    TEXT.append('> '+(text or ''.join(a for a in parts if isinstance(a,str)))+'\n\n')
    return pp

def fmt(x,digits=6):return f'{float(x):.{digits}f}'

def build():
    d=Document();sec=d.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(1.65);sec.bottom_margin=Cm(1.65)
    sec.left_margin=Cm(1.9);sec.right_margin=Cm(1.9)
    # Intentionally no header/footer references, rules, page numbers or running text.
    for name in ['Normal','Caption']:
        style=d.styles[name];style.font.name='Times New Roman';style.font.size=Pt(10.5)
        style.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
        style.paragraph_format.space_after=Pt(6)
    cp=d.core_properties;cp.title='支持向量机的间隔、对偶与核机制'
    cp.subject='基于课堂原始数据与受控实验的完整报告';cp.author=''
    cp.keywords='SVM; maximum margin; duality; kernels; gamma; scaling'

    PAGES.append('摘要与数据任务');TEXT.append('# 支持向量机的间隔、对偶与核机制\n\n')
    pp=p(d,'支持向量机的间隔、对偶与核机制',22,after=4,bold=True,face='黑体');pp.paragraph_format.line_spacing=Pt(30)
    p(d,'基于脊柱生物力学课堂实践的受控实验报告',11.5,after=4,face='黑体',color='485158')
    pp=p(d,'Geometry, duality and kernel similarity in support vector machines',10.3,after=10,color='68727A');pp.runs[0].italic=True
    p(d,'摘要  支持向量机通过间隔原则选择分类边界，并以软间隔协调范数控制与训练违例。本报告严格沿用课堂的两输入、186/62/62 固定划分及 A—G 受控实验，重新计算几何、删点、参数、尺度和扰动结果。八点子集上，三个零错误候选的最小几何距离约为 0.383、0.957、0.383；完整训练集上，训练违例改善不保证验证表现同步提高。对偶表示解释了支持向量如何构成判别函数，核技巧则将特征变换连接到内积计算。RBF 的 gamma 决定相似度衰减尺度，训练标准化可抵消本次单位变化。结论限定于当前输入、划分和人工扰动条件，不作为临床效用证明。',9,after=5)
    p(d,'关键词  支持向量机；最大间隔；支持向量；对偶；核技巧；gamma；标准化',8.2,after=8,color='68727A')
    def a(c):
        h(c,'1  数据定义与课堂问题')
        p(c,'本课不以模型排名为目标，而是追问：多条边界都分对时如何选择；哪些记录约束当前解；数据重叠时怎样允许违例；改变核、gamma 和尺度会发生什么。全部分析以同一份 UCI 脊柱生物力学记录为案例。[1–3]')
    def b(c):
        h(c,'1.1  输入、标签与解释范围')
        p(c,'310 条记录包含 100 个正常 NO 与 210 个异常 AB；AB 合并椎间盘突出和脊椎滑脱。本课只用骨盆入射角、脊椎滑脱程度，ID 不进入模型。标签表示既有分类，不表示未来风险或疾病严重程度。')
    columns(d,a,b)
    picture(d,'fig01_data',f'图 1｜完整训练记录与局部显示。a，186 条训练记录的全范围散点；b，按训练数据主要范围放大，{FIG_NOTES["full_train_local_display_outside"]} 条记录处于显示范围外，但仍参与全部正式拟合。两类存在重叠，极值不能仅因画图不便而删除。横纵轴保留 source scale；源资料未提供足够信息把滑脱程度直接解释为角度或百分比。')
    table(d,'固定划分与各集合职责',['集合','NO / AB','记录数','职责'],
          [['训练','60 / 126','186','拟合 scaler 与 SVM'],['验证','20 / 42','62','参数对照与配置选择'],['测试','20 / 42','62','配置冻结后按课堂安排评价']],
          [2.2,2.3,2.0,10.7],note='标准化只使用训练统计量；验证与测试沿用同一变换。六个原始测量中仅预先指定的两个用于本课二维几何，并非最佳特征组合结论。')

    page(d,'2  决策边界、归一化距离与最大间隔〔实践 B〕')
    def a(c):
        h(c,'2.1  从评分到几何距离')
        p(c,'模型输入记为训练标准化后的 z，线性分数为 f(z)=wᵀz+b。本课按 f≥0 判 AB、f<0 判 NO；f=0 为边界。w 垂直边界，固定 w 改变 b 会平移边界。分数是实数评分，不直接等于概率。')
        eq(c,['d(z) = ',frac('|f(z)|','‖w‖')],1,text='d(z)=|f(z)|/‖w‖')
    def b(c):
        h(c,'2.2  为什么必须除以范数')
        p(c,'将 w、b 同乘正数 3，零集合和预测不变，但 f 变成 3 倍，‖w‖ 也变成 3 倍，故几何距离不变。沿单位法向 w/‖w‖ 投影到边界，可得带符号位移 f/‖w‖；乘上 y 后，其正负区分正确侧与错误侧。')
    columns(d,a,b)
    picture(d,'fig02_margin','图 2｜零训练错误不足以选择唯一边界。a，八条按明示规则挑选的可分训练记录，灰、黑、赭色线的截距偏移分别为 −0.6、0、+0.6，法向量相同；点的类别配色同图 1，空心圈为基准解的支持向量。b，最小带标签距离提供训练错误之外的选择依据。此对照只比较平移候选；一般优化还需同时选择方向与截距。')
    def a(c):
        h(c,'2.3  硬间隔目标从何而来')
        p(c,'可分时可缩放参数，使最小 yᵢfᵢ 等于 1。最近约束点到中线的距离为 1/‖w‖，两条参考线 f=±1 的总宽度为 2/‖w‖。最大间隔因此等价于在分类约束下最小化 ½‖w‖²。')
        p(c,'比较最近点而非距离总和，是为了避免远点掩盖贴边点。软间隔中该宽度仅是参考带尺度，不代表带内必须空无样本。',10.2)
    def b(c):
        h(c,'2.4  V061 的课堂手算')
        p(c,'使用工作单给出的近似参数与标准化坐标：')
        p(c,'w=(0.7287,0.7492)，b=−0.0200',10.0,after=3,align=WD_ALIGN_PARAGRAPH.LEFT)
        p(c,'z=(0.7108,0.6700)',10.0,after=5,align=WD_ALIGN_PARAGRAPH.LEFT)
        p(c,'代入后，分数约为 0.999924，范数约为 1.045134，距离约为 0.956743，预测 AB。保留完整精度时，分数约为 1，距离约为 0.956807。')
        p(c,'所有宽度均在 z 空间中，不是原始测量单位。随意放大已训练模型的分数会改变 hinge 与 f=±1 参考线，不能据边界不变推断目标函数也不变。',10.2)
    columns(d,a,b)
    eq(d,[script('min','w,b'),'  ',frac('1','2'),script('‖w‖','2',True),'    s.t.  ',script('y','i'),'(',script('w','T',True),script('z','i'),'+b) ≥ 1'],2,text='min ½‖w‖²，约束 yᵢ(wᵀzᵢ+b)≥1')
    table(d,'三个候选边界的几何核对',['b 偏移','训练错误数','最小带标签距离'],
          [[f'{row.offset:+.1f}',int(row.training_errors),fmt(row.min_signed_distance)] for row in R['geo']['candidates'].itertuples()],
          [3.5,4.5,9.2],note='基准解总参考带宽约 1.913613。代码用 C=10000 的线性 SVC 并核对无实质违例，近似展示硬间隔；并非专用硬间隔求解器。')

    page(d,'3  哪些记录约束边界：支持向量与删除实验〔实践 C〕')
    def a(c):
        h(c,'3.1  从几何支撑到严格定义')
        p(c,'支持向量是当前最优解中对偶系数 αᵢ>0 的训练记录。典型硬间隔图中，它们贴住两侧间隔边界；软间隔的支持向量也可能在带内，甚至被误分。退化情况下，落在参考线上的点也不一定具有非零 α。')
        eq(c,['w = ',summation('i',[script('α','i'),script('y','i'),script('z','i')])],3,text='w=Σᵢαᵢyᵢzᵢ')
    def b(c):
        h(c,'3.2  当前模型中的作用')
        p(c,'w 是样本的带标签加权和，而非普通平均；α=0 的项不直接贡献。支持向量身份由训练样本、特征表示、核和 C 共同决定。其角色属于优化几何，不能解释为患者典型性、病情严重程度或因果重要性。')
        p(c,'八点基准解有两个支持向量：V217 与 V061。实验分别删除远离边界的非 SV V072 与一个 SV V061，并在共同的原八点上比较分数。')
    columns(d,a,b)
    picture(d,'fig03_support','图 3｜冻结尺度后的删点干预。a，黑线为原解，青线为删去非 SV V072 后的解，赭色线为删去 SV V061 后的解；青线与黑线重合，赭色线发生改变。b，在同一原八点集合上比较绝对分数变化，避免评价对象随删点改变。坐标与 C 均固定，所有曲线来自真实重新拟合。')
    table(d,'删除不同记录的实际变化',['删除对象','ID','‖Δw‖','|Δb|','max |Δf|'],
          [['非 SV','V072','0','0','0'],['SV','V061',fmt(R['geo']['changes'].iloc[1].coefficient_change),fmt(R['geo']['changes'].iloc[1].intercept_change),fmt(R['geo']['changes'].iloc[1].score_change_max)]],
          [3,2.2,3.5,3.5,5.0],note='Δf 在原八条记录上计算。删除实验统一使用原 186 条训练记录拟合出的 scaler，重新拟合时不重估尺度。')
    def a(c):
        h(c,'控制变量为何必要')
        p(c,'删点后若重新拟合 scaler，训练均值与标准差会改变，从而同时移动所有坐标。此时既移除一个约束，又改变坐标系，无法只解释删除样本的作用。冻结 scaler 是本次干预设计的必要条件。')
    def b(c):
        h(c,'结论为何不能无限推广')
        p(c,'固定表示和参数时，删去 α=0 的点可保留原解最优；删除一个 SV 则可能改变解，但不保证必然变化，因为可存在冗余约束或非唯一情形。数值精度也可能使输出出现微小差异。')
    columns(d,a,b)

    page(d,'4  从不可分约束到软间隔与 hinge loss〔实践 C〕')
    def a(c):
        h(c,'4.1  一个不能靠核消除的矛盾')
        p(c,'复制一个输入坐标并给予相反标签，正类要求 f(z*)≥1，负类要求 f(z*)≤−1，两者不可能同时成立。任何确定性核映射都会把相同输入映到相同表示，因此复杂核也不能解决这一逻辑冲突。')
        p(c,'这只是教学反事实：原始标签未修改，人工记录不进入正式参数实验，也不证明原始记录存在错标。')
    def b(c):
        h(c,'4.2  用松弛量允许违例')
        p(c,'软间隔令 yᵢfᵢ≥1−ξᵢ，且 ξᵢ≥0。固定 w、b 后，最小可行 ξᵢ 为 max(0,1−yᵢfᵢ)，恰好是 hinge。允许违例使不可分时仍可优化，同时用 C 对违例支付代价。')
        p(c,'ξ=0 表示满足间隔；0<ξ<1 表示分对但间隔不足；ξ>1 表示在错误侧。ξ=1 是边界情形，类别由阈值约定处理。')
    columns(d,a,b)
    eq(d,[script('min','w,b'),'  ',frac('1','2'),script('‖w‖','2',True),' + C ',summation('i',['max(0,1−',script('y','i'),script('f','i'),')'])],4,text='min ½‖w‖² + C Σᵢ max(0,1−yᵢfᵢ)')
    picture(d,'fig04_hinge','图 4｜错误数与间隔违例不是同一个量。a，hinge 同时惩罚错误侧记录和正确但间隔不足的记录；0/1 错误不反映违例程度。b，工作单四个独立算式的损失为 1.5、0.6、0、0；它们不是新增患者。yf<1 表示间隔违例，而是否处于参考带还需看 |f|<1。')
    table(d,'工作单损失与位置核对',['y·f','hinge','分类','相对参考带位置'],
          [['−0.5','1.5','分错','带内，错误侧'],['0.4','0.6','分对','带内，正确侧'],['1','0','分对','正确侧参考线上'],['1.8','0','分对','正确侧带外']],
          [2,2,3,10.2],note='错误侧带外也会有违例，例如 yf=−2 时 hinge=3，但 |f|=2，不在参考带内。')
    table(d,'人工矛盾数据的软间隔拟合',['C','训练错误数','总 hinge','支持向量数'],
          [[f'{a.C:g}',int(a.errors),fmt(a.sum_hinge),int(a.n_sv)] for a in R['geo']['contradiction'].itertuples()],
          [2.2,4,6.5,4.5],note='同坐标相反标签的一对记录，损失和 max(0,1−t)+max(0,1+t) 至少为 2。增大 C 会增加代价，但不能使这对记录同时分类正确。')

    page(d,'5  从原问题到对偶：核技巧所需的内积结构')
    def a(c):
        h(c,'5.1  用乘子连接目标与约束')
        p(c,'对硬间隔约束写 gᵢ=1−yᵢ(wᵀzᵢ+b)≤0，引入 αᵢ≥0 构造拉格朗日函数。α 不是预设风险分数，而是求解过程中获得的对偶变量。对 w、b 的一阶条件给出支持向量展开与标签平衡条件。')
    def b(c):
        h(c,'5.2  对偶性意味着什么')
        p(c,'原问题直接求 w、b；对偶问题求 α。对偶函数给出原问题最优值的下界，最大化该下界可使其尽量紧。标准可分硬间隔 SVM 满足强对偶，原问题最小值等于对偶最大值；相等的是目标值，不是变量本身。')
    columns(d,a,b)
    eq(d,['L = ',frac('1','2'),script('‖w‖','2',True),' + ',summation('i',[script('α','i'),'[1−',script('y','i'),'(',script('w','T',True),script('z','i'),'+b)]'])],5,text='L=½‖w‖²+Σᵢαᵢ[1−yᵢ(wᵀzᵢ+b)]')
    eq(d,['∂L/∂w=0 ⇒ w=',summation('i',[script('α','i'),script('y','i'),script('z','i')]),' ,    ∂L/∂b=0 ⇒ ',summation('i',[script('α','i'),script('y','i')]),'=0'],6,text='w=Σᵢαᵢyᵢzᵢ；Σᵢαᵢyᵢ=0')
    eq(d,[script('max','α'),'  {',summation('i',[script('α','i')]),' − ',frac('1','2'),script('‖Σᵢαᵢyᵢzᵢ‖','2',True),'} ,    αᵢ≥0,  Σᵢαᵢyᵢ=0'],7,text='硬间隔对偶：maxα {Σᵢαᵢ−½‖Σᵢαᵢyᵢzᵢ‖²}，αᵢ≥0，Σᵢαᵢyᵢ=0')
    picture(d,'fig05_duality','图 5｜两点理论例子连接原问题与对偶。取 x=0、y=−1 与 x=2、y=+1，原问题给出 w=1、b=−1。对偶平衡条件使两个 α 相等为 a，w=2a；最大化 Q(a)=2a−2a² 得 a=0.5，同样得到 w=1。此图为数学示例，不是患者数据或额外性能实验。')
    def a(c):
        h(c,'从 α 回到分类函数')
        p(c,'将 w 展开代入预测，得到 f(z)=Σᵢαᵢyᵢ(zᵢᵀz)+b。对偶目标中的范数平方展开后，也只含训练样本的两两内积。因此更换特征表示时，只需提供新表示的内积。')
    def b(c):
        h(c,'软间隔增加的条件')
        p(c,'软间隔对 ξ 求一阶条件，可得 0≤αᵢ≤C。KKT 条件进一步说明：0<αᵢ<C 的点满足 yf=1；αᵢ=C 的点可在边上、带内或错误侧。存在自由支持向量时，可由 b=yᵢ−wᵀzᵢ 求截距。')
    columns(d,a,b)

    page(d,'6  C 如何权衡范数与训练违例〔实践 D〕')
    p(d,'正式实验回到全部 186 条训练记录，冻结输入、scaler、核与验证集，仅改变线性 C。目标中的第一项控制范数，第二项惩罚总 hinge；C 是相对权重，不是噪声比例、风险阈值或参考带宽度。')
    picture(d,'fig06_linear_c','图 6｜C 的变化影响训练机制，但验证表现不必同步。a，标准化空间中的线性参考带总宽度；b，平均 hinge；c，训练与验证 BA。带宽面板采用双对数坐标，其他面板的 C 轴为对数坐标。全部曲线来自本次对课堂预定五组配置的实际拟合。')
    lin=R['grid'][R['grid'].kernel=='linear']
    table(d,'线性 C 实验的完整记录',['C','参考带总宽度','平均 hinge','训练错误','SV 数','验证 BA'],
          [[f'{a.C:g}',fmt(a.linear_width),fmt(a.mean_hinge),int(a.train_errors),int(a.n_sv),fmt(a.val_balanced_accuracy)] for a in lin.itertuples()],
          [1.5,3.3,3.0,2.6,2.0,4.8],note='总 hinge=186×平均 hinge。粗体标识按本课验证规则保留的线性配置；不能跨 C 只比较目标 J 的绝对值，因为改变 C 也改变了目标定义。',emph=[2])
    def a(c):
        h(c,'6.1  哪些趋势有理论保证')
        p(c,'固定数据、表示、核并取得精确最优时，C 增大使总 hinge 不增加、‖w‖ 不减，非零线性 w 的参考带宽不增。训练错误数、SV 数和验证指标没有同样的单调定理。')
        p(c,'用 R₁+C₁H₁≤R₂+C₁H₂ 和 R₂+C₂H₂≤R₁+C₂H₁ 相加，可得 (C₂−C₁)(H₂−H₁)≤0。若 C₂>C₁，则 H₂≤H₁，并可进一步推出 R₂≥R₁。',10.0)
    def b(c):
        h(c,'6.2  为什么宽带仍可能失效')
        p(c,'C=0.01 时参考带很宽，但验证 BA=0.5。较小 C 可把权重压得很小，使分类接近常数；若 w=0，通常的 2/‖w‖ 几何解释不再适用。软间隔带内允许样本，因此宽度不能独立代表模型质量。')
        p(c,'从 C=1 增至 100，平均 hinge 略降，而验证 BA 从约 0.760 降至 0.710。训练违例改善与同源新记录表现是不同问题，需要并列报告。',10.0)
    columns(d,a,b)

    return finish_pages(d)


def finish_pages(d):
    page(d,'7  核函数：用内积表达新的特征关系〔实践 E〕')
    def a(c):
        h(c,'7.1  显式变换解释非线性')
        p(c,'课件用 x=−2、−1、+1、+2 展示两端正类、中间负类。单一原轴阈值无法分开；换成 φ(x)=x² 后，两类分别落在 4 和 1，阈值 2.5 即可区分。特征空间中的线性关系，对应原空间中的非线性。')
        p(c,'这个示例是一维映到一维，说明变换不必总是升维。真正核技巧的价值在于：即使 φ 很大，也可只计算内积而不展开全部坐标。')
    def b(c):
        h(c,'7.2  对偶结构使核替换可行')
        p(c,'令 K(z,u)=〈φ(z),φ(u)〉，对偶训练目标和预测中的普通内积均可替换为 K。核模型依旧在相应特征空间中寻找线性超平面；原二维平面上的边界则可以弯曲。[4,5]')
        p(c,'核必须满足相应内积结构条件，不能把任意相似度直接当成标准 SVM 核。相同输入仍会映到相同表示，故核也无法消除同坐标相反标签的矛盾。')
    columns(d,a,b)
    eq(d,['f(z) = ',summation('i∈SV',[script('α','i'),script('y','i'),'K(',script('z','i'),',z)']),' + b'],8,text='核预测：f(z)=Σᵢ∈SV αᵢyᵢK(zᵢ,z)+b')
    table(d,'课堂使用的三类核',['核','定义','允许表达的关系'],
          [['Linear','K(z,u)=zᵀu','当前输入的线性关系'],['Polynomial','K(z,u)=(γzᵀu+c)ᵈ','平方、交互等特征组合'],['RBF','K(z,u)=exp(−γ‖z−u‖²)','按距离衰减的局部相似度']],
          [2.8,7.4,7.0],note='多项式对照只用 degree=2、coef0=1、gamma=0.1、C=1；不额外搜索。γ=0.1 在本页 RBF 对照中同样固定，线性核不使用 gamma。')
    picture(d,'fig07_kernels',f'图 7｜同一训练数据上的三类代表边界。全部使用 C=1 与训练标准化，背景为预测类别，实线为 f=0，虚线为 f=±1。各图采用同一显示范围；{FIG_NOTES["kernel_display_outside"]} 条范围外记录仍参与拟合。非线性核提供更丰富的函数类，但当前图形不要求明显不同，亦不构成核之间的通用性能排名。')
    def a(c):
        h(c,'二次核为什么包含组合项')
        p(c,'(zᵀu)² 展开含 z₁²u₁²、2z₁z₂u₁u₂、z₂²u₂²，对应 φ(z)=(z₁²,√2z₁z₂,z₂²)。交互项因此无需逐列显式构造，也能进入模型。',10.0)
    def b(c):
        h(c,'特征空间间隔的解释边界')
        p(c,'核空间仍可定义间隔，但 RBF 的 f=±1 不是原平面上的等距线。不能用弯曲轮廓之间的视觉间距，直接和线性 2/‖w‖ 比较几何宽度。',10.0)
    columns(d,a,b)

    page(d,'8  gamma：相似度与局部作用范围〔实践 E〕')
    def a(c):
        h(c,'8.1  相似度到底比较什么')
        p(c,'RBF 将标准化输入间的距离 r 转成核值 K=e^(−γr²)。相同坐标 K=1，距离增大时 K 趋近 0。这是输入特征在当前核规则下的接近程度，既不保证疾病标签相同，也不表示患病概率。')
        p(c,'预测中单个支持向量贡献 αᵢyᵢK(zᵢ,z)。在该系数固定时，K 越大，贡献绝对值越大；正负标签决定把分数往哪一侧推，最后由所有项与 b 共同决定预测。')
    def b(c):
        h(c,'8.2  作用范围不是硬截断')
        p(c,'作用范围描述一个支持向量在多远的距离上仍保留明显核权重。gamma 大时衰减快，影响集中于近处；gamma 小时衰减慢，影响延伸更远。任意有限距离下 RBF 仍为正，没有突然归零的范围边界。')
        p(c,'将 K=e⁻¹ 的位置作为参考尺度，可得 r*=1/√gamma。这是选定相似度水平的半径，不是临床距离，也不是完整分类模型的决策边界。')
    columns(d,a,b)
    eq(d,['K(z,u) = exp(−γ',script('‖z−u‖','2',True),'),    γ > 0'],9,text='RBF：K(z,u)=exp(−γ‖z−u‖²)')
    picture(d,'fig08_gamma','图 8｜gamma 如何改变单个中心的核权重。a，γ=0.1、1、10 的相似度衰减曲线；b、c，以同一中心计算的核值热图，使用相同坐标范围和色标。白色虚线为 K=e⁻¹ 的参考圆。热图是解析机制示意，不是患者风险图或完整 SVM 边界；其颜色不应解释为概率。')
    table(d,'工作单 RBF 手算：必须使用距离平方',['gamma','距离 r=1','距离 r=2','解释'],
          [['0.1',fmt(math.exp(-.1)),fmt(math.exp(-.4)),'衰减较慢，范围较广'],['1',fmt(math.exp(-1)),fmt(math.exp(-4)),'衰减较快，范围较局部']],
          [2,4.0,4.0,7.2],note='r 从 1 增至 2，距离平方从 1 变为 4。γ=1、r=2 时 K≈0.018，表示该支持向量的这项核权重很小，而不是 1.8% 的患病概率。')
    def a(c):
        h(c,'gamma 与 C 分别改变什么')
        p(c,'gamma 改变 K 的距离衰减规则；C 改变训练中违反间隔的相对代价。两者都会影响最终图形，但原因不同，应先固定一个再改变另一个。',10.0)
    def b(c):
        h(c,'为何不能只改公式而不重训')
        p(c,'改变 gamma 也会改变最优 α 和截距；比较核值时可固定系数理解局部贡献，但实际参数对照必须按各组配置重新拟合。局部化不等于验证表现必然改善。',10.0)
    columns(d,a,b)

    page(d,'9  参数切片与联合网格：机制解释先于配置选择〔实践 E〕')
    p(d,'本课先固定 C=1 改变 gamma，再固定 gamma=10 改变 C，以排除同时调参造成的归因混淆。随后查看预先规定的 4×4 联合网格，按验证规则选择家族配置，不追加测试驱动搜索。')
    picture(d,'fig09_slices','图 9｜两组受控切片的真实训练与验证结果。a，gamma 过小时，本次 C=1 模型区分不足；增大 gamma 后验证 BA 并不持续上升。b，固定 gamma=10，C 从 10 增至 100 时训练 BA 从约 0.870 升至 0.910，验证 BA 从约 0.805 降至 0.669。后一现象与更强训练局部贴合带来的过拟合风险一致，但不是所有 RBF 的普遍定律。')
    picture(d,'fig10_grid','图 10｜预定 RBF 网格的验证 balanced accuracy。C∈{0.1,1,10,100}，gamma∈{0.01,0.1,1,10}。颜色与单元格数值均来自固定验证集；按本课规则，本次 RBF 家族保留 C=10、gamma=10。热图用于配置比较，不表示测试结果或新医院的预期表现。')
    def a(c):
        h(c,'9.1  为什么不能只看训练成绩')
        p(c,'优化器只针对训练目标工作，训练贴合增强不要求验证指标同步改善。尤其在 gamma 较大、核影响较局部时，较大 C 可能更强烈迁就局部训练约束，需用保留记录检查这种调整的后果。')
        p(c,'训练 BA 本身也不是被直接最小化的 hinge。因此不能把表中某个 BA 的变化当作对优化器是否成功的唯一判断。',10.0)
    def b(c):
        h(c,'9.2  固定选择规则与家族解释')
        p(c,'线性与 RBF 分别按验证 BA 最大选择，平分取较小 C，再取较小 gamma。本次线性保留 C=1，RBF 保留 C=10、gamma=10；线性 gamma 无效，不作为实际选择量。')
        p(c,'根据验证集做过选择后，其最高成绩含有选择带来的乐观性，不能替代冻结后的测试评价，更不能据一次划分宣布普遍冠军。',10.0)
    columns(d,a,b)

    page(d,'10  同样信息、不同单位：尺度与训练内标准化〔实践 F〕')
    p(d,'仅将 x₁ 乘 100，标签、划分和信息不变。固定 RBF C=1、gamma=0.1，交叉比较是否标准化与是否换单位。该实验检验坐标单位变化的不变性，不是为每套流程重新搜索最佳参数。')
    picture(d,'fig11_scaling','图 11｜单位改变前后的验证决策分数。横轴为原单位分数，纵轴为 x₁ 乘 100 后的分数，虚线为完全一致。a，未标准化流程明显偏离一致线；b，分别在各自训练数据拟合 scaler 后，两套分数仅有浮点差异。两图均由课堂规定的固定参数重新拟合，不能解释为“标准化对所有任务都必然提高成绩”。')
    rows=[]
    for a in R['scaling'].itertuples():
        rows.append(['训练标准化' if a.scaled else '无标准化','原单位' if a.unit=='original' else 'x₁×100',fmt(a.val_balanced_accuracy),int(a.n_sv)])
    table(d,'四种流程的固定参数对照',['预处理','输入单位','验证 BA','SV 数'],rows,[4.1,4.1,5.0,4.0],
          note='最大 |Δf|：无标准化为 '+fmt(R['changes']['False'])+'；训练标准化为 '+f'{R["changes"]["True"]:.3e}'+'。对照只评估单位变化带来的差异，不作最优流程排名。')
    def a(c):
        h(c,'10.1  单位如何进入距离')
        p(c,'原距离平方为 (x₁−u₁)²+(x₂−u₂)²；换单位后变为 10000(x₁−u₁)²+(x₂−u₂)²。第一项被放大一万倍，故同一个 gamma 对应不同的实际相似度。')
        p(c,'若训练均值与标准差也对应变为 100μ₁、100s₁，则 z₁′=(100x₁−100μ₁)/(100s₁)=z₁，所以训练标准化抵消本次正比例变换。')
    def b(c):
        h(c,'10.2  标准化参数也是学出来的')
        p(c,'StandardScaler 使用训练均值与总体式标准差（ddof=0），不是强行把数据变成正态分布。验证和测试只 transform；不能各自在保留集 fit，也不能用全部 310 条估计尺度。')
        p(c,'即使不用标签，全数据 scaler 也利用了保留集分布，构成泄漏。Pipeline 只有在 fit 输入范围正确、交叉验证各训练折内重拟合时，才能保证相应隔离。')
    columns(d,a,b)
    eq(d,[script('z','j'),' = ',frac('xⱼ−μⱼ','sⱼ'),' ,    μⱼ、sⱼ 仅由训练数据估计'],10,text='zⱼ=(xⱼ−μⱼ)/sⱼ，μⱼ与sⱼ只由训练数据估计')

    page(d,'11  验证指标、家族配置与冻结测试流程〔实践 F〕')
    p(d,'以 AB 为正类、NO 为负类，混淆矩阵按 [[TN,FP],[FN,TP]] 解读。敏感度衡量真实 AB 的识别率，特异度衡量真实 NO 的识别率，balanced accuracy（BA）取两者平均。ROC-AUC 使用连续 decision score 排序，不需要把分数当作概率。')
    picture(d,'fig12_evaluation','图 12｜验证集上的错误构成与排序表现。a、b，按家族规则保留的线性与 RBF 配置，混淆矩阵行是真实标签、列是预测标签。c，同一验证集的 ROC。RBF 在阈值 0 下具有较高 BA，线性模型则有较高 AUC，说明固定阈值分类与整体排序评价可以给出不同比较。此图明确是验证结果，不是测试结果。')
    rows=[]
    for family in ['linear','rbf']:
        m=R['manifest']['validation'][family]
        rows.append(['linear C=1' if family=='linear' else 'RBF C=10, γ=10',fmt(m['balanced_accuracy'],4),fmt(m['sensitivity'],4),fmt(m['specificity'],4),fmt(m['roc_auc'],4)])
    table(d,'按验证规则冻结的两组家族配置',['配置','验证 BA','敏感度','特异度','验证 AUC'],rows,[6.2,2.7,2.7,2.7,2.9],
          note='共同条件：两指定输入；训练 scaler；仅原 186 条训练记录拟合；阈值 0；probability=False。预定规则为家族内先最大验证 BA，再较小 C、较小 gamma。')
    eq(d,['Sensitivity=',frac('TP','TP+FN'),' ,   Specificity=',frac('TN','TN+FP'),' ,   BA=',frac('Sensitivity+Specificity','2')],11,text='Sensitivity=TP/(TP+FN)，Specificity=TN/(TN+FP)，BA=(Sensitivity+Specificity)/2')
    def a(c):
        h(c,'11.1  多数类基线与错误解释')
        p(c,'验证集含 42 个 AB、20 个 NO。始终预测 AB，accuracy=42/62≈0.677，敏感度为 1、特异度为 0，BA 仅 0.5。因此只报告 accuracy 会掩盖对 NO 的识别失败。')
        p(c,'本次线性模型漏判 16 个 AB、误报 2 个 NO；RBF 漏判 8 个 AB、误报 4 个 NO。需要并列呈现两类错误，不能把某一指标改善当作所有代价都降低。',10.0)
    def b(c):
        h(c,'11.2  测试回答什么问题')
        p(c,'冻结输入、预处理、参数和解释问题后，才按教师安排打开两个测试开关。测试仍只用原 186 条训练记录拟合，不合并验证；测试后不追加网格、阈值或特征搜索。')
        if R['test'] is None:
            p(c,'本次报告未启动锁定测试评价、未读取测试标签，故不填测试成绩。上述验证结果已参与配置选择，不能充当一次全新的独立测试确认。',10.0)
        else:
            p(c,'用户已确认课堂开放测试，本报告在保存冻结配置后执行一次评价。教师此前已预跑测试，故仍按课程说明视为保留集流程演示，不宣称全新独立科研确认。',10.0)
    columns(d,a,b)
    if R['test'] is not None:
        table(d,'冻结后按课堂安排执行的保留集评价',['家族','TN / FP / FN / TP','accuracy','BA','AUC'],
              [[r.family,f'{r.TN} / {r.FP} / {r.FN} / {r.TP}',fmt(r.accuracy,4),fmt(r.balanced_accuracy,4),fmt(r.roc_auc,4)] for r in R['test'].itertuples()],
              [2.3,6.5,2.8,2.8,2.8],note='测试前已保存配置，不据测试继续调参。有限同源保留结果仍不足以确认新医院表现。')

    page(d,'12  冻结模型的输入扰动与预测稳定性〔扩展 G〕')
    def a(c):
        h(c,'12.1  干预与控制条件')
        p(c,'在验证输入上加入独立高斯噪声，各特征噪声 SD 取训练 SD 的 0%、5%、10%、20%。非零强度各重复 100 次，随机种子为 9；固定模型、scaler、参数、标签和记录身份，不重新拟合。')
    def b(c):
        h(c,'12.2  翻转率与错误率不同')
        p(c,'翻转率统计扰动后预测类别相对原预测改变的比例。翻转可能从对变错，也可能从错变对；原本一直分错但不翻转的记录不会计入。因此稳定性不能替代准确性评价。')
    columns(d,a,b)
    picture(d,'fig13_noise','图 13｜固定家族配置在人工扰动下的表现。a，重复平均预测翻转率；b，重复平均验证 BA，误差条为同一验证集在人工噪声重复中的标准差，不是人群抽样置信区间。0% 强度仅计算一次。当前 RBF 配置在本假设下翻转更多，不说明所有核模型普遍更不稳定。')
    rows=[]
    for i in range(4):
        a=R['noise']['linear'].iloc[i];b=R['noise']['rbf'].iloc[i]
        rows.append([f'{100*a.noise_sd_fraction:g}%',fmt(a.mean_flip_rate,4),fmt(b.mean_flip_rate,4),fmt(a.mean_balanced_accuracy,4),fmt(b.mean_balanced_accuracy,4)])
    table(d,'扰动强度、平均翻转率与平均验证 BA',['噪声 SD','线性翻转率','RBF 翻转率','线性 BA','RBF BA'],rows,[2.4,3.6,3.6,3.8,3.8],
          note='所用线性配置 C=1，RBF 配置 C=10、gamma=10，均按未扰动验证集的既定规则冻结。扰动不改变原标签，也不用于重新选参。')
    def a(c):
        h(c,'12.3  距离为什么提供翻转余量')
        p(c,'对固定线性模型，扰动 δ 使分数改变 wᵀδ，且 |wᵀδ|≤‖w‖‖δ‖。若 ‖δ‖<|f(z)|/‖w‖，该点不会跨过边界。于是最近边界的点通常更容易受小扰动影响。')
        p(c,'RBF 的局部变化还依赖曲线形状和位置，不能直接用分数大小当原空间距离。',10.0)
    def b(c):
        h(c,'12.4  为什么不能直接外推')
        p(c,'噪声分布、独立性和强度都是教学设定。源资料未给真实仪器误差结构，故本实验不能替代测量误差研究，更不能证明对外部医院或不同人群稳定。')
        p(c,'100 次重复只度量人工噪声下的波动，未增加独立患者数。结果应限定为“这两个冻结配置在本扰动条件下”的观察。',10.0)
    columns(d,a,b)

    page(d,'13  讨论、方法选择与可复现性')
    p(d,'本课证据支持一条连续机制链：零错误不能唯一确定边界，几何间隔增加选择原则；支持向量刻画当前解中的有效样本约束；不可分数据需要允许并惩罚违例；对偶表示使内积成为计算核心；核与 gamma 改变特征相似度；尺度、验证与扰动则限制这些机制可以如何被解释。')
    table(d,'机制带来的优势、条件与局限',['机制','优势','需核对的条件与局限'],
          [['间隔与范数控制','给边界提供明确优化原则','距离与特征表示是否合理；训练余量不能保证外部泛化'],
           ['软间隔与 C','重叠数据下仍可作权衡','标签噪声、C 与验证证据；过小 C 可欠拟合，过大 C 可迁就局部约束'],
           ['核技巧与 gamma','表达原空间非线性关系','相似度、尺度与参数是否适合；核训练和多 SV 预测可能昂贵'],
           ['支持向量展开','描述参与当前解的记录','不是患者严重程度或因果解释；冗余 SV 删除后也可能不变']],
          [3.4,5.3,8.5],note='优势必须连同条件陈述。高维或小样本不自动使 SVM 最优；仍需信号、验证和计算资源支持。')
    def a(c):
        h(c,'13.1  面向新任务的选择依据')
        p(c,'至少需要知道样本量、标签定义与重叠程度、输入尺度、相似度是否有任务含义、是否需要概率以及解释要求。若使用非线性核，应先说明何种关系值得表达，再用可靠验证选择参数。')
        p(c,'核 SVM 可能需要大量样本对的相似度计算，预测成本也随 SV 数增加；大样本任务应评估训练、内存与推断成本。若需要概率，应另作不泄漏的校准和校准评价。',10.0)
        h(c,'13.2  当前结果的证据边界')
        p(c,'两个特征用于二维教学，不代表所有可用信息的上限；固定一次同源划分不能代表外部医院。这里不建立因果结论，也不据单一分数批准应用。',10.0)
    def b(c):
        h(c,'13.3  复现范围与数值来源')
        p(c,'本报告使用当前课堂原始 CSV 与原实验函数重算全部训练、验证、几何、尺度和扩展 G。真实拟合结果与解析示意分开标注；四个 hinge 手算、两点对偶例子与 RBF 热图不作为新增患者。')
        v=R['manifest']['versions']
        p(c,f'环境为 Python {v["python"]}、scikit-learn {v["sklearn"]}、NumPy {v["numpy"]}、pandas {v["pandas"]}。SVC 的 tol=10⁻⁷、max_iter=200000；八点几何使用更严格容差。所有预定配置均检查收敛。',10.0)
        p(c,'原函数含旧目录深度假设，仅在内存修正未参与实验的 REPO 路径赋值；课程源文件、数据、标签、算法目标与参数均未修改。输入哈希、冻结配置、完整网格和 CSV 输出随报告保留。',10.0)
    columns(d,a,b)
    h(d,'结论',10.5)
    p(d,'SVM 的核心不是单纯追求零训练错误，而是在合理表示下，通过间隔、训练违例与范数控制学习判别函数。对偶解释样本如何构成解，核技巧解释非线性从何而来；gamma 的局部范围必须连同 C 和尺度理解。受控实验与清楚的评价协议，才使这些公式成为可检验、可解释的方法。',10.0)
    h(d,'参考资料',9.5)
    p(d,'[1] Barreto G, Neto A. Vertebral Column. UCI Machine Learning Repository. DOI: 10.24432/C5K89B. CC BY 4.0。\n[2] 本课课件《SVM 与 Margin》：svm-pbl-intro-with-kernel.pptx，26 页。\n[3] 本课 student-worksheet.md、svm-lab.ipynb、data/README.md 与 experiment-design.md。\n[4] Cortes C, Vapnik V. Support-vector networks. Machine Learning. 1995;20:273–297. DOI: 10.1007/BF00994018。\n[5] scikit-learn. Support Vector Machines; SVC; StandardScaler. scikit-learn.org/stable/modules/svm.html。\n[6] 本课 scripts/lab_utils.py；本次 analysis/run-manifest.json、frozen-configurations.json 与各实验 CSV。',7.7,after=0,color='68727A')
    path=OUT/'SVM_课堂实践完整报告.docx';d.save(path)
    (OUT/'SVM_课堂实践完整报告_文字稿.md').write_text(''.join(TEXT),encoding='utf-8')
    structure={'expected_pages':13,'page_titles':PAGES,'figures':13,'tables':TABLE_COUNT,
        'header_footer':'Removed entirely, including rules, dates, running text and page numbers.',
        'actual_rerun':True,'test_opened':R['manifest']['test_opened'],
        'worksheet_coverage':{'A':[1],'B':[2],'C':[3,4,5],'D':[6],'E':[7,8,9],'F':[10,11],'G':[12],'synthesis':[13]}}
    (OUT/'analysis/report-structure.json').write_text(json.dumps(structure,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path);print('Logical pages:',len(PAGES),'Tables:',TABLE_COUNT)
    return d


if __name__=='__main__':
    build()
