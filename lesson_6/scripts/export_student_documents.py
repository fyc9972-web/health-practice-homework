"""Build self-contained HTML and illustrated DOCX from the completed Markdown."""
from pathlib import Path
import base64
import html
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE / 'results'
TOKENS = re.compile(r'(`[^`]+`|\*\*.+?\*\*|!?\[[^\]]+\]\([^)]+\))')

def cells(line):
    return [x.strip().replace(r'\|', '|') for x in re.split(r'(?<!\\)\|', line.strip().strip('|'))]

def blocks(source):
    lines = source.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            yield 'code', '\n'.join(code)
        elif s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = cells(lines[i])
                if not all(re.fullmatch(r':?-+:?', x) for x in row): rows.append(row)
                i += 1
            yield 'table', rows
            continue
        elif re.fullmatch(r'!\[[^\]]*\]\([^)]+\)', s):
            match = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', s)
            yield 'image', match.groups()
        elif re.match(r'^#{1,6} ', s):
            marks, title = s.split(' ', 1)
            yield 'heading', (len(marks), title)
        elif re.match(r'^- \[[ x]\] ', s):
            yield 'check', s[6:]
        elif s.startswith('- '):
            yield 'bullet', s[2:]
        elif re.match(r'^\d+\. ', s):
            yield 'number', s
        else:
            yield 'paragraph', s
        i += 1

def inline_html(s):
    chunks = []
    for part in TOKENS.split(s):
        if part.startswith('`') and part.endswith('`'):
            chunks.append('<code>' + html.escape(part[1:-1]) + '</code>')
        elif part.startswith('**') and part.endswith('**'):
            chunks.append('<strong>' + html.escape(part[2:-2]) + '</strong>')
        elif re.fullmatch(r'\[[^\]]+\]\([^)]+\)', part):
            m = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', part)
            chunks.append(f'<a href="{html.escape(m[2], quote=True)}">{html.escape(m[1])}</a>')
        else:
            chunks.append(html.escape(part))
    return ''.join(chunks)

def inline_word(p, s):
    for part in TOKENS.split(s):
        if not part: continue
        if part.startswith('`') and part.endswith('`'):
            r = p.add_run(part[1:-1]); r.font.name = 'Consolas'; r.font.size = Pt(9)
        elif part.startswith('**') and part.endswith('**'):
            p.add_run(part[2:-2]).bold = True
        elif re.fullmatch(r'\[[^\]]+\]\([^)]+\)', part):
            m = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', part)
            node = OxmlElement('w:hyperlink')
            node.set(qn('r:id'), p.part.relate_to(m[2], 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True))
            run = OxmlElement('w:r'); props = OxmlElement('w:rPr')
            color = OxmlElement('w:color'); color.set(qn('w:val'), '165E80'); props.append(color)
            run.append(props); t = OxmlElement('w:t'); t.text = m[1]; run.append(t)
            node.append(run); p._p.append(node)
        else: p.add_run(part)

CSS = '''
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#edf2f6;color:#182938;font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;font-size:16px;line-height:1.85}
main{max-width:1120px;margin:32px auto;padding:44px 54px;background:white;border-top:7px solid #176e81;box-shadow:0 6px 32px #233c4d12}
h1{font-size:29px;line-height:1.45;color:#103d53;margin-top:0}h2{font-size:23px;color:#145b70;border-bottom:1px solid #c9dce4;padding-bottom:8px;margin-top:36px}h3{font-size:19px;color:#214b61;margin-top:25px}
p{margin:12px 0}a{color:#126889;text-decoration:none}a:hover{text-decoration:underline}code{font:0.9em Consolas,monospace;overflow-wrap:anywhere;background:#eff5f7;padding:2px 4px;border-radius:3px}pre{padding:18px;background:#eff5f7;white-space:pre-wrap;overflow-wrap:anywhere}pre code{padding:0;background:none}
table{width:100%;border-collapse:collapse;font-size:14px;margin:20px 0;line-height:1.65}th,td{padding:9px 10px;border:1px solid #ccdae2;text-align:left;overflow-wrap:anywhere}th{background:#e7f0f4;color:#164b60}tbody tr:nth-child(even){background:#f7fafb}thead{display:table-header-group}tr{break-inside:avoid}
figure{margin:24px 0;text-align:center;break-inside:avoid}figure img{max-width:100%;height:auto}figcaption{font-size:13px;color:#526c7b;margin-top:8px}nav{font-size:14px;padding:12px;background:#edf5f8;margin-bottom:24px}nav a{margin-right:20px}
li{margin:8px 0}.check{list-style:none}.check:before{content:'☐ ';color:#176e81}
@media(max-width:750px){main{margin:0;padding:22px 18px}table{font-size:12px}th,td{padding:5px}h1{font-size:24px}}
@media print{@page{size:A4;margin:16mm}body{background:white;font-size:10.5pt}main{max-width:none;margin:0;padding:0;border:0;box-shadow:none}nav{display:none}h1{font-size:20pt}h2{font-size:15pt;break-after:avoid}h3{font-size:12pt;break-after:avoid}table{font-size:8.5pt}th,td{padding:5px}a{color:inherit}pre{font-size:9pt}}
'''

def export(path):
    content = path.read_text(encoding='utf-8')
    parsed = list(blocks(content))
    title = next(v[1] for k,v in parsed if k == 'heading')
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.5)
    sec.top_margin = sec.bottom_margin = Cm(1.6)
    for name in ['Normal','Title','Heading 1','Heading 2','Heading 3','List Bullet']:
        style = doc.styles[name]
        style.font.name = 'Microsoft YaHei'
        style.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
        style.font.color.rgb = RGBColor.from_string('18384B')
    normal = doc.styles['Normal']
    normal.font.size = Pt(10)
    normal.paragraph_format.line_spacing = 1.2
    normal.paragraph_format.space_after = Pt(6)
    for name, size in [('Title',21),('Heading 1',15),('Heading 2',12),('Heading 3',11)]:
        doc.styles[name].font.size = Pt(size)
    doc.core_properties.title = title
    doc.core_properties.author = ''
    doc.core_properties.subject = '机器学习基础与朴素贝叶斯；AI辅助整理，真实实验输出'
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = footer.add_run('机器学习基础与朴素贝叶斯  ·  '); r.font.size = Pt(8)
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); footer._p.append(field)
    rendered = []
    for kind, value in parsed:
        if kind == 'heading':
            level, s = value
            p = doc.add_paragraph(style='Title' if level == 1 else f'Heading {min(level-1,3)}')
            inline_word(p,s)
            rendered.append(f'<h{level}>{inline_html(s)}</h{level}>')
        elif kind == 'table':
            rows = value
            assert all(len(r)==len(rows[0]) for r in rows), (path, rows)
            n = len(rows[0]); table = doc.add_table(rows=0, cols=n)
            table.style = 'Table Grid'; table.autofit = False
            if n >= 9: widths = [2.8] + [15.2/(n-1)]*(n-1)
            elif n == 6: widths = [3.6, .8, 2.1, 2.1, 4.7, 4.7]
            else:
                weights = [max(5,min(30,max(len(row[i]) for row in rows))) for i in range(n)]
                widths = [18*w/sum(weights) for w in weights]
            for col,w in zip(table.columns,widths): col.width = Cm(w)
            for row_i,row in enumerate(rows):
                cells_ = table.add_row().cells
                tr_pr = table.rows[-1]._tr.get_or_add_trPr(); tr_pr.append(OxmlElement('w:cantSplit'))
                if row_i == 0: tr_pr.append(OxmlElement('w:tblHeader'))
                for col_i, (cell, text) in enumerate(zip(cells_,row)):
                    cell.width = Cm(widths[col_i]); p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(3); p.paragraph_format.space_before = Pt(3)
                    inline_word(p,text)
                    for run in p.runs: run.font.size = Pt(7.5 if n >= 9 else 9)
                    if row_i == 0:
                        fill = OxmlElement('w:shd'); fill.set(qn('w:fill'),'E7F0F4'); cell._tc.get_or_add_tcPr().append(fill)
                        for run in p.runs: run.bold = True
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
            rendered.append('<table><thead><tr>'+''.join('<th>'+inline_html(x)+'</th>' for x in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline_html(x)+'</td>' for x in row)+'</tr>' for row in rows[1:])+'</tbody></table>')
        elif kind == 'image':
            alt, target = value
            img = path.parent / target
            assert img.is_file(), img
            from PIL import Image
            with Image.open(img) as im: width,height = im.size
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(img), width=Cm(min(18, 11 if width/height < 1.5 else 18)))
            p.paragraph_format.keep_with_next = True
            p = doc.add_paragraph(alt); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs: r.font.size = Pt(8)
            data = base64.b64encode(img.read_bytes()).decode('ascii')
            rendered.append(f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(alt)}"><figcaption>{html.escape(alt)}</figcaption></figure>')
        elif kind == 'code':
            p = doc.add_paragraph()
            r = p.add_run(value); r.font.name = 'Consolas'; r.font.size = Pt(8.5)
            fill = OxmlElement('w:shd'); fill.set(qn('w:fill'),'EFF5F7'); p._p.get_or_add_pPr().append(fill)
            rendered.append('<pre><code>'+html.escape(value)+'</code></pre>')
        else:
            p = doc.add_paragraph(style='List Bullet' if kind in ['bullet','check'] else None)
            inline_word(p, ('☐ ' if kind=='check' else '')+value)
            rendered.append(('<p class="check">' if kind=='check' else '<p>')+('• ' if kind=='bullet' else '')+inline_html(value)+'</p>')
    doc.save(path.with_suffix('.docx'))
    nav_prefix = 'results/' if path.parent == BASE else ''
    navigation = f'<nav><a href="{nav_prefix}experiment-report.html">图文报告</a><a href="{nav_prefix}operation-guide.html">操作说明</a><a href="{nav_prefix}knowledge-guide.html">知识清单</a></nav>'
    page = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style></head><body><main>'+navigation+'\n'.join(rendered)+'</main></body></html>'
    path.with_suffix('.html').write_text(page,encoding='utf-8')
    print(path.name, 'DOCX + HTML exported')

if __name__ == '__main__':
    export(BASE/'results/student-worksheet.md')
    for stem in ['experiment-report','operation-guide','knowledge-guide']:
        export(REPORTS/f'{stem}.md')
