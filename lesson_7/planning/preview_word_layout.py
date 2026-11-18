"""Internal approximate layout proof generated from the final Word XML."""
from pathlib import Path
from html import escape
import base64
import json
import re
import subprocess
from docx import Document
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'.tmp/linear-models-report-layout'
DEST.mkdir(parents=True,exist_ok=True)
doc=Document(ROOT/'results/linear-models-report/linear-models-report.docx')
ns=doc.element.nsmap

def text(e):
    return ''.join(e.itertext())

def math(e):
    result=''
    for child in e:
        if child.tag==qn('m:r'):
            result+=escape(''.join(child.itertext()))
        elif child.tag==qn('m:f'):
            num=child.find(qn('m:num')); den=child.find(qn('m:den'))
            result+='<span class="fraction"><span>'+escape(text(num))+'</span><span>'+escape(text(den))+'</span></span>'
    return result

def paragraph(p, intable=False):
    pr=p.find(qn('w:pPr'))
    style=pr.find(qn('w:pStyle')) if pr is not None else None
    style=style.get(qn('w:val')) if style is not None else 'Normal'
    parts=[]
    for child in p:
        if child.tag==qn('w:r'):
            drawings=child.findall('.//'+qn('a:blip'))
            if drawings:
                for blip in drawings:
                    part=doc.part.related_parts[blip.get(qn('r:embed'))]
                    parts.append('<img src="data:'+part.content_type+';base64,'+base64.b64encode(part.blob).decode()+'">')
            else:
                parts.append(escape(''.join(t.text or '' for t in child.findall('.//'+qn('w:t')))))
        elif child.tag==qn('m:oMath'):
            parts.append('<span class="math">'+math(child)+'</span>')
    s=''.join(parts)
    if not s:return ''
    return '<p class="'+style+(' image' if '<img' in s else '')+'">'+s+'</p>'

def table(t):
    rows=t.findall(qn('w:tr'))
    layout=len(rows)==1 and len(rows[0].findall(qn('w:tc')))==3
    if layout:
        cells=rows[0].findall(qn('w:tc'))
        return '<div class="columns">'+''.join('<section>'+''.join(paragraph(p,True) for p in c.findall(qn('w:p')))+'</section>' for c in (cells[0],cells[2]))+'</div>'
    return '<table>'+''.join('<tr>'+''.join('<'+('th' if i==0 else 'td')+'>'+''.join(paragraph(p,True) for p in c.findall(qn('w:p')))+'</'+('th' if i==0 else 'td')+'>' for c in row.findall(qn('w:tc')))+'</tr>' for i,row in enumerate(rows))+'</table>'

pages=[[]]
for e in doc.element.body:
    if e.tag==qn('w:p'):
        if any(b.get(qn('w:type'))=='page' for b in e.findall('.//'+qn('w:br'))):pages.append([])
        else:pages[-1].append(paragraph(e))
    elif e.tag==qn('w:tbl'):
        pages[-1].append(table(e))

css='''@page {size:A4;margin:0} *{box-sizing:border-box} body{margin:0;background:#e4e8eb;color:#171b20;font-family:"Times New Roman","SimSun",serif;font-size:10pt}
.page{width:210mm;height:297mm;padding:16mm 17mm 15.5mm;background:white;position:relative;break-after:page}
p{margin:0 0 4pt;line-height:1.35;text-align:justify} .Title{font-family:"SimHei";font-size:18.5pt;line-height:1.15;margin-bottom:5pt;color:#172d3d}.page:not(:first-child)>.content>.Title{font-size:14pt}
.Subtitle{font-size:10.4pt;color:#526471;margin-bottom:7pt}.Caption{font-size:8pt;line-height:1.2;color:#4f626f;margin-bottom:4pt}
.Heading1{font-family:"SimHei";font-size:11pt;color:#24445c;margin:7pt 0 4pt;line-height:1.35}
.Heading2{font-family:"SimHei";font-size:10.2pt;color:#24445c;margin:7pt 0 4pt;line-height:1.35}
.columns{display:grid;grid-template-columns:84.5mm 84.5mm;gap:7mm} .columns section{min-width:0}
.math{font-family:"Cambria Math";font-size:9pt;display:inline-flex;align-items:center;vertical-align:middle;line-height:1.1}
p:has(>.math){text-align:center;margin:2pt 0 4pt;line-height:1.1;font-size:7.5pt}
.fraction{display:inline-flex;flex-direction:column;text-align:center;margin:0 2pt}.fraction>span:first-child{border-bottom:.5pt solid black;padding-bottom:2pt}.fraction>span:last-child{padding-top:2pt}
.image{margin:4pt 0 1pt;line-height:0}.image img{width:176mm;height:auto}
table{width:176mm;border-collapse:collapse;table-layout:fixed;margin-bottom:3pt}td,th{text-align:left;padding:3pt 5.4pt;font-weight:normal;vertical-align:top}table p{font-size:8.3pt;line-height:1.15;margin:0}th{border-top:.6pt solid #687e8e;border-bottom:.4pt solid #687e8e;font-family:SimHei}tr:last-child td{border-bottom:.6pt solid #687e8e}
.header{position:absolute;top:7mm;left:17mm;right:17mm;font-size:7pt;color:#657580;border-bottom:.4pt solid #a4b1bb;padding-bottom:3pt}
.footer{position:absolute;bottom:8mm;left:17mm;right:17mm;font-size:7pt;color:#657580;display:flex;justify-content:space-between}
@media print{body{background:white}.page{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''
script='''<script>window.addEventListener('load',async()=>{await document.fonts.ready;document.body.dataset.checks=JSON.stringify([...document.querySelectorAll('.page')].map((p,i)=>({page:i+1,contentHeight:p.querySelector('.content').getBoundingClientRect().height,clearance:p.querySelector('.footer').getBoundingClientRect().top-p.querySelector('.content').getBoundingClientRect().bottom,wide:[...p.querySelectorAll('section p')].filter(x=>x.scrollWidth>x.clientWidth+2).map(x=>x.innerText)})))});</script>'''
html='<!doctype html><html><head><meta charset="utf-8"><style>'+css+'</style></head><body>'+''.join('<article class="page"><div class="header">生物医学数据科学 · 方法与实践报告</div><div class="content">'+''.join(page)+'</div><div class="footer"><span>LINEAR CLASSIFICATION · METHODS AND EVIDENCE</span><span>'+str(i+1)+'</span></div></article>' for i,page in enumerate(pages))+script+'</body></html>'
(DEST/'layout-proof.html').write_text(html,encoding='utf-8')
chrome=Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
flags=[str(chrome),'--headless','--disable-gpu','--disable-background-networking','--no-first-run','--no-default-browser-check','--disable-extensions',f'--user-data-dir={DEST/"browser-profile"}','--virtual-time-budget=1200','--hide-scrollbars']
uri=(DEST/'layout-proof.html').as_uri()
result=subprocess.run(flags+['--dump-dom',uri],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
m=re.search('data-checks="([^"]+)"',result.stdout)
if m:
    import html as h
    checks=json.loads(h.unescape(m.group(1)));print(json.dumps(checks,ensure_ascii=False,indent=2))
    (DEST/'approximate-layout.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
else:print(result.returncode,result.stderr[-1000:])
result=subprocess.run(flags+[f'--screenshot={DEST/"six-page-preview.png"}','--window-size=794,6736','--force-device-scale-factor=1',uri],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
print('Screenshot exit',result.returncode)
print('This is an approximate browser proof, not a Word-native render.')
