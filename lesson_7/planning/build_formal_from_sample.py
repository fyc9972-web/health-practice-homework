"""Expand the approved HTML/PDF sample using its original typography and layout."""
from pathlib import Path
from html import escape, unescape
import ast
import csv
import json
import re
import subprocess
import sys
from copy import deepcopy

from journal_report_content import TITLE, SUBTITLE, ABSTRACT, KEYWORDS, PAGES, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/journal-formal'
OUT.mkdir(parents=True, exist_ok=True)
QA = ROOT / '.tmp/journal-formal'
QA.mkdir(parents=True, exist_ok=True)

def assignment(path, name):
    tree = ast.parse(path.read_text('utf-8'))
    for item in tree.body:
        if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in item.targets):
            return ast.literal_eval(item.value)
    raise KeyError(name)

css = assignment(ROOT/'planning/build_journal_sample.py', 'css')
eqs = assignment(ROOT/'planning/build_journal_full.py', 'equations')

# The original approved sample CSS remains authoritative. These rules only add
# missing report elements and control their semantic spacing, not its type scale.
css += '''
.content h1{margin-bottom:2mm}.content>figure{margin-top:4mm}
.equation{font-size:9.5pt;white-space:normal;overflow-wrap:normal}
.equation.long{font-size:9pt}.fraction{display:inline-flex;flex-direction:column;vertical-align:middle;text-align:center;line-height:1.15;margin:0 1mm}
.fraction>span:first-child{border-bottom:.5pt solid currentColor;padding:0 .6mm .8mm}.fraction>span:last-child{padding-top:.8mm}
.thought{color:#24445C}.table-caption{font-size:7.7pt;color:#44515D;margin:3mm 0 1mm;line-height:1.52}
.refs p{font-size:7.5pt;line-height:1.55;margin:0 0 1.3mm;text-align:left}
.full-heading{font-family:SimHei;font-size:10.8pt;color:#1F3444;margin:4mm 0 2mm}
.table-note{font-size:7.3pt;color:#62707A;line-height:1.5;margin:1mm 0 0}
.comparison td{vertical-align:top}.comparison th:nth-child(1){width:19%}
.page:not(:first-child) h1{font-size:16.5pt;margin-top:5mm}
'''

pages = []
intro = deepcopy(PAGES[0])
intro['blocks'] = intro['blocks'][:8]
intro['first'] = True
intro['heading'] = TITLE
pages.append(intro)

estimation = {
    'heading':'Logistic 回归：怎样学习、怎样解释',
    'name':'训练目标与条件解释',
    'deck':'从真实标签的概率出发，连接似然、交叉熵、正则化与优势比。',
    'blocks':deepcopy(PAGES[0]['blocks'][8:]),
    'table':'comparison',
    'table_caption':'表 1 | 课堂四个比较对象的建模对象与参照作用。QDA 用于说明放松共享协方差假设的后果，不属于本课四个主要比较对象。',
}
estimation['blocks'][1:1] = [
    ('p','对一名真实患病者，模型分配给“患病”的概率越大越好；对真实未患病者，则希望分配给“未患病”的概率越大。训练时把每个人真实类别对应的概率相乘，得到条件似然；取负对数后，相乘变相加，得到式（3）。'),
    ('p','例如三人的真实标签依次为 1、0、1，模型预测患病概率依次为 0.9、0.2、0.8。真实类别对应的概率是 0.9、1−0.2、0.8，乘积为 0.576。这里 0.2 是第二人的预测患病概率；因第二人实际未患病，所以使用 0.8。'),
]
pages.append(estimation)
pages.extend(deepcopy(PAGES[1:]))
pages[3]['table_caption']=pages[3]['table_caption'].replace('表 1','表 2')
pages[4]['table_caption']=pages[4]['table_caption'].replace('表 2','表 3')
pages[5]['table_caption']=pages[5]['table_caption'].replace('表 3','表 4')
pages[5]['blocks']=[(k,t.replace('表 3','表 4')) for k,t in pages[5]['blocks']]
pages[3]['compact']=True
pages[3]['blocks']=[(k,('课程文字描述“无缺失”，但当前 CSV 的 ca、thal、slope 缺失率分别为 67.0%、55.9%、38.1%。填补只能支持计算，不会恢复真实值，也不能自动消除缺失偏倚。高缺失变量的保留、敏感性分析和解释均需有依据。' if t.startswith('课程文字描述') else t)) for k,t in pages[3]['blocks']]

# Give ranking/probability assessment and action costs their own pages rather
# than compressing the sample's body type or allowing a figure into the footer.
evaluation=pages[4]
cut=next(i for i,(k,t) in enumerate(evaluation['blocks']) if k=='h2' and t.startswith('8 '))
decisions={
    'name':'阈值选择与行动代价',
    'heading':'从预测概率走向有依据的行动',
    'deck':'概率告诉我们风险，阈值表达漏诊与误报之间的取舍。',
    'blocks':evaluation['blocks'][cut:],
    'figure':evaluation.pop('figure'),
    'caption':evaluation.pop('caption'),
    'table':'decisions',
    'table_caption':'表 4 | 同一批样本上降低阈值的示意演算。数值用于说明代价取舍，不是课堂模型实测结果。',
}
evaluation['blocks']=evaluation['blocks'][:cut]
evaluation['heading']='模型评价：先区分排序与概率质量'
decisions['blocks'].insert(-1,('p','若决定按阳性处理，错误只发生在此人实际阴性时，期望成本为 1−p；若决定按阴性处理，漏诊的期望成本为 5p。比较两者，1−p≤5p 得到 p≥1／6。这就是理想阈值的来源。经验阈值仍应在开发数据中选定，并说明样本量、校准与实际代价。'))
pages.insert(5,decisions)
pages[6]['table_caption']=pages[6]['table_caption'].replace('表 4','表 5')
pages[6]['blocks']=[(k,t.replace('表 4','表 5')) for k,t in pages[6]['blocks']]

with (ROOT/'data/heart.csv').open(encoding='utf-8-sig',newline='') as handle:
    data=list(csv.DictReader(handle))

def table(key, caption):
    if key=='comparison':
        headers=['方法','直接描述或估计什么','主要参照作用']
        rows=[['患病比例基线','训练数据的阳性比例；所有人使用同一概率','检查个人特征是否提供额外信息'],
              ['Gaussian NB','类条件高斯；给定类别后特征条件独立','以更强结构约束提供简单参照'],
              ['LDA','各类均值、共享协方差与类别先验','检验生成式建模及共享协方差假设'],
              ['Logistic','特征给定时的患病概率；线性 logit','检验条件建模与正则化的预测表现']]
    elif key=='decisions':
        headers=['阈值方案','FN','FP','成本 5×FN＋FP']
        rows=[['较高阈值','2','16','26'],['较低阈值','1','28','33']]
    elif key=='descriptives':
        import numpy as np
        headers=['输入变量','有效 n','中位数［Q1，Q3］','缺失 n（%）']
        rows=[]
        for name in ['age','trestbps','chol','thalach','oldpeak']:
            values=[float(r[name]) for r in data if r[name].strip() not in {'','NA','NaN','?','nan'}]
            q1,med,q3=np.quantile(values,[.25,.5,.75])
            fmt=lambda n:f'{n:.2f}'.rstrip('0').rstrip('.')
            missing=len(data)-len(values)
            rows.append([name,str(len(values)),f'{fmt(med)} [{fmt(q1)}, {fmt(q3)}]',f'{missing} ({missing/len(data):.1%})'])
    elif key=='metrics':
        headers=['指标','定义或对象','主要职责']
        rows=[['Sensitivity','TP／(TP＋FN)','真实阳性中的检出比例'],
              ['Specificity','TN／(TN＋FP)','真实阴性中的正确排除比例'],
              ['Precision','TP／(TP＋FP)','预测阳性中的实际阳性比例'],
              ['ROC-AUC','阳性评分高于阴性；同分计一半','排序区分，不指定阈值'],
              ['AP','precision–recall 的汇总评分','检出与阳性预测质量'],
              ['Brier／log loss','概率与标签的综合评分','概率质量，越低通常越好']]
    else:
        headers=['模型','均值或系数','协方差与先验','q＝20 时总数']
        rows=[['Logistic','q＋1','—','21'],['LDA','2q','q(q＋1)／2＋1','251'],['QDA','2q','q(q＋1)＋1','461']]
    return '<div class="table-caption">'+escape(caption)+'</div><table class="comparison"><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'

def equation(key):
    text,num,den,index=eqs[key]
    frac=('<span class="fraction"><span>'+escape(num)+'</span><span>'+escape(den)+'</span></span>') if num else ''
    return '<div class="equation'+(' long' if key=='loss' else '')+'">'+escape(text)+frac+'<span class="eqnumber">('+str(index)+')</span></div>'

def block(kind, value):
    if kind=='eq':return equation(value)
    tag={'h2':'h2','h3':'h3'}.get(kind,'p')
    cls=' class="'+('thought' if kind=='thought' else 'note')+'"' if kind in {'thought','note'} else ''
    return '<'+tag+cls+'>'+escape(value)+'</'+tag+'>'

def figure(name,caption):
    return '<figure><img src="../linear-models-report/figures/'+name+'" alt="'+escape(caption,quote=True)+'"><figcaption>'+escape(caption)+'</figcaption></figure>'

parts=[]
for i,page in enumerate(pages):
    content=[]
    content.append('<h1>'+escape(page['heading'])+'</h1>')
    if i==0:
        content.extend(['<p class="subtitle">'+escape(SUBTITLE)+'</p>',
                        '<p class="meta">知识框架与实践审计　|　课程报告正式版　|　2026 年 11 月</p>',
                        '<div class="abstract"><strong>摘要　</strong>'+escape(ABSTRACT)+'</div>',
                        '<p class="keywords">关键词：'+escape(KEYWORDS)+'</p>'])
    elif page.get('deck'):
        content.append('<p class="deck">'+escape(page['deck'])+'</p>')
    if page.get('figure_top'):
        content.append(figure(page['figure_top'],page['caption_top']))
    blocks=page['blocks']
    # The browser will measure actual line wrapping and balance at a heading.
    choices=[j for j in range(1,len(blocks)) if blocks[j][0] in {'h2','h3'}]
    if not choices:choices=[len(blocks)//2]
    split=choices[len(choices)//2]
    rendered=[block(k,v) for k,v in blocks]
    content.append('<div class="columns'+(' compact' if page.get('compact') else '')+'" data-candidates="'+','.join(map(str,choices))+'"><section>'+''.join(rendered[:split])+'</section><section>'+''.join(rendered[split:])+'</section></div>')
    if page.get('table'):content.append(table(page['table'],page['table_caption']))
    if page.get('figure'):content.append(figure(page['figure'],page['caption']))
    if page.get('references'):
        content.append('<div class="endmatter refs"><div class="full-heading">参考资料与数据说明</div>'+''.join('<p>'+escape(r)+'</p>' for r in REFERENCES)+'<p>图 1、2、4 为公式或机制演算；图 5 为受控模拟；图 3 与表 2 为当前教学文件审计。本报告未将示例图当作模型实测性能。</p></div>')
    parts.append('<article class="page '+('p1' if i==0 else 'p2')+'"><div class="running"><span>生物医学数据科学 · 方法简报</span><span>'+escape(page['name'])+'</span></div><div class="content">'+''.join(content)+'</div><div class="folio"><span>LINEAR CLASSIFICATION · METHODS AND EVIDENCE</span><span>'+f'{i+1:02}'+'</span></div></article>')

script='''<script>
window.addEventListener('load',async()=>{
 await document.fonts.ready;
 await Promise.all([...document.images].map(im=>im.complete?Promise.resolve():new Promise(r=>im.onload=r)));
 for(const columns of document.querySelectorAll('.columns')){
  const sections=[...columns.children], nodes=sections.flatMap(s=>[...s.children]);
  let best=null;
  for(const split of columns.dataset.candidates.split(',').map(Number)){
   nodes.forEach((n,i)=>sections[i<split?0:1].appendChild(n));
   const h=sections.map(s=>s.getBoundingClientRect().height);
   const score=Math.max(...h)+Math.abs(h[0]-h[1])*.03;
   if(!best||score<best.score)best={score,split};
  }
  nodes.forEach((n,i)=>sections[i<best.split?0:1].appendChild(n));
 }
 const checks=[...document.querySelectorAll('.page')].map((p,i)=>({page:i+1,clearance_px:Math.round(p.querySelector('.folio').getBoundingClientRect().top-p.querySelector('.content').getBoundingClientRect().bottom),wide:[...p.querySelectorAll('.equation,p,td,th')].filter(x=>x.scrollWidth>x.clientWidth+2).map(x=>x.textContent)}));
 document.body.dataset.layoutCheck=JSON.stringify(checks);
 const only=new URL(location).searchParams.get('page');
 if(only){[...document.querySelectorAll('.page')].forEach((p,i)=>{if(i+1!=Number(only))p.remove()});}
});
</script>'''
source='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>'+escape(TITLE)+'</title><style>'+css+'</style></head><body>'+''.join(parts)+script+'</body></html>'
path=OUT/'formal-report.html'
path.write_text(source,encoding='utf-8')

chrome='C:/Program Files/Google/Chrome/Application/chrome.exe'
flags=[chrome,'--headless','--disable-gpu','--disable-background-networking','--disable-extensions','--disable-sync','--no-first-run','--no-default-browser-check',f'--user-data-dir={QA/"browser-profile"}','--virtual-time-budget=1800','--no-pdf-header-footer','--hide-scrollbars']
uri=path.as_uri()
result=subprocess.run(flags+['--dump-dom',uri],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
match=re.search('data-layout-check="([^"]+)"',result.stdout)
if not match:raise RuntimeError(result.stderr[-1500:])
checks=json.loads(unescape(match.group(1)))
(QA/'layout-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
if any(c['clearance_px']<15 or c['wide'] for c in checks):
    print('LAYOUT_NEEDS_ADJUSTMENT')
    sys.exit(2)
pdf=OUT/'线性分类模型课程报告_正式版.pdf'
result=subprocess.run(flags+[f'--print-to-pdf={pdf}',uri],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
if result.returncode or not pdf.exists():raise RuntimeError(result.stderr[-1500:])
pages_in_pdf=len(re.findall(rb'/Type\s*/Page\b',pdf.read_bytes()))
assert pages_in_pdf==len(pages),(pages_in_pdf,len(pages))
print('PDF_PAGES',pages_in_pdf,'PDF_BYTES',pdf.stat().st_size)
for i in range(len(pages)):
    result=subprocess.run(flags+[f'--screenshot={QA/f"proof-{i+1:02}.png"}','--window-size=794,1123','--force-device-scale-factor=1',uri+f'?page={i+1}'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
    if result.returncode:raise RuntimeError(result.stderr[-1000:])
print('FORMAL_PDF',pdf)
