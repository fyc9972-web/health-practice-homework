"""Make printable PDFs with embedded local Chinese fonts, without Office."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, KeepTogether)
from export_student_documents import blocks, TOKENS, REPORTS, BASE

FONTROOT = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Yahei',str(FONTROOT/'msyh.ttc'),subfontIndex=0))
pdfmetrics.registerFont(TTFont('YaheiBold',str(FONTROOT/'msyhbd.ttc'),subfontIndex=0))
pdfmetrics.registerFontFamily('Yahei', normal='Yahei', bold='YaheiBold', italic='Yahei', boldItalic='YaheiBold')
WIDTH = A4[0]-88
BODY = ParagraphStyle('body',fontName='Yahei',fontSize=9.4,leading=16.5,spaceAfter=7,wordWrap='CJK',textColor=colors.HexColor('#18384B'))
TABLE = ParagraphStyle('cell',parent=BODY,fontSize=7.8,leading=12,spaceAfter=0)
SMALLTABLE = ParagraphStyle('smallcell',parent=TABLE,fontSize=6.6,leading=10)
CAPTION = ParagraphStyle('caption',parent=BODY,fontSize=8,leading=12,alignment=TA_CENTER,spaceAfter=12)
CODE = ParagraphStyle('code',parent=BODY,fontName='Courier',fontSize=8,leading=12,backColor=colors.HexColor('#EFF5F7'),borderPadding=7)

def inline(s):
    chunks=[]
    for part in TOKENS.split(s):
        if part.startswith('`') and part.endswith('`'):
            chunks.append(escape(part[1:-1]))
        elif part.startswith('**') and part.endswith('**'):
            chunks.append('<b>'+escape(part[2:-2])+'</b>')
        elif re.fullmatch(r'\[[^\]]+\]\([^)]+\)',part):
            m=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',part)
            chunks.append(escape(m[1]))
        else: chunks.append(escape(part))
    return ''.join(chunks)

def footer(canvas,doc):
    canvas.saveState()
    canvas.setFont('Yahei',7.5)
    canvas.setFillColor(colors.HexColor('#526C7B'))
    canvas.drawCentredString(A4[0]/2,24,f'机器学习基础与朴素贝叶斯  ·  {doc.page}')
    canvas.restoreState()

def export(path):
    flow=[]
    for kind,value in blocks(path.read_text(encoding='utf-8')):
        if kind=='heading':
            level,s=value
            style=ParagraphStyle(f'h{level}',parent=BODY,fontName='YaheiBold',fontSize={1:19,2:13,3:11}.get(level,10),leading={1:28,2:21,3:18}.get(level,16),spaceBefore=12 if level>1 else 0,spaceAfter=9,keepWithNext=True)
            flow.append(Paragraph(inline(s),style))
        elif kind=='table':
            rows=value;n=len(rows[0]);style=SMALLTABLE if n>=9 else TABLE
            if n>=9: weights=[1.9]+[1]*(n-1)
            elif n==6: weights=[2.4,.55,1.1,1.1,2.6,2.6]
            else: weights=[max(5,min(30,max(len(row[i]) for row in rows))) for i in range(n)]
            widths=[WIDTH*w/sum(weights) for w in weights]
            data=[[Paragraph(('<b>'+inline(x)+'</b>') if i==0 else inline(x),style) for x in row] for i,row in enumerate(rows)]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7F0F4')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#CCDAE2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            flow.extend([t,Spacer(1,9)])
        elif kind=='image':
            alt,target=value
            from PIL import Image as PILImage
            with PILImage.open(path.parent/target) as im: w,h=im.size
            width=WIDTH if w/h>1.5 else 310
            flow.append(KeepTogether([Image(str(path.parent/target),width=width,height=width*h/w),Spacer(1,5),Paragraph(escape(alt),CAPTION)]))
        elif kind=='code':
            flow.append(Paragraph(escape(value).replace(' ','&#160;').replace('\n','<br/>'),CODE))
        else:
            prefix='☐ ' if kind=='check' else '• ' if kind=='bullet' else ''
            flow.append(Paragraph(prefix+inline(value),BODY))
    pdf_name={'knowledge-guide':'knowledge-concepts','operation-guide':'classroom-operations'}.get(path.stem,path.stem)
    destination=path.with_name(pdf_name+'.pdf')
    doc=SimpleDocTemplate(str(destination),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=40,bottomMargin=40,title=next(v[1] for k,v in blocks(path.read_text(encoding='utf-8')) if k=='heading'),author='')
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    print(path.stem,'PDF exported')

if __name__=='__main__':
    export(BASE/'results/student-worksheet.md')
    for stem in ['experiment-report','operation-guide','knowledge-guide']:
        export(REPORTS/f'{stem}.md')
