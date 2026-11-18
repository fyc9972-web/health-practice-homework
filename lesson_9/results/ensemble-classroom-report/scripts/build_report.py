"""Build the self-contained HTML, editable Word report and a printable PDF."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/".tmp"/"ensemble_report_deps"))
import base64
import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import pandas as pd
import markdown
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

REPORT=Path(__file__).resolve().parents[1]
RESULTS=REPORT/"results"
LABELS={"single_tree":"单树","bagging":"Bagging","random_forest":"随机森林",
        "adaboost":"AdaBoost","gradient_boosting":"梯度提升","logistic":"逻辑回归","rbf_svm":"RBF-SVM"}


def read(name,file):
    return pd.read_csv(RESULTS/name/file)


def md_table(headers,rows):
    return "\n".join(["| "+" | ".join(headers)+" |", "| "+" | ".join(["---"]*len(headers))+" |"]+
                     ["| "+" | ".join(map(str,row))+" |" for row in rows])


def populate():
    source=(REPORT/"report.template.md").read_text(encoding="utf-8")
    manifest=json.loads((RESULTS/"manifest.json").read_text(encoding="utf-8"))
    values={"PYTHON":manifest["python"],"SKLEARN":manifest["sklearn"]}
    sim=pd.read_csv(RESULTS/"bootstrap-simulation.csv")
    values["TABLE_BOOTSTRAP"]=md_table(["原记录数 n","不同记录比例：模拟均值","OOB：模拟均值","OOB：精确期望"],
        [[n,f"{d.unique_fraction.mean():.3%}",f"{d.oob_fraction.mean():.3%}",f"{d.expected_oob.iloc[0]:.3%}"]
         for n,d in sim.groupby("n")])
    for name,key in (("wdbc","W"),("ctg","C")):
        fixed=read(name,"model-comparison.csv").set_index("model")
        cv=read(name,"cross-validation.csv").set_index("model")
        rows=[]
        for model,label in LABELS.items():
            a,b=fixed.loc[model],cv.loc[model]
            rows.append([label,f"{a.roc_auc:.3f}",f"{a.balanced_accuracy:.3f}",
                         f"{b.roc_auc_mean:.3f} ± {b.roc_auc_sd:.3f}",f"{b.ap_mean:.3f}",f"{b.balanced_accuracy_mean:.3f}"])
        values[f"TABLE_{key}_MAIN"]=md_table(["模型","验证 AUC","验证 BA","CV AUC 均值 ± SD","CV AP","CV BA"],rows)
    rows=[]
    for name in ("wdbc","ctg"):
        for _,r in read(name,"prediction-stability-row.csv").iterrows():
            rows.append([name.upper(),LABELS[r.model],f"{r.prediction_sd_mean:.4f}",f"{r.class_flip_rate:.1%}"])
    values["TABLE_STABILITY"]=md_table(["数据","模型","平均预测 SD","类别翻转率"],rows)
    rows=[]
    for name in ("wdbc","ctg"):
        for _,r in read(name,"adaboost-weight-trace.csv").head(3).iterrows():
            rows.append([name.upper(),int(r.stage),int(r.wrong_count),f"{r.wrong_mass_before:.1%}",f"{r.wrong_mass_after:.1%}"])
    values["TABLE_ADA"]=md_table(["数据","轮次","本轮错分记录数","更新前权重占比","更新后权重占比"],rows)
    rows=[]
    for name in ("wdbc","ctg"):
        data=read(name,"boosting-curves.csv")
        for _,r in data[(data.learning_rate==.1)&data.stage.isin([50,100,500])].iterrows():
            rows.append([name.upper(),int(r.stage),f"{r.train_log_loss:.6f}",f"{r.validation_log_loss:.6f}",f"{r.validation_auc:.6f}"])
    values["TABLE_BOOSTING"]=md_table(["数据（η=0.1）","轮数","训练 log-loss","验证 log-loss","验证 AUC"],rows)
    rows=[]
    for name in ("wdbc","ctg"):
        data=read(name,"conditional-validation-bootstrap.csv")
        low,high=data.difference_rf_minus_lr.quantile([.025,.975])
        fixed=read(name,"model-comparison.csv").set_index("model")
        delta=fixed.loc["random_forest","roc_auc"]-fixed.loc["logistic","roc_auc"]
        rows.append([name.upper(),"验证行" if name=="wdbc" else "验证录音整组",f"{delta:+.4f}",f"[{low:+.4f}, {high:+.4f}]",len(data)])
    values["TABLE_CONDITIONAL"]=md_table(["数据","抽样单位","观察 AUC 差 RF−LR","探索性 95% 百分位区间","有效重复"],rows)
    for key,value in values.items():
        source=source.replace("{{"+key+"}}",str(value))
    assert not re.findall(r"\{\{.*?\}\}",source)
    (REPORT/"report.md").write_text(source,encoding="utf-8")
    return source


CSS=r"""
:root{--navy:#18344a;--teal:#16877f;--ink:#253b49;--muted:#687d89;--line:#dae3e8;--paper:#fff;--soft:#f2f7f8}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:70px}body{margin:0;background:#edf2f4;color:var(--ink);font:16px/1.95 'Noto Sans SC','Microsoft YaHei',sans-serif}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}.progress{height:3px;background:var(--teal);position:fixed;top:0;left:0;z-index:30;width:0}
.topbar{position:sticky;top:0;background:#18344af5;color:#fff;display:flex;align-items:center;justify-content:space-between;gap:15px;padding:12px 30px;z-index:20;box-shadow:0 2px 12px #18344a12}
.brand{font-size:12px;letter-spacing:1.2px}.tools{display:flex;gap:8px}.tools button{color:#fff;border:1px solid #ffffff55;background:transparent;padding:5px 12px;border-radius:3px;font:inherit;font-size:12px;cursor:pointer}.tools button:hover{background:#ffffff18}
.layout{max-width:1390px;margin:0 auto;display:grid;grid-template-columns:232px minmax(0,1fr);gap:28px;padding:30px 24px 70px}.sidebar{position:sticky;top:90px;align-self:start;max-height:83vh;overflow:auto;padding:4px 10px 25px 0;font-size:12px;line-height:1.7}.sidebar-label{font-weight:700;font-size:11px;letter-spacing:2px;color:var(--muted);margin-bottom:16px}.sidebar a{display:block;padding:7px 10px;color:#58707e;border-left:2px solid transparent}.sidebar a.active{border-color:var(--teal);background:#e2eeed;color:var(--teal)}
article{background:var(--paper);padding:56px 58px 46px;min-width:0;box-shadow:0 12px 45px #16314a07;border-top:4px solid var(--teal)}
.kicker{font-size:11px;letter-spacing:3px;font-weight:700;color:var(--teal);margin-bottom:20px}h1{font-size:35px;line-height:1.45;letter-spacing:-.5px;color:var(--navy);margin:0 0 18px;font-weight:750}h1+p{font-size:15px;color:var(--muted);margin:0 0 15px}h1+p+p{font-size:11px;color:var(--muted);padding-bottom:24px;border-bottom:1px solid var(--line)}
h2{font-size:23px;line-height:1.6;color:var(--navy);margin:48px 0 19px;padding-top:15px;border-top:2px solid var(--navy);break-after:avoid}h3{font-size:17px;line-height:1.7;margin:29px 0 12px;color:var(--navy);break-after:avoid}p{margin:12px 0 16px;text-align:justify;overflow-wrap:anywhere}strong{font-weight:700;color:#153c50}li{padding:3px 0}ol,ul{padding-left:25px}
blockquote{margin:24px 0;padding:17px 22px;border-left:3px solid var(--teal);background:#f0f7f5;color:#365a61;font-size:14px}blockquote p{margin:0;text-align:justify}.speaker{position:relative}.hide-speaker .speaker{display:none}.caption{font-size:12px;color:#5d727e;line-height:1.8;text-align:justify;margin:8px 0 0}.caption strong{color:var(--navy)}
figure{margin:26px 0 27px;padding:15px 0 13px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);break-inside:avoid}figure img{display:block;width:100%;height:auto;cursor:zoom-in}figure:has(img[src*='fig03']){padding-top:0}.figure-tools{font-size:11px;text-align:right;color:var(--muted);margin:4px 0 0}
.table-wrap{overflow-x:auto;margin:21px 0 25px}table{border-collapse:collapse;width:100%;font-size:12px;line-height:1.7;border-top:1.6px solid var(--navy);border-bottom:1px solid var(--navy)}thead{display:table-header-group}th{background:#edf3f6;color:var(--navy);padding:10px 9px;text-align:left;font-weight:700;border-bottom:1px solid #b9cbd5}td{padding:9px 9px;vertical-align:top;border-bottom:1px solid #e3e9ed}tr:nth-child(even) td{background:#fafcfc}tr:last-child td{border-bottom:0}tr{break-inside:avoid}td:nth-child(n+2){font-variant-numeric:tabular-nums}
code{font:12px/1.7 Consolas,monospace;background:#f0f4f6;color:#315669;padding:2px 4px;border-radius:2px}pre{white-space:pre-wrap;background:#f1f5f7;padding:16px;font-size:12px}pre code{padding:0;background:none}
.equation{background:#f6f9fb;border:1px solid #e1e9ed;padding:16px 20px;margin:20px 0 12px;text-align:center;line-height:2.1;font-family:'Cambria Math','Times New Roman','Noto Sans SC',serif;font-size:18px;break-inside:avoid}.eq-line{white-space:pre-wrap;overflow-wrap:anywhere}.eq-note{font-size:13px;color:#526b79;line-height:1.85;border-left:2px solid #ccdae2;padding-left:14px;margin:10px 0 22px}
.article-end{font-size:11px;letter-spacing:1px;color:var(--muted);text-align:center;border-top:1px solid var(--line);margin-top:35px;padding-top:20px}.zoom{border:0;padding:20px;background:white;width:min(98vw,1600px);max-width:98vw;max-height:96vh;box-shadow:0 10px 100px #0005}.zoom::backdrop{background:#102534cc}.zoom img{width:100%;height:auto;max-height:87vh;object-fit:contain}.zoom button{float:right;background:var(--navy);color:#fff;border:0;padding:5px 15px;cursor:pointer}
.presentation article{font-size:19px}.presentation h2{font-size:27px}.presentation .layout{grid-template-columns:190px minmax(0,1fr);max-width:1600px}.presentation figure{margin:35px 0}.presentation .caption{font-size:14px}
@media(max-width:1100px){.layout{grid-template-columns:180px minmax(0,1fr);gap:18px;padding:20px 15px}.sidebar{font-size:11px}article{padding:35px}h1{font-size:29px}}
@media(max-width:760px){.layout,.presentation .layout{display:block;padding:12px}.sidebar{display:none}article{padding:27px 21px}.brand{font-size:10px}.topbar{padding:10px 14px;flex-wrap:wrap}.tools button{font-size:11px}h1{font-size:27px}h2{font-size:21px}.equation{font-size:15px}}
@page{size:A4;margin:16mm 16mm 17mm;@bottom-right{content:counter(page);font-family:Arial;font-size:8pt;color:#758895}}
@media print{html{scroll-behavior:auto}body{background:#fff;font-size:9.8pt;line-height:1.75;-webkit-print-color-adjust:exact;print-color-adjust:exact}.topbar,.sidebar,.progress,.figure-tools,dialog{display:none!important}.layout{display:block;padding:0;margin:0;max-width:none}article{padding:0;border:0;box-shadow:none;background:white}.kicker{font-size:8pt;margin-bottom:12px}h1{font-size:25pt;line-height:1.45;margin-bottom:12px}h1+p{font-size:10pt}h1+p+p{font-size:8pt;padding-bottom:12px}h2{font-size:15pt;margin:24px 0 12px;padding-top:9px}h3{font-size:11pt;margin:18px 0 8px}p{margin:7px 0 10px;orphans:3;widows:3}figure{margin:16px 0 18px;padding:9px 0;break-inside:avoid}figure img{max-height:170mm;object-fit:contain}.caption{font-size:8pt;line-height:1.65}.table-wrap{overflow:visible;margin:12px 0 16px}table{font-size:8pt;line-height:1.65}th,td{padding:5px 6px}blockquote{font-size:9pt;margin:14px 0;padding:10px 13px;break-inside:avoid}.equation{font-size:12pt;line-height:1.85;padding:10px 12px;margin:13px 0 7px}.eq-note{font-size:9pt;line-height:1.7;margin-bottom:15px}code{font-size:8pt}a{color:inherit}.article-end{font-size:8pt}li{padding:1px 0}.presentation article{font-size:9.8pt}.presentation h2{font-size:15pt}}
"""


def build_html(source):
    md=markdown.Markdown(extensions=["tables","fenced_code","toc"],extension_configs={"toc":{"permalink":False}})
    body=md.convert(source)
    def equation(m):
        text=html.unescape(m.group(1)).rstrip()
        return '<div class="equation">'+"".join('<div class="eq-line">'+html.escape(line)+'</div>' for line in text.splitlines())+'</div>'
    body=re.sub(r'<pre><code class="language-math">(.*?)</code></pre>',equation,body,flags=re.S)
    body=re.sub(r'<p><strong>公式注释。</strong>(.*?)</p>',r'<p class="eq-note"><strong>公式注释。</strong>\1</p>',body,flags=re.S)
    body=re.sub(r'(<div class="equation">.*?</div></div>)\s*(<p class="eq-note">.*?</p>)',
                r'<div class="formula-block">\1\2</div>',body,flags=re.S)
    def figure(m):
        alt,rel,caption=m.groups()
        data=base64.b64encode((REPORT/rel).read_bytes()).decode("ascii")
        return f'<figure><img src="data:image/svg+xml;base64,{data}" alt="{alt}" loading="eager"/><figcaption class="caption">{caption}</figcaption><div class="figure-tools">点击图表可放大查看</div></figure>'
    body=re.sub(r'<p><img alt="([^"]*)" src="([^"]*)"\s*/?></p>\s*<p>(<strong>(?:图 |补充图).*?)</p>',figure,body,flags=re.S)
    assert body.count('<figure>')==12,body.count('<figure>')
    body=re.sub(r'<table>(.*?)</table>',r'<div class="table-wrap"><table>\1</table></div>',body,flags=re.S)
    body=re.sub(r'<blockquote>\s*<p><strong>课堂讲解',r'<blockquote class="speaker"><p><strong>课堂讲解',body)
    nav=[]
    for token in md.toc_tokens:
        for child in token.get("children",[]):
            if child["level"]==2:
                name=re.sub(r'^\d+\.\s*','',child["name"])
                nav.append(f'<a href="#{child["id"]}">{html.escape(name)}</a>')
    shell='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>从单树到集成｜课堂实践报告</title><style>__CSS__</style></head><body>
<div class="progress" id="progress"></div><header class="topbar"><div class="brand">ENSEMBLE LEARNING / 课堂实践研究</div><div class="tools"><button onclick="document.body.classList.toggle('hide-speaker')">讲解提示</button><button onclick="document.body.classList.toggle('presentation')">大字阅读</button><button onclick="window.print()">打印 / 存为 PDF</button></div></header>
<div class="layout"><nav class="sidebar"><div class="sidebar-label">阅读路线 / CONTENTS</div>__NAV__</nav><article><div class="kicker">CLASSROOM RESEARCH REPORT · LESSON 10</div>__BODY__<div class="article-end">方法可复现 · 结论有边界 · 测试标签未揭示</div></article></div>
<dialog class="zoom" id="zoom"><button onclick="document.getElementById('zoom').close()">关闭 ×</button><img id="zoomimg" alt="放大图表"></dialog>
<script>document.querySelectorAll('figure img').forEach(img=>img.addEventListener('click',()=>{document.getElementById('zoomimg').src=img.src;document.getElementById('zoom').showModal()}));document.getElementById('zoom').addEventListener('click',e=>{if(e.target.id==='zoom')e.target.close()});const links=[...document.querySelectorAll('.sidebar a')];const sections=[...document.querySelectorAll('h2[id]')];addEventListener('scroll',()=>{const max=document.documentElement.scrollHeight-innerHeight;document.getElementById('progress').style.width=(max>0?scrollY/max*100:0)+'%';let current=sections[0]?.id;sections.forEach(s=>{if(s.getBoundingClientRect().top<150)current=s.id});links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+current))},{passive:true});</script></body></html>'''
    print_refinements='@media print{.table-wrap,.formula-block{break-inside:avoid}.formula-block .eq-note{margin-bottom:12px}}'
    shell=shell.replace('__CSS__',CSS+print_refinements).replace('__NAV__',''.join(nav)).replace('__BODY__',body)
    assert len(nav)>=14,len(nav)
    (REPORT/"index.html").write_text(shell,encoding="utf-8")
    print("HTML ready; embedded figures: 12; navigation entries:",len(nav),flush=True)


def font(style,size,latin="Calibri",east="Noto Sans SC"):
    style.font.name=latin;style.font.size=Pt(size)
    rpr=style.element.get_or_add_rPr();fonts=rpr.find(qn("w:rFonts"))
    if fonts is None:fonts=OxmlElement("w:rFonts");rpr.insert(0,fonts)
    fonts.set(qn("w:eastAsia"),east)


def shade(p,color):
    pr=p.get_or_add_pPr() if p.tag==qn('w:p') else p.get_or_add_tcPr()
    shd=OxmlElement('w:shd');shd.set(qn('w:fill'),color);pr.append(shd)


def inline(p,text):
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`|<https?://[^>]+>)',text):
        if not part:continue
        if part.startswith('**') and part.endswith('**'):p.add_run(part[2:-2]).bold=True
        elif part.startswith('`') and part.endswith('`'):
            r=p.add_run(part[1:-1]);r.font.name='Consolas';r.font.size=Pt(8.5)
        elif part.startswith('<http'):p.add_run(part[1:-1])
        else:p.add_run(part)


def build_word(source):
    doc=Document();sec=doc.sections[0]
    sec.page_width,sec.page_height=Cm(21),Cm(29.7)
    sec.top_margin,sec.bottom_margin=Cm(1.8),Cm(1.8)
    sec.left_margin,sec.right_margin=Cm(1.7),Cm(1.7)
    font(doc.styles['Normal'],10)
    doc.styles['Normal'].paragraph_format.line_spacing=1.25
    doc.styles['Normal'].paragraph_format.space_after=Pt(6)
    for name,size in [('Title',23),('Heading 1',16),('Heading 2',12),('Heading 3',11)]:
        font(doc.styles[name],size);doc.styles[name].font.color.rgb=RGBColor.from_string('18344A')
        doc.styles[name].paragraph_format.space_before=Pt(13)
        doc.styles[name].paragraph_format.space_after=Pt(7)
    for name,size,color in [('Report Caption',8.5,'627885'),('Report Note',9,'4D6C77'),('Report Equation',12,'18344A')]:
        style=doc.styles.add_style(name,1);font(style,size,latin='Cambria Math' if 'Equation' in name else 'Calibri')
        style.font.color.rgb=RGBColor.from_string(color);style.paragraph_format.line_spacing=1.15
        style.paragraph_format.space_after=Pt(7)
    p=sec.header.paragraphs[0];r=p.add_run('从单树到集成  |  集成学习与 Bootstrapping');r.font.size=Pt(8)
    p=sec.footer.paragraphs[0];p.alignment=2
    p.add_run('课堂实践研究  ·  ').font.size=Pt(8)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');p._p.append(field)
    lines=source.splitlines();i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            lang=line[3:];i+=1;block=[]
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            for item in block:
                p=doc.add_paragraph(style='Report Equation');p.alignment=1;shade(p._p,'F2F6F9')
                # A native editable Word math object; Unicode linear expressions retain beginner readability.
                math=OxmlElement('m:oMath');run=OxmlElement('m:r');text=OxmlElement('m:t');text.text=item;run.append(text);math.append(run);p._p.append(math)
                p.paragraph_format.keep_with_next=True
            i+=1;continue
        image=re.match(r'!\[(.*?)\]\((.*?)\)',line)
        if image:
            p=doc.add_paragraph();p.alignment=1;p.paragraph_format.keep_with_next=True
            imagepath=(REPORT/image.group(2)).with_suffix('.png')
            p.add_run().add_picture(str(imagepath),width=Cm(17.3))
            i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in row):rows.append(row)
                i+=1
            assert all(len(r)==len(rows[0]) for r in rows)
            table=doc.add_table(rows=len(rows),cols=len(rows[0]));table.style='Light Shading Accent 1'
            for ri,row in enumerate(rows):
                for ci,value in enumerate(row):
                    cell=table.cell(ri,ci);p=cell.paragraphs[0];inline(p,value)
                    p.paragraph_format.line_spacing=1.12;p.paragraph_format.space_after=Pt(4)
                    p.paragraph_format.space_before=Pt(3)
                    for run in p.runs:run.font.size=Pt(8.3);run.bold=(ri==0)
                    if ri==0:shade(cell._tc,'E6EFF3')
                cant=OxmlElement('w:cantSplit');table.rows[ri]._tr.get_or_add_trPr().append(cant)
            repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
            doc.add_paragraph().paragraph_format.space_after=Pt(2)
            continue
        h=re.match(r'^(#{1,3}) (.+)',line)
        if h:
            level=len(h.group(1))-1;p=doc.add_paragraph(style='Title' if level==0 else f'Heading {level}')
            inline(p,h.group(2))
        elif line.startswith('> '):
            p=doc.add_paragraph(style='Report Note');inline(p,line[2:]);shade(p._p,'F0F7F5')
            p.paragraph_format.keep_together=True;p.paragraph_format.left_indent=Cm(.2)
        elif re.match(r'^\*\*(图 \d+|补充图)',line):
            p=doc.add_paragraph(style='Report Caption');inline(p,line);p.paragraph_format.keep_together=True
        elif line.startswith('**公式注释。'):
            p=doc.add_paragraph(style='Report Note');inline(p,line)
        else:
            p=doc.add_paragraph();inline(p,line)
        i+=1
    doc.core_properties.title='从单树到集成：用课堂实验理解稳定性、性能与模型选择'
    doc.core_properties.subject='第10讲课堂研究报告；WDBC与CTG双方案'
    doc.core_properties.author=''
    doc.save(REPORT/'report.docx')
    print('Editable Word report ready',flush=True)


def build_pdf():
    candidates=[Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'),Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')]
    browser=next((p for p in candidates if p.is_file()),None)
    if browser is None:raise RuntimeError('A Chromium browser is required for PDF export.')
    profile=ROOT/'.tmp'/'ensemble_report_browser'
    command=[str(browser),'--headless','--disable-gpu','--no-sandbox','--disable-background-networking',
             '--disable-sync','--no-first-run','--no-default-browser-check','--no-pdf-header-footer',
             '--allow-file-access-from-files','--user-data-dir='+str(profile),
             '--print-to-pdf='+str(REPORT/'report.pdf'),(REPORT/'index.html').as_uri()]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode or not (REPORT/'report.pdf').exists():
        raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[-2500:])
    print('PDF ready:',(REPORT/'report.pdf').stat().st_size,'bytes',flush=True)


def main():
    source=populate()
    build_html(source)
    build_word(source)
    if '--no-pdf' not in sys.argv:build_pdf()


if __name__=='__main__':main()
