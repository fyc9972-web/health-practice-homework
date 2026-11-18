"""Create the user-approved fixed-page Word edition from actual PDF renders."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
import hashlib
import json
import zipfile

from PIL import Image
from docx import Document
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/journal-formal'
QA=ROOT/'.tmp/journal-formal'
pages=sorted((QA/'pdf-pages').glob('page-*.png'))
assert len(pages)==8
doc=Document()
sec=doc.sections[0]
sec.page_width=Cm(21)
sec.page_height=Cm(29.7)
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Cm(0)
sec.header_distance=sec.footer_distance=Cm(0)
normal=doc.styles['Normal']
normal.font.size=Pt(1)
normal.paragraph_format.space_before=Pt(0)
normal.paragraph_format.space_after=Pt(0)
normal.paragraph_format.line_spacing=Pt(1)
normal.paragraph_format.widow_control=False
snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0')
normal.element.get_or_add_pPr().append(snap)

manifest=[]
for index,path in enumerate(pages):
    with Image.open(path) as image:
        assert image.width>=2480 and image.height>=3500
        image.verify()
    p=doc.add_paragraph()
    p.paragraph_format.page_break_before=index>0
    p.paragraph_format.keep_with_next=False
    p.paragraph_format.keep_together=False
    r=p.add_run()
    shape=r.add_picture(str(path),width=Cm(21),height=Cm(29.7))
    old=shape._inline
    anchor=OxmlElement('wp:anchor')
    for key,value in {'distT':'0','distB':'0','distL':'0','distR':'0','simplePos':'0','relativeHeight':str(index+1),'behindDoc':'0','locked':'1','layoutInCell':'1','allowOverlap':'1'}.items():anchor.set(key,value)
    simple=OxmlElement('wp:simplePos');simple.set('x','0');simple.set('y','0');anchor.append(simple)
    for axis in ['H','V']:
        pos=OxmlElement('wp:position'+axis);pos.set('relativeFrom','page')
        offset=OxmlElement('wp:posOffset');offset.text='0';pos.append(offset);anchor.append(pos)
    anchor.append(deepcopy(old.find(qn('wp:extent'))))
    effects=OxmlElement('wp:effectExtent')
    for key in ['l','t','r','b']:effects.set(key,'0')
    anchor.append(effects)
    anchor.append(OxmlElement('wp:wrapNone'))
    docpr=deepcopy(old.find(qn('wp:docPr')))
    docpr.set('name',f'PDF 原版第 {index+1} 页')
    docpr.set('descr',f'课程报告第 {index+1} 页，按原 PDF 整页保存，以保持版式；正文不能逐字编辑。')
    anchor.append(docpr)
    anchor.append(deepcopy(old.find(qn('wp:cNvGraphicFramePr'))))
    anchor.append(deepcopy(old.find(qn('a:graphic'))))
    old.getparent().replace(old,anchor)
    manifest.append({'page':index+1,'source':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

compress=OxmlElement('w:doNotAutoCompressPictures')
doc.settings.element.append(compress)
doc.core_properties.title='线性分类模型的概率建模与决策评价'
doc.core_properties.subject='沿用已认可样稿的正式版；PDF 同版式 Word 图版'
doc.core_properties.comments='用户选择保留版式的整页图版 Word。正文不能逐字编辑，适合展示与打印。'
doc.core_properties.author=''
dest=OUT/'线性分类模型课程报告_同版式Word图版.docx'
doc.save(dest)
with zipfile.ZipFile(dest) as archive:
    assert archive.testzip() is None
    media=[name for name in archive.namelist() if name.startswith('word/media/')]
    assert len(media)==len(pages)
    stored={hashlib.sha256(archive.read(name)).hexdigest() for name in media}
    assert stored=={item['sha256'] for item in manifest}
    xml=archive.read('word/document.xml')
    assert xml.count(b'<wp:anchor ')==8
    assert xml.count(b'<w:pageBreakBefore')==8 # first page explicitly false

reopened=Document(dest)
assert len(reopened.paragraphs)==8
assert sum(bool(p.paragraph_format.page_break_before) for p in reopened.paragraphs)==7
manifest_doc={'pages':8,'edition':'fixed-page facsimile; not editable text','pdf_sha256':hashlib.sha256((OUT/'线性分类模型课程报告_正式版.pdf').read_bytes()).hexdigest(),'word_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'images':manifest}
(QA/'delivery-verification.json').write_text(json.dumps(manifest_doc,ensure_ascii=False,indent=2),encoding='utf-8')
print('WORD_SAVED',dest)
print('WORD_BYTES',dest.stat().st_size)
print('PASS: 8 full-page anchors; 7 page breaks; 8 intact actual-PDF images; embedded hashes match')
