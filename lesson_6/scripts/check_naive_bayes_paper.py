"""Check paper assets, numerical evidence and printable output; render review pages."""
from pathlib import Path
import base64
import hashlib
import json
import re
import zipfile
from fractions import Fraction
from PIL import Image, ImageDraw
from pypdf import PdfReader
import pypdfium2 as pdfium

BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE/'results'
PAPER = REPORTS/'naive-bayes-paper.md'
QA = BASE/'.tmp/naive-bayes/paper-review'
QA.mkdir(parents=True, exist_ok=True)
evidence = json.loads((REPORTS/'experiment-evidence.json').read_text(encoding='utf-8'))
assert hashlib.sha256((BASE/'notebooks/naive-bayes-lab.ipynb').read_bytes()).hexdigest() == evidence['source_notebook_sha256']
nb = json.loads((REPORTS/'naive-bayes-lab-completed.ipynb').read_text(encoding='utf-8'))
for index, stem in [(7, 'B-ranking'), (9, 'C-reliability')]:
    outputs = [o['data']['image/png'] for o in nb['cells'][index]['outputs'] if 'image/png' in o.get('data', {})]
    assert base64.b64decode(outputs[-1]) == (REPORTS/f'images/{stem}.png').read_bytes()
w0 = Fraction(37,72)
w1 = Fraction(35,72)
for numerator in [13,33,8,14,6,14]:
    w0 *= Fraction(numerator,39)
for numerator in [23,23,23,36,29,18]:
    w1 *= Fraction(numerator,37)
assert abs(float(w1/(w0+w1))-evidence['sklearn_p']) < 1e-12
assert f"{evidence['test']['log_loss']:.6f}" == '0.074492'
source = PAPER.read_text(encoding='utf-8')
for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', source):
    if not target.startswith(('https://', 'http://')):
        assert (PAPER.parent/target).is_file(), target
assert len(re.findall(r'^!\[', source, re.M)) == 2
assert len(re.findall(r'^表\d', source, re.M)) == 6
with zipfile.ZipFile(PAPER.with_suffix('.docx')) as z:
    assert len([p for p in z.namelist() if p.startswith('word/media/')]) == 2
reader = PdfReader(PAPER.with_suffix('.pdf'))
texts = [p.extract_text() or '' for p in reader.pages]
joined = '\n'.join(texts)
for key in ['摘要', '结论', '0.986575906260', '0.074492', 'A094', '条件独立', 'AI']:
    assert key in joined, key
assert all(len(t) > 100 for t in texts)
assert '\ufffd' not in joined
pdf = pdfium.PdfDocument(str(PAPER.with_suffix('.pdf')))
thumbs = []
for i in range(len(pdf)):
    im = pdf[i].render(scale=.6).to_pil().convert('RGB')
    im.thumbnail((360, 510))
    tile = Image.new('RGB', (380, 540), '#ddd')
    tile.paste(im, ((380-im.width)//2, 10))
    ImageDraw.Draw(tile).text((12, 522), f'Paper page {i+1}', fill='black')
    thumbs.append(tile)
    if any(word in texts[i] for word in ['图1 ', '图2 ', '表3 ', 'w0 =']):
        pdf[i].render(scale=1.5).to_pil().save(QA/f'page-{i+1}.png')
sheet = Image.new('RGB', (380*3, 540*((len(thumbs)+2)//3)), '#ddd')
for i, im in enumerate(thumbs):
    sheet.paste(im, ((i%3)*380, (i//3)*540))
sheet.save(QA/'contact-sheet.jpg')
record = dict(checks='passed', pages=len(texts), notebook_source_preserved=True,
              original_notebook_figures=2, tables=6, links_valid=True,
              posterior_recalculated=float(w1/(w0+w1)),
              pdf_text_valid=True, docx_images=2)
(QA/'verification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
for i, t in enumerate(texts):
    print(f'Page {i+1}: {len(t)} characters; {t[:50]!r} ... {t[-70:]!r}')
