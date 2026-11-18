"""Check submission consistency; render PDFs for visual review."""
from pathlib import Path
import base64
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from pypdf import PdfReader
import pypdfium2 as pdfium

BASE=Path(__file__).resolve().parents[1]
REPORTS=BASE/'results'
QA=BASE/'.tmp/naive-bayes/deliverable-review'
QA.mkdir(parents=True,exist_ok=True)
evidence=json.loads((REPORTS/'experiment-evidence.json').read_text(encoding='utf-8'))
assert hashlib.sha256((BASE/'notebooks/naive-bayes-lab.ipynb').read_bytes()).hexdigest()==evidence['source_notebook_sha256']
assert abs(evidence['posterior']-evidence['sklearn_p'])<1e-12
assert evidence['test']['tn']==12 and evidence['test']['tp']==12
assert evidence['test']['fp']==evidence['test']['fn']==0
assert evidence['test_profiles_seen']==24
protocol=json.loads((REPORTS/'fixed-protocol.json').read_text(encoding='utf-8'))
assert protocol['threshold']==.5 and protocol['teacher_release_confirmed']
assert len(protocol['training_ids'])==len(set(protocol['training_ids']))==72
nb=json.loads((REPORTS/'naive-bayes-lab-completed.ipynb').read_text(encoding='utf-8'))
for idx in [1,3,5,7,9,11,13]:
    assert nb['cells'][idx]['execution_count'] is not None
    assert not any(o['output_type']=='error' for o in nb['cells'][idx]['outputs'])
assert nb['cells'][11]['execution_count']<nb['cells'][13]['execution_count']
assert nb['cells'][15]['execution_count'] is None
for idx,name in [(7,'B-ranking'),(9,'C-reliability')]:
    outputs=[o['data']['image/png'] for o in nb['cells'][idx]['outputs'] if 'image/png' in o.get('data',{})]
    assert base64.b64decode(outputs[-1])==(REPORTS/f'images/{name}.png').read_bytes()

results=[]
for stem in ['experiment-report','operation-guide','knowledge-guide']:
    md=REPORTS/f'{stem}.md'
    source=md.read_text(encoding='utf-8')
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',source):
        if not re.match('https?://',target): assert (md.parent/target).exists(),(stem,target)
    with zipfile.ZipFile(REPORTS/f'{stem}.docx') as z:
        ET.fromstring(z.read('word/document.xml'))
        image_count=len([p for p in z.namelist() if p.startswith('word/media/')])
        assert image_count==(0 if stem=='knowledge-guide' else 2)
    pdf_stem={'knowledge-guide':'knowledge-concepts','operation-guide':'classroom-operations'}.get(stem,stem)
    pdf_path=REPORTS/f'{pdf_stem}.pdf'
    reader=PdfReader(pdf_path)
    texts=[p.extract_text() or '' for p in reader.pages]
    assert all(len(x)>70 for x in texts), (stem,'almost blank page')
    joined='\n'.join(texts)
    assert '\ufffd' not in joined
    if stem=='experiment-report':
        for key in ['0.986575906','0.074492','AI','A094','99%','35/72']:
            assert key in joined,(stem,key)
    doc=pdfium.PdfDocument(str(pdf_path))
    thumbs=[]
    for index in range(len(doc)):
        im=doc[index].render(scale=.55).to_pil().convert('RGB')
        im.thumbnail((350,500))
        tile=Image.new('RGB',(370,530),'#dfe7ec')
        tile.paste(im,((370-im.width)//2,14))
        ImageDraw.Draw(tile).text((12,510),f'{stem} page {index+1}',fill='black')
        thumbs.append(tile)
        if stem=='experiment-report' and any(k in texts[index] for k in ['图1说明','图2说明','w0=','0.1 |']):
            doc[index].render(scale=1.4).to_pil().save(QA/f'{stem}-page-{index+1}.png')
    columns=3
    sheet=Image.new('RGB',(370*columns,530*((len(thumbs)+columns-1)//columns)),'#dfe7ec')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%columns)*370,(i//columns)*530))
    sheet.save(QA/f'{stem}-contact-sheet.jpg')
    results.append(dict(document=stem,pages=len(reader.pages),embedded_docx_images=image_count,
                        pdf_text_extracted=True,relative_links_checked=True))
record=dict(checks='passed',source_notebook_preserved=True,core_notebook_executed_without_errors=True,
            freeze_executed_before_test=True,images_extracted_exactly_from_notebook=True,
            posterior_difference=abs(evidence['posterior']-evidence['sklearn_p']),documents=results)
(QA/'verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
