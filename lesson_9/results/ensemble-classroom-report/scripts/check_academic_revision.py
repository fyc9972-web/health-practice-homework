"""Validate the revised report against saved experiment outputs; no refitting."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.tmp'/'ensemble_report_deps'))
import re,json,hashlib
import numpy as np
import pandas as pd
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
from docx import Document
from sklearn.metrics import roc_auc_score,balanced_accuracy_score,confusion_matrix
from lxml import etree

OUT=ROOT/'results'/'ensemble-report'
RESULTS=ROOT/'results/ensemble-classroom-report'/'results'
REVIEW=OUT/'review'

def main():
    checks={}
    manifest=json.loads((RESULTS/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['test_labels_read'] is False
    for name,digest in manifest['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    checks['input_hashes_unchanged']=True
    for name in ['wdbc','ctg']:
        folder=RESULTS/name
        pred=pd.read_csv(folder/'validation-predictions.csv')
        for _,r in pd.read_csv(folder/'model-comparison.csv').iterrows():
            np.testing.assert_allclose([r.roc_auc,r.balanced_accuracy],
                [roc_auc_score(pred.y,pred[r.model+'_score']),balanced_accuracy_score(pred.y,pred[r.model+'_class'])],atol=1e-12)
            np.testing.assert_array_equal([r.tn,r.fp,r.fn,r.tp],confusion_matrix(pred.y,pred[r.model+'_class'],labels=[0,1]).ravel())
        fold=pd.read_csv(folder/'cv-folds.csv')
        cv=pd.read_csv(folder/'cross-validation.csv').set_index('model')
        assert len(fold)==35
        for model,g in fold.groupby('model'):
            np.testing.assert_allclose([cv.loc[model,'roc_auc_mean'],cv.loc[model,'roc_auc_sd']],[g.roc_auc.mean(),g.roc_auc.std(ddof=1)],atol=1e-12)
        for mode in (['row','recording'] if name=='ctg' else ['row']):
            for _,r in pd.read_csv(folder/f'prediction-stability-{mode}.csv').iterrows():
                p=np.load(folder/f'stability-{mode}-{r.model}.npz')['probabilities']
                assert p.shape==(30,len(pred))
                classes=(p>=.5).mean(axis=0)
                np.testing.assert_allclose([r.prediction_sd_mean,r.class_flip_rate],
                    [p.std(axis=0).mean(),((classes>0)&(classes<1)).mean()],atol=1e-12)
        checks[name+'_saved_metrics_verified']=True
    source=(OUT/'article.source.md').read_text(encoding='utf-8')
    md=next(OUT.glob('*_文字稿.md')).read_text(encoding='utf-8')
    html=(OUT/'index.html').read_text(encoding='utf-8')
    assert '{{' not in md and '\ufffd' not in md
    assert len(re.findall(r'^!\[',md,re.M))==12
    assert len(re.findall(r'^表 \d+｜',md,re.M))==13
    assert len(re.findall(r'^:::equation ',source,re.M))==13
    memos=re.findall(r'### 13\.[12][^\n]+\n\n([^\n]+)',source)
    assert len(memos)==2 and all(250<=len(m)<=400 for m in memos),[len(m) for m in memos]
    assert html.count('data:image/svg+xml;base64,')==12
    assert len(re.findall(r'<math\b',html))==15
    assert not re.search(r'<(?:img|script|link)[^>]+(?:src|href)=["\']https?://',html)
    doc=Document(next(OUT.glob('*.docx')))
    assert len(doc.inline_shapes)==12
    assert doc._element.xml.count('<m:oMath>')==15
    assert doc._element.xml.count('<m:f>')>=12
    for file in (OUT/'figures').glob('*.svg'):etree.parse(str(file))
    layout=json.loads((REVIEW/'layout-check.json').read_text())
    assert len(layout)==14 and all(r['overflow']==0 for r in layout)
    pdf=pdfium.PdfDocument(OUT/'Ensemblelesson_9.pdf')
    assert len(pdf)==14,len(pdf)
    texts=[];thumbs=[]
    for i,page in enumerate(pdf):
        text=page.get_textpage().get_text_range()
        assert len(text)>300 and '\ufffd' not in text,(i+1,len(text))
        texts.append(text)
        im=page.render(scale=.65).to_pil().convert('RGB')
        canvas=Image.new('RGB',(im.width,im.height+24),'#dce5ea');canvas.paste(im,(0,24))
        ImageDraw.Draw(canvas).text((10,6),str(i+1),fill='black');thumbs.append(canvas)
        if i+1 in [1,2,4,9,11,14]:page.render(scale=1.5).to_pil().save(REVIEW/f'page-{i+1}.png')
    for start in range(0,len(thumbs),8):
        chunk=thumbs[start:start+8];w,h=chunk[0].size
        canvas=Image.new('RGB',(w*4,h*2),'#c6d1d8')
        for j,im in enumerate(chunk):canvas.paste(im,((j%4)*w,(j//4)*h))
        canvas.save(REVIEW/f'contact-{start//8+1}.png')
    (REVIEW/'pdf-page-text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(texts)),encoding='utf-8')
    checks.update(pdf_pages=14,figures=12,tables=13,equation_groups=13,editable_word_equations=15,
                  memo_character_counts=[len(m) for m in memos],page_overflow=False,status='passed')
    (REVIEW/'quality-check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
