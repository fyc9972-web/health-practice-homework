"""Build the revision matched to the supplied SVM report's academic layout."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.tmp'/'ensemble_report_deps'))
import re
import json
import base64
import html
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pandas as pd
import markdown
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT=ROOT/'results'/'ensemble-report'
RESULTS=ROOT/'results/ensemble-classroom-report'/'results'
STEM='集成学习_课堂实践完整报告'
LABEL={'single_tree':'单树','bagging':'Bagging','random_forest':'RF','adaboost':'AdaBoost',
       'gradient_boosting':'GB','logistic':'LR','rbf_svm':'RBF-SVM'}
MATHNS='http://www.w3.org/1998/Math/MathML'


def mi(t):return '<mi>'+html.escape(t)+'</mi>'
def mn(t):return '<mn>'+str(t)+'</mn>'
def mo(t):return '<mo>'+html.escape(t)+'</mo>'
def tx(t):return '<mtext>'+html.escape(t if t.strip() else '\u2003')+'</mtext>'
def row(*t):return '<mrow>'+''.join(t)+'</mrow>'
def frac(a,b):return '<mfrac>'+a+b+'</mfrac>'
def sub(a,b):return '<msub>'+a+b+'</msub>'
def sup(a,b):return '<msup>'+a+b+'</msup>'
def ss(a,b,c):return '<msubsup>'+a+b+c+'</msubsup>'
def par(a):return row(mo('('),a,mo(')'))
def eq(a,b):return row(a,mo('='),b)
def bar(a):return '<mover accent="true">'+a+mo('¯')+'</mover>'
def hat(a):return '<mover accent="true">'+a+mo('^')+'</mover>'
def sigma(low,high):return '<munderover>'+mo('∑')+low+high+'</munderover>'
def sqrt(a):return '<msqrt>'+a+'</msqrt>'
def math(a):return f'<math xmlns="{MATHNS}" display="block">'+a+'</math>'


def equations():
    p=mi('p');G=mi('G');n=mi('n');t=mi('t');B=mi('B');R=mi('R')
    dist=row(mn(1),mo('−'),frac(mn(1),n))
    gini=eq(row(G,par(t)),row(mn(1),mo('−'),sigma(eq(mi('k'),mn(0)),mn(1)),sup(row(sub(p,mi('k')),par(t)),mn(2))))
    split=eq(row(mi('Δ'),G),row(G,par(t),mo('−'),frac(sub(n,mi('L')),n),G,par(sub(t,mi('L'))),mo('−'),frac(sub(n,mi('R')),n),G,par(sub(t,mi('R')))))
    leaf=eq(row(hat(p),par(row(mi('y'),mo('='),mn(1),mo('|'),mi('L')))),frac(sub(mi('N'),mn(1)),row(sub(mi('N'),mn(0)),mo('+'),sub(mi('N'),mn(1)))))
    voting=eq(row(bar(p),par(mi('x'))),row(frac(mn(1),B),sigma(eq(mi('b'),mn(1)),B),sub(p,mi('b')),par(mi('x'))))
    var=eq(row(tx('Var'),par(bar(mi('f')))),row(mi('ρ'),sup(mi('σ'),mn(2)),mo('+'),frac(row(par(row(mn(1),mo('−'),mi('ρ'))),sup(mi('σ'),mn(2))),B)))
    bootstrap=row(eq(sub(mi('P'),tx('OOB')),sup(par(dist),n)),mo(','),tx('   '),eq(row(mi('E'),mo('['),frac(mi('U'),n),mo(']')),row(mn(1),mo('−'),sup(par(dist),n))))
    pbar=sub(bar(p),mi('i'));pri=sub(p,row(mi('r'),mi('i')))
    stability=row(eq(pbar,row(frac(mn(1),R),sigma(eq(mi('r'),mn(1)),R),pri)),mo(','),tx('   '),eq(sub(tx('SD'),mi('i')),sqrt(row(frac(mn(1),R),sigma(eq(mi('r'),mn(1)),R),sup(par(row(pri,mo('−'),pbar)),mn(2))))))
    eps=sub(mi('ε'),t);alpha=sub(mi('α'),t);wi=ss(mi('w'),mi('i'),t)
    ada=[eq(alpha,row(tx('ln'),frac(row(mn(1),mo('−'),eps),eps))),
         eq(ss(mi('w'),mi('i'),row(t,mo('+'),mn(1))),frac(row(wi,tx('exp'),par(row(alpha,mi('I'),mo('['),sub(mi('h'),t),par(sub(mi('x'),mi('i'))),mo('≠'),sub(mi('y'),mi('i')),mo(']')))),sub(mi('Z'),t)))]
    gradient=row(eq(p,frac(mn(1),row(mn(1),mo('+'),sup(mi('e'),row(mo('−'),mi('F')))))),mo(','),tx('   '),
                 eq(row(sub(mi('F'),t),par(mi('x'))),row(sub(mi('F'),row(t,mo('−'),mn(1))),par(mi('x')),mo('+'),mi('η'),sub(mi('h'),t),par(mi('x')))))
    loss=[eq(mi('ℓ'),row(mo('−'),mi('y'),tx('ln'),p,mo('−'),par(row(mn(1),mo('−'),mi('y'))),tx('ln'),par(row(mn(1),mo('−'),p)))),
          eq(mi('r'),row(mo('−'),frac(row(mo('∂'),mi('ℓ')),row(mo('∂'),mi('F'))),mo('='),mi('y'),mo('−'),p))]
    importance=eq(sub(mi('I'),mi('j')),row(sub(tx('AUC'),tx('base')),mo('−'),sub(tx('AUC'),row(tx('perm'),par(mi('j'))))))
    metrics=row(eq(tx('TPR'),frac(tx('TP'),row(tx('TP'),mo('+'),tx('FN')))),mo(','),tx('  '),
                eq(tx('TNR'),frac(tx('TN'),row(tx('TN'),mo('+'),tx('FP')))),mo(','),tx('  '),
                eq(tx('BA'),frac(row(tx('TPR'),mo('+'),tx('TNR')),mn(2))))
    std=eq(sub(mi('z'),mi('j')),frac(row(sub(mi('x'),mi('j')),mo('−'),sub(mi('μ'),mi('j'))),sub(mi('s'),mi('j'))))
    raws=[('gini',gini,'G(t)=1−Σₖpₖ(t)²'),('split',split,'ΔG=G(t)−(nᴸ/n)G(tᴸ)−(nᴿ/n)G(tᴿ)'),
          ('leaf',leaf,'p̂(y=1|L)=N₁/(N₀+N₁)'),('voting',voting,'p̄(x)=(1/B)Σᵦpᵦ(x)'),
          ('variance',var,'Var(f̄)=ρσ²+(1−ρ)σ²/B'),('bootstrap',bootstrap,'P_OOB=(1−1/n)ⁿ；E[U/n]=1−(1−1/n)ⁿ'),
          ('stability',stability,'p̄ᵢ=(1/R)Σᵣpᵣᵢ；SDᵢ=√[(1/R)Σᵣ(pᵣᵢ−p̄ᵢ)²]'),
          ('adaboost',ada,'αₜ=ln[(1−εₜ)/εₜ]；wᵢᵗ⁺¹=wᵢᵗ exp(αₜI[hₜ(xᵢ)≠yᵢ])/Zₜ'),
          ('gradient',gradient,'p=1/(1+exp(−F))；Fₜ(x)=Fₜ₋₁(x)+ηhₜ(x)'),
          ('logloss',loss,'ℓ=−y ln(p)−(1−y)ln(1−p)；r=−∂ℓ/∂F=y−p'),
          ('importance',importance,'Iⱼ=AUC_base−AUC_perm(j)'),
          ('metrics',metrics,'TPR=TP/(TP+FN)；TNR=TN/(TN+FP)；BA=(TPR+TNR)/2'),
          ('standardize',std,'zⱼ=(xⱼ−μⱼ)/sⱼ；μⱼ、sⱼ仅由训练部分估计')]
    return {key:{'number':i,'rows':item if isinstance(item,list) else [item],'text':text} for i,(key,item,text) in enumerate(raws,1)}


EQ=equations()


def table(head,rows):
    return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+
                     ['| '+' | '.join(map(str,r))+' |' for r in rows])


def read(name,file):return pd.read_csv(RESULTS/name/file)


def populate():
    s=(OUT/'article.source.md').read_text(encoding='utf-8');values={}
    values['T1']=table(['数据','训练（正类）','验证（正类）','测试记录数','开发 CV'],
        [['WDBC','341（127）','114（43）','114','分层五折'],['CTG','1,279（108）','424（34）','423','录音分组五折']])
    a,b=read('wdbc','tree-depth.csv'),read('ctg','tree-depth.csv')
    values['T2']=table(['最大深度','WDBC 训练准确率','WDBC 验证准确率','CTG 训练准确率','CTG 验证准确率'],
        [[depth,f'{a.iloc[i].train_accuracy:.4f}',f'{a.iloc[i].accuracy:.4f}',f'{b.iloc[i].train_accuracy:.4f}',f'{b.iloc[i].accuracy:.4f}'] for i,depth in enumerate(['1','2','3','4','不限'])])
    values['T3']=table(['样本','真值','硬投票','平均正类概率','软投票'],[['A',1,1,'0.650000',1],['B',0,1,'0.483333',0],['C',1,1,'0.633333',1],['D',0,0,'0.366667',0]])
    sim=pd.read_csv(RESULTS/'bootstrap-simulation.csv')
    values['T4']=table(['n','不同记录比例均值','袋外比例均值','袋外比例精确期望'],
        [[n,f'{d.unique_fraction.mean():.6f}',f'{d.oob_fraction.mean():.6f}',f'{d.expected_oob.iloc[0]:.6f}'] for n,d in sim.groupby('n')])
    values['T5']=table(['数据','全部候选：验证 AUC','sqrt 候选：验证 AUC','差值（sqrt−全部）'],
        [[name.upper(),f'{(d:=read(name,"matched-feature-randomization.csv")).iloc[0].roc_auc:.6f}',f'{d.iloc[1].roc_auc:.6f}',f'{d.iloc[1].roc_auc-d.iloc[0].roc_auc:+.6f}'] for name in ['wdbc','ctg']])
    rows=[]
    for name in ['wdbc','ctg']:
        for _,r in read(name,'prediction-stability-row.csv').iterrows():rows.append([name.upper(),LABEL[r.model],f'{r.prediction_sd_mean:.6f}',f'{r.class_flip_rate:.4%}'])
    values['T6']=table(['数据','模型','平均预测 SD','类别翻转率'],rows)
    rows=[]
    for name in ['wdbc','ctg']:
        for _,r in read(name,'adaboost-weight-trace.csv').head(3).iterrows():rows.append([name.upper(),int(r.stage),int(r.wrong_count),f'{r.wrong_mass_before:.4f}',f'{r.wrong_mass_after:.4f}'])
    values['T7']=table(['数据','轮次','错分记录数','更新前权重占比','更新后权重占比'],rows)
    rows=[]
    for name in ['wdbc','ctg']:
        d=read(name,'boosting-curves.csv')
        for _,r in d[(d.learning_rate==.1)&d.stage.isin([50,100,500])].iterrows():rows.append([name.upper(),int(r.stage),f'{r.train_log_loss:.6f}',f'{r.validation_log_loss:.6f}',f'{r.validation_auc:.6f}'])
    values['T8']=table(['数据','轮数','训练 log-loss','验证 log-loss','验证 AUC'],rows)
    d=read('wdbc','feature-importance.csv').set_index('feature');rows=[]
    for f in ['worst perimeter','worst area','worst radius']:
        r=d.loc[f];rows.append([f,f'{r.impurity_importance:.6f}',f'{r.permutation_auc_drop_mean:.6f}',f'{r.permutation_auc_drop_sd:.6f}'])
    values['T9']=table(['特征','不纯度重要性','置换 AUC 降幅','置换 SD'],rows)
    a=read('wdbc','cross-validation.csv').set_index('model');b=read('ctg','cross-validation.csv').set_index('model')
    values['T10']=table(['模型','WDBC AUC±SD','CTG AUC±SD','CTG AP','CTG BA'],
        [[label,f'{a.loc[m,"roc_auc_mean"]:.4f}±{a.loc[m,"roc_auc_sd"]:.4f}',f'{b.loc[m,"roc_auc_mean"]:.4f}±{b.loc[m,"roc_auc_sd"]:.4f}',f'{b.loc[m,"ap_mean"]:.4f}',f'{b.loc[m,"balanced_accuracy_mean"]:.4f}'] for m,label in LABEL.items()])
    d=read('ctg','model-comparison.csv').set_index('model')
    values['T11']=table(['模型','TP','FN','FP','TN','敏感度','BA'],
        [[LABEL[m],*[int(d.loc[m,c]) for c in ['tp','fn','fp','tn']],f'{d.loc[m,"sensitivity"]:.4f}',f'{d.loc[m,"balanced_accuracy"]:.4f}'] for m in ['random_forest','logistic']])
    a=read('ctg','prediction-stability-row.csv').set_index('model');b=read('ctg','prediction-stability-recording.csv').set_index('model')
    values['T12']=table(['模型','行抽样 SD','录音抽样 SD','行抽样翻转率','录音抽样翻转率'],
        [[LABEL[m],f'{a.loc[m,"prediction_sd_mean"]:.6f}',f'{b.loc[m,"prediction_sd_mean"]:.6f}',f'{a.loc[m,"class_flip_rate"]:.2%}',f'{b.loc[m,"class_flip_rate"]:.2%}'] for m in ['single_tree','bagging','random_forest']])
    for key,value in values.items():s=s.replace('{{'+key+'}}',value)
    assert '{{' not in s
    return s


CSS=r'''
@font-face{font-family:ReportSong;src:local('SimSun'),local('宋体')}
@font-face{font-family:ReportHei;src:local('Noto Sans SC'),local('Microsoft YaHei')}
*{box-sizing:border-box}body{margin:0;background:#e8ecef;color:#4c5257;font-family:'Times New Roman',ReportSong,SimSun,serif;font-size:10.4pt;line-height:1.47}
.page{position:relative;width:210mm;height:297mm;margin:22px auto;background:#fff;padding:17.5mm 19mm 17mm;box-shadow:0 2px 15px #142a3a16;break-after:page;overflow:visible}
.page-content{width:100%;height:100%;position:relative}.page:last-child{break-after:auto}.pageno{position:absolute;bottom:7mm;right:19mm;color:#9aa2a8;font:7pt 'Times New Roman',serif}
h1,h2,h3{font-family:ReportHei,'Microsoft YaHei',sans-serif;color:#262e34;font-weight:750;line-height:1.45}h1{font-size:22pt;margin:0 0 5pt}h2{font-size:12.5pt;margin:0 0 10pt}h3{font-size:10.2pt;margin:3pt 0 5pt}
p{margin:0 0 7pt;text-align:justify;overflow-wrap:anywhere;orphans:2;widows:2}.subtitle{font-size:11.5pt;line-height:1.4;margin-bottom:5pt;font-family:ReportHei,sans-serif;color:#56626a}.english{font-size:10pt;font-style:italic;color:#7d8890;margin-bottom:10pt}.abstract{font-size:9pt;line-height:1.5;margin-bottom:7pt}.keywords{font-size:8pt;color:#85919a;margin-bottom:14pt}
.columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:7mm;margin:0 0 5pt;align-items:start}.col>*:last-child{margin-bottom:0}.col h2{font-size:11pt;margin:3pt 0 7pt}.col{min-width:0}
figure{margin:8pt 0 7pt}figure img{display:block;width:100%;height:auto}.caption{font-size:7.8pt;line-height:1.46;color:#7c858b;margin-top:6pt;text-align:justify}.table-title{font:750 8.3pt/1.4 ReportHei,sans-serif;margin:8pt 0 4pt;color:#303b42}
table{width:100%;border-collapse:collapse;border-top:1.2pt solid #30404a;border-bottom:1.1pt solid #30404a;table-layout:auto;font-size:8.2pt;line-height:1.32;margin-bottom:4pt}thead{border-bottom:.55pt solid #56636d}th{font-family:ReportHei,sans-serif;font-weight:700;color:#2e383f;padding:3.5pt 4pt}td{padding:3.3pt 4pt;text-align:center;color:#55616b;font-variant-numeric:tabular-nums}th:first-child,td:first-child{text-align:left}tr{break-inside:avoid}thead{display:table-header-group}th,td{border-left:0;border-right:0;background:transparent}
.note{font-size:7.7pt;line-height:1.4;color:#8a939a;margin:3pt 0 8pt}.equation{position:relative;display:flex;align-items:center;justify-content:center;gap:9pt;padding:4pt 25pt 5pt;margin:3pt 0 6pt;min-height:24pt;color:#252b30;break-inside:avoid}.eq-body{display:flex;flex-direction:column;gap:5pt}.eq-no{position:absolute;right:2pt;font-size:8pt;color:#7d878e}math{font-family:'Cambria Math','STIX Two Math',serif;font-size:11.3pt;math-style:normal;line-height:1.1}
code{font:8.4pt 'Times New Roman',ReportSong,serif;color:inherit;background:transparent;padding:0}strong{font-weight:700;color:#303a42}.references{font-size:7.6pt;line-height:1.42}.references p{margin-bottom:4pt}.references h3{font-size:10pt}.page[data-page='11'] table{font-size:7.7pt}.page[data-page='11'] td,.page[data-page='11'] th{padding:2.8pt 3pt}.page[data-page='9'] .columns{font-size:9.8pt;line-height:1.42}.page[data-page='9'] .caption{font-size:7.4pt}.page[data-page='9'] figure{margin-top:5pt}.page[data-page='9'] td{padding:2.7pt 3pt}.page[data-page='9'] .equation{padding-top:1pt;padding-bottom:2pt;margin-bottom:3pt}
@page{size:A4;margin:0}@media print{body{background:#fff}.page{margin:0;box-shadow:none;overflow:visible}.pageno{display:block}a{color:inherit;text-decoration:none}}
.page[data-page='11'] .table-title{margin-top:6pt}
@media screen and (max-width:820px){body{background:#fff}.page{margin:0;width:100%;height:auto;min-height:297mm;padding:24px;box-shadow:none;border-bottom:1px solid #ddd}.page-content{height:auto}.columns{gap:22px}.pageno{display:none}h1{font-size:25px}}
'''


def convert_markdown(text):
    text=re.sub(r'^:::equation (\w+)\s*$',lambda m:render_equation(m.group(1)),text,flags=re.M)
    def cols(m):
        parts=m.group(1).split('\n|||\n');assert len(parts)==2
        return '<div class="columns">'+''.join('<div class="col">'+convert_markdown(p)+'</div>' for p in parts)+'</div>'
    text=re.sub(r':::columns\n(.*?)\n:::',cols,text,flags=re.S)
    output=markdown.markdown(text,extensions=['tables','fenced_code'])
    output=re.sub(r'<p><img alt="([^"]*)" src="([^"]*)"\s*/?></p>\s*<p>(图 \d+｜.*?)</p>',render_figure,output,flags=re.S)
    output=re.sub(r'<p>(表 \d+｜.*?)</p>',r'<p class="table-title">\1</p>',output,flags=re.S)
    output=re.sub(r'<p>(注：.*?)</p>',r'<p class="note">\1</p>',output,flags=re.S)
    return output


def render_equation(key):
    value=EQ[key]
    return '<div class="equation"><div class="eq-body">'+''.join(math(item) for item in value['rows'])+f'</div><span class="eq-no">({value["number"]})</span></div>'


def render_figure(m):
    alt,relative,caption=m.groups();svg=(OUT/relative).read_bytes()
    src='data:image/svg+xml;base64,'+base64.b64encode(svg).decode('ascii')
    return f'<figure><img alt="{html.escape(alt)}" src="{src}"><figcaption class="caption">{caption}</figcaption></figure>'


def build_html(source):
    pages=[]
    for index,text in enumerate(re.split(r'<!-- page: \d+ -->',source)[1:],1):
        content=convert_markdown(text)
        if index==1:
            content=content.replace('<p>基于 WDBC','<p class="subtitle">基于 WDBC',1)
            content=content.replace('<p>Sampling,','<p class="english">Sampling,',1)
            content=content.replace('<p>摘要','<p class="abstract">摘要',1).replace('<p>关键词','<p class="keywords">关键词',1)
        if index==14:content=content.replace('<h3>参考资料</h3>','<div class="references"><h3>参考资料</h3>')+'</div>'
        pages.append(f'<section class="page" data-page="{index}"><div class="page-content">{content}</div><span class="pageno">{index}</span></section>')
    assert len(pages)==14
    assert sum(p.count('<figure>') for p in pages)==12
    js="""<script>document.fonts.ready.then(()=>{setTimeout(()=>{const a=[...document.querySelectorAll('.page')].map(p=>{const c=p.querySelector('.page-content');return{page:+p.dataset.page,available:c.clientHeight,used:c.scrollHeight,overflow:c.scrollHeight-c.clientHeight}});const e=document.createElement('pre');e.id='layout-check';e.style.display='none';e.textContent=JSON.stringify(a);document.body.append(e)},100)});</script>"""
    document='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>集成学习的抽样、聚合与顺序修正机制</title><style>'+CSS+'</style></head><body>'+''.join(pages)+js+'</body></html>'
    (OUT/'index.html').write_text(document,encoding='utf-8')
    return pages


def set_font(style,size,east='宋体',latin='Times New Roman'):
    style.font.name=latin;style.font.size=Pt(size)
    rpr=style.element.get_or_add_rPr();rfonts=rpr.find(qn('w:rFonts'))
    if rfonts is None:rfonts=OxmlElement('w:rFonts');rpr.insert(0,rfonts)
    rfonts.set(qn('w:eastAsia'),east)


def inline(p,text):
    for token in re.split(r'(\*\*.*?\*\*|`[^`]+`)',text):
        if token.startswith('**') and token.endswith('**'):p.add_run(token[2:-2]).bold=True
        elif token.startswith('`') and token.endswith('`'):p.add_run(token[1:-1])
        elif token:p.add_run(token)


def mml_to_omml(element):
    tag=element.tag.split('}')[-1];children=list(element)
    if tag in ['math','mrow']:
        group=[]
        for c in children:group.extend(mml_to_omml(c))
        return group
    if tag in ['mi','mn','mo','mtext']:
        r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=element.text or '';r.append(t);return [r]
    patterns={'mfrac':('m:f',['m:num','m:den']),'msub':('m:sSub',['m:e','m:sub']),
              'msup':('m:sSup',['m:e','m:sup']),'msubsup':('m:sSubSup',['m:e','m:sub','m:sup'])}
    if tag in patterns:
        name,slots=patterns[tag];node=OxmlElement(name)
        for c,slot in zip(children,slots):
            part=OxmlElement(slot)
            for obj in mml_to_omml(c):part.append(obj)
            node.append(part)
        return [node]
    if tag=='msqrt':
        rad=OxmlElement('m:rad');pr=OxmlElement('m:radPr');hide=OxmlElement('m:degHide');hide.set(qn('m:val'),'1');pr.append(hide);rad.append(pr)
        rad.append(OxmlElement('m:deg'));part=OxmlElement('m:e')
        for c in children:
            for obj in mml_to_omml(c):part.append(obj)
        rad.append(part);return [rad]
    if tag=='mover':
        acc=OxmlElement('m:acc');pr=OxmlElement('m:accPr');ch=OxmlElement('m:chr');ch.set(qn('m:val'),children[1].text or '̂');pr.append(ch);acc.append(pr)
        part=OxmlElement('m:e')
        for obj in mml_to_omml(children[0]):part.append(obj)
        acc.append(part);return [acc]
    if tag=='munderover':
        node=OxmlElement('m:nary');pr=OxmlElement('m:naryPr');ch=OxmlElement('m:chr');ch.set(qn('m:val'),children[0].text or '∑');pr.append(ch);node.append(pr)
        for c,name in zip(children[1:],['m:sub','m:sup']):
            part=OxmlElement(name)
            for obj in mml_to_omml(c):part.append(obj)
            node.append(part)
        node.append(OxmlElement('m:e'));return [node]
    raise ValueError('Unsupported MathML '+tag)


def no_borders(table):
    borders=OxmlElement('w:tblBorders')
    for name in ['top','left','bottom','right','insideH','insideV']:
        item=OxmlElement('w:'+name);item.set(qn('w:val'),'nil');borders.append(item)
    table._tbl.tblPr.append(borders)


def render_word_blocks(container,text):
    lines=text.strip().splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line==':::columns':
            block=[];i+=1
            while lines[i].strip()!=':::':block.append(lines[i]);i+=1
            parts='\n'.join(block).split('\n|||\n')
            grid=container.add_table(rows=1,cols=2);no_borders(grid)
            for cell,part in zip(grid.rows[0].cells,parts):
                render_word_blocks(cell,part)
            i+=1;continue
        if line.startswith(':::equation '):
            val=EQ[line.split()[-1]]
            for j,m in enumerate(val['rows']):
                p=container.add_paragraph();p.alignment=1;p.paragraph_format.space_after=Pt(3)
                omath=OxmlElement('m:oMath')
                for obj in mml_to_omml(ET.fromstring(math(m))):omath.append(obj)
                p._p.append(omath)
                if j==len(val['rows'])-1:p.add_run(f'  ({val["number"]})').font.size=Pt(8)
            i+=1;continue
        match=re.match(r'!\[(.*?)\]\((.*?)\)',line)
        if match:
            p=container.add_paragraph();p.alignment=1;p.paragraph_format.keep_with_next=True
            p.add_run().add_picture(str((OUT/match.group(2)).with_suffix('.png')),width=Cm(17.1));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in row):rows.append(row)
                i+=1
            t=container.add_table(rows=len(rows),cols=len(rows[0]));no_borders(t)
            for ri,row in enumerate(rows):
                for ci,value in enumerate(row):
                    cell=t.cell(ri,ci);p=cell.paragraphs[0];p.alignment=0 if ci==0 else 1
                    p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(2);p.paragraph_format.line_spacing=1.0
                    inline(p,value)
                    for run in p.runs:run.font.size=Pt(8);run.bold=(ri==0)
                    if ri==0 or ri==len(rows)-1:
                        borders=OxmlElement('w:tcBorders')
                        if ri==0:
                            for side in ['top','bottom']:
                                border=OxmlElement('w:'+side);border.set(qn('w:val'),'single');border.set(qn('w:sz'),'7' if side=='top' else '4');border.set(qn('w:color'),'34424B');borders.append(border)
                        else:
                            border=OxmlElement('w:bottom');border.set(qn('w:val'),'single');border.set(qn('w:sz'),'7');border.set(qn('w:color'),'34424B');borders.append(border)
                        cell._tc.get_or_add_tcPr().append(borders)
            continue
        heading=re.match(r'^(#{1,3}) (.+)',line)
        if heading:
            level=len(heading.group(1))-1;p=container.add_paragraph(style='Title' if level==0 else f'Heading {level}');inline(p,heading.group(2))
        else:
            style='Normal'
            if line.startswith('图 '):style='Academic Caption'
            elif line.startswith('表 '):style='Academic Table Title'
            elif line.startswith('注：'):style='Academic Note'
            elif line.startswith('摘要'):style='Academic Abstract'
            elif line.startswith('关键词'):style='Academic Note'
            elif line.startswith('Sampling,'):style='Academic English'
            elif line.startswith('基于 WDBC'):style='Academic Subtitle'
            p=container.add_paragraph(style=style);inline(p,line)
        i+=1


def build_word(source):
    doc=Document();sec=doc.sections[0];sec.page_width,sec.page_height=Cm(21),Cm(29.7)
    sec.top_margin=sec.bottom_margin=Cm(1.65);sec.left_margin=sec.right_margin=Cm(1.9)
    set_font(doc.styles['Normal'],10.2);doc.styles['Normal'].font.color.rgb=RGBColor.from_string('4C5257')
    doc.styles['Normal'].paragraph_format.line_spacing=1.15;doc.styles['Normal'].paragraph_format.space_after=Pt(5)
    for name,size in [('Title',22),('Heading 1',12.5),('Heading 2',10.2)]:
        set_font(doc.styles[name],size,east='黑体');doc.styles[name].font.color.rgb=RGBColor.from_string('262E34')
        doc.styles[name].paragraph_format.space_before=Pt(4);doc.styles[name].paragraph_format.space_after=Pt(6)
    for name,size in [('Academic Caption',7.8),('Academic Note',7.5),('Academic Abstract',9),('Academic Table Title',8.5),('Academic English',10),('Academic Subtitle',11.5)]:
        st=doc.styles.add_style(name,1);set_font(st,size);st.paragraph_format.line_spacing=1.08;st.paragraph_format.space_after=Pt(5)
        if name in ['Academic Caption','Academic Note','Academic English']:st.font.color.rgb=RGBColor.from_string('7D8890')
        if name=='Academic English':st.font.italic=True
        if name=='Academic Table Title':st.font.bold=True;st.paragraph_format.keep_with_next=True
    for i,text in enumerate(re.split(r'<!-- page: \d+ -->',source)[1:]):
        if i:doc.add_page_break()
        render_word_blocks(doc,text)
    doc.core_properties.title='集成学习的抽样、聚合与顺序修正机制';doc.core_properties.author=''
    doc.core_properties.subject='WDBC 与 CTG 课堂实践受控实验报告'
    doc.save(OUT/(STEM+'.docx'))


def browser_command(mode):
    browser=Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    cmd=[str(browser),'--headless','--disable-gpu','--no-sandbox','--disable-background-networking','--disable-sync','--no-first-run','--no-default-browser-check',
         '--user-data-dir='+str(ROOT/'.tmp'/'ensemble_academic_browser')]
    if mode=='pdf':cmd+=['--no-pdf-header-footer','--print-to-pdf='+str(OUT/'Ensemblelesson_9.pdf')]
    elif mode=='check':cmd+=['--window-size=1200,1500','--dump-dom','--virtual-time-budget=2500']
    else:cmd+=['--window-size=1100,1200','--hide-scrollbars','--force-device-scale-factor=1','--screenshot='+str(OUT/'review'/'web-preview.png')]
    cmd.append((OUT/'index.html').as_uri());return cmd


def browser(mode):
    result=subprocess.run(browser_command(mode),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=50,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[-1500:])
    if mode=='check':
        dom=result.stdout.decode('utf-8',errors='replace');match=re.search(r'<pre id="layout-check"[^>]*>(.*?)</pre>',dom,re.S)
        if not match:raise RuntimeError('Layout measurement did not complete')
        data=json.loads(html.unescape(match.group(1)));(OUT/'review'/'layout-check.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps(data,indent=2))
    else:print('Browser output ready:',mode)


def main():
    (OUT/'review').mkdir(exist_ok=True)
    if '--pdf' in sys.argv:browser('pdf');return
    if '--check-layout' in sys.argv:browser('check');return
    if '--screenshot' in sys.argv:browser('screenshot');return
    source=populate();build_html(source);build_word(source)
    plain=re.sub(r'^:::equation (\w+)\s*$',lambda m:'> '+EQ[m.group(1)]['text']+f'　（{EQ[m.group(1)]["number"]}）',source,flags=re.M)
    plain=re.sub(r'^:::columns\s*$|^:::\s*$|^\|\|\|\s*$','',plain,flags=re.M)
    plain=re.sub(r'<!-- page: \d+ -->','',plain)
    (OUT/(STEM+'_文字稿.md')).write_text(plain.strip()+'\n',encoding='utf-8')
    print('Revised HTML and Word ready; pages: 14; figures: 12; equation groups:',len(EQ))


if __name__=='__main__':main()
