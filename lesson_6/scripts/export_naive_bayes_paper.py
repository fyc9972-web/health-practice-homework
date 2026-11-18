"""Export the illustrated course paper using a restrained academic layout."""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether

from export_student_documents import export as export_word_html, blocks, REPORTS
from export_student_pdf import inline  # Also registers the embedded Chinese fonts.

PAPER = REPORTS / 'naive-bayes-paper.md'
WIDTH = A4[0] - 100
BODY = ParagraphStyle('paper-body', fontName='Yahei', fontSize=10, leading=17,
                      spaceAfter=7, wordWrap='CJK', textColor=colors.black,
                      firstLineIndent=20, alignment=TA_JUSTIFY)
PLAIN = ParagraphStyle('paper-plain', parent=BODY, firstLineIndent=0)
CELL = ParagraphStyle('paper-cell', parent=PLAIN, fontSize=8, leading=12, spaceAfter=0)
CAPTION = ParagraphStyle('paper-caption', parent=PLAIN, fontSize=8.5, leading=14,
                         alignment=TA_CENTER, spaceBefore=5, spaceAfter=8)


def widths_for(rows):
    n = len(rows[0])
    if n == 5:
        return [0.23, 0.14, 0.14, 0.245, 0.245]
    if n == 4:
        if rows[0][0] == '顺序':
            return [0.08, 0.15, 0.32, 0.45]
        if rows[0][0] == '模型与数据':
            return [0.35, 0.25, 0.16, 0.24]
        return [0.25, 0.20, 0.23, 0.32]
    return [1/n]*n


def restyle_word():
    doc = Document(PAPER.with_suffix('.docx'))
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(1.9)
    for name in ['Normal', 'Title', 'Heading 1', 'Heading 2', 'Heading 3']:
        st = doc.styles[name]
        st.font.name = 'Times New Roman'
        st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '宋体' if name == 'Normal' else '黑体')
        st.font.color.rgb = RGBColor(0, 0, 0)
    normal = doc.styles['Normal']
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.4
    normal.paragraph_format.first_line_indent = Pt(21)
    for name, size in [('Title', 20), ('Heading 1', 14), ('Heading 2', 11.5)]:
        doc.styles[name].font.size = Pt(size)
        doc.styles[name].paragraph_format.first_line_indent = Pt(0)
    for p in doc.paragraphs:
        s = p.text
        if p.style.name == 'Title':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if not s or re.match(r'^(表\d|图\d|\[\d|核验附件|辅助说明|关键词|P\(|πc|ℓ\(|w[01] =|p =)', s):
            p.paragraph_format.first_line_indent = Pt(0)
        if re.match(r'^(表\d|图\d)', s):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.size = Pt(9)
            if s.startswith('表'):
                p.paragraph_format.keep_with_next = True
        for r in p.runs:
            if r.font.name != 'Consolas':
                r.font.color.rgb = RGBColor(0, 0, 0)
    for shape in doc.inline_shapes:
        max_width = Cm(17)
        if shape.width > max_width:
            shape.height = int(shape.height * max_width / shape.width)
            shape.width = max_width
    rows_list = [v for k, v in blocks(PAPER.read_text(encoding='utf-8')) if k == 'table']
    for table, rows in zip(doc.tables, rows_list):
        weights = widths_for(rows)
        props = table._tbl.tblPr
        borders = props.find(qn('w:tblBorders'))
        if borders is None:
            borders = OxmlElement('w:tblBorders'); props.append(borders)
        for side in ['top', 'bottom', 'left', 'right', 'insideH', 'insideV']:
            edge = OxmlElement('w:'+side)
            edge.set(qn('w:val'), 'single' if side in ['top', 'bottom'] else 'nil')
            edge.set(qn('w:sz'), '8'); edge.set(qn('w:color'), '333333')
            borders.append(edge)
        for col, weight in zip(table.columns, weights):
            col.width = Cm(17*weight)
        for i, row in enumerate(table.rows):
            for cell, weight in zip(row.cells, weights):
                cell.width = Cm(17*weight)
                for shade in list(cell._tc.get_or_add_tcPr().findall(qn('w:shd'))):
                    cell._tc.get_or_add_tcPr().remove(shade)
                if i == 0:
                    cb = OxmlElement('w:tcBorders'); edge = OxmlElement('w:bottom')
                    edge.set(qn('w:val'), 'single'); edge.set(qn('w:sz'), '4'); cb.append(edge)
                    cell._tc.get_or_add_tcPr().append(cb)
                for p in cell.paragraphs:
                    p.paragraph_format.first_line_indent = Pt(0)
                    for r in p.runs:
                        r.font.size = Pt(8.5)
                        r.font.color.rgb = RGBColor(0, 0, 0)
    footer = sec.footer.paragraphs[0]
    footer.clear()
    footer.paragraph_format.first_line_indent = Pt(0)
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    doc.core_properties.subject = '基于六项二元症状的朴素贝叶斯实验报告'
    doc.save(PAPER.with_suffix('.docx'))
    page = PAPER.with_suffix('.html').read_text(encoding='utf-8')
    paper_css = '<style>body{color:#111;background:#eee}main{max-width:960px;border-top:0}h1,h2,h3{color:#111}h1{text-align:center}h2{border:0}p{text-align:justify}table{border-top:2px solid #333;border-bottom:2px solid #333}th,td{border:0;border-bottom:1px solid #ddd}th{background:white;color:#111}tbody tr:nth-child(even){background:white}</style>'
    page = page.replace('</head>', paper_css+'</head>').replace('href="experiment-report.html"', 'href="naive-bayes-paper.html"')
    PAPER.with_suffix('.html').write_text(page, encoding='utf-8')


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Yahei', 8)
    canvas.drawCentredString(A4[0]/2, 25, str(doc.page))
    canvas.restoreState()


def export_pdf():
    flow = []
    parsed = list(blocks(PAPER.read_text(encoding='utf-8')))
    for kind, value in parsed:
        if kind == 'heading':
            level, text = value
            st = ParagraphStyle('paper-heading-'+str(level), parent=PLAIN,
                                fontName='YaheiBold', fontSize={1:19, 2:13, 3:11}.get(level, 10),
                                leading={1:28, 2:21, 3:18}.get(level, 17),
                                spaceBefore=12 if level > 1 else 0, spaceAfter=9,
                                keepWithNext=True, alignment=TA_CENTER if level == 1 else 0)
            flow.append(Paragraph(inline(text), st))
        elif kind == 'table':
            rows = value
            data = [[Paragraph(('<b>'+inline(s)+'</b>') if i == 0 else inline(s), CELL)
                     for s in row] for i, row in enumerate(rows)]
            t = Table(data, colWidths=[WIDTH*w for w in widths_for(rows)], repeatRows=1)
            t.setStyle(TableStyle([
                ('LINEABOVE', (0,0), (-1,0), .9, colors.black),
                ('LINEBELOW', (0,0), (-1,0), .5, colors.black),
                ('LINEBELOW', (0,-1), (-1,-1), .9, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ]))
            flow.extend([t, Spacer(1,9)])
        elif kind == 'image':
            alt, target = value
            with PILImage.open(PAPER.parent/target) as im:
                w, h = im.size
            width = WIDTH if w/h > 1.5 else 300
            flow.append(KeepTogether([Image(str(PAPER.parent/target), width=width, height=width*h/w),
                                      Paragraph(escape(alt), CAPTION)]))
        else:
            is_caption = bool(re.match(r'^表\d', value))
            if is_caption:
                st = ParagraphStyle('table-caption', parent=CAPTION, keepWithNext=True)
            elif re.match(r'^(P\(|πc|ℓ\(|w[01] =|p =|\[\d|核验附件|辅助说明|\*\*辅助说明|\*\*关键词)', value):
                st = PLAIN
            else:
                st = BODY
            flow.append(Paragraph(inline(value), st))
    title = parsed[0][1][1]
    doc = SimpleDocTemplate(str(PAPER.with_suffix('.pdf')), pagesize=A4,
                            leftMargin=50, rightMargin=50, topMargin=44, bottomMargin=44,
                            title=title, author='')
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)


if __name__ == '__main__':
    export_word_html(PAPER)
    restyle_word()
    export_pdf()
    print('Paper DOCX, HTML and PDF exported.')
