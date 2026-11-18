"""Check numerical consistency and inspectable document structure, without refitting."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.tmp'/'ensemble_report_deps'))
import re
import json
import hashlib
import numpy as np
import pandas as pd
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
from lxml import etree
from docx import Document
from sklearn.metrics import roc_auc_score,balanced_accuracy_score,confusion_matrix
from html.parser import HTMLParser

REPORT=Path(__file__).resolve().parents[1]
REVIEW=REPORT/'review'
REVIEW.mkdir(exist_ok=True)


class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.fragments=[];self.remote_assets=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag=='a' and a.get('href','').startswith('#'):self.fragments.append(a['href'][1:])
        if tag in ('img','script','link'):
            url=a.get('src',a.get('href',''))
            if url.startswith(('http:','https:')):self.remote_assets.append(url)


def main():
    checks={}
    manifest=json.loads((REPORT/'results'/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['test_labels_read'] is False
    for rel,digest in manifest['input_sha256'].items():
        assert 'teacher' not in rel and 'locked-test' not in rel
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest
    checks['input_hashes_unchanged']=True
    for name in ('wdbc','ctg'):
        result=REPORT/'results'/name
        models=pd.read_csv(result/'model-comparison.csv').set_index('model')
        pred=pd.read_csv(result/'validation-predictions.csv')
        for model,r in models.iterrows():
            np.testing.assert_allclose(r.roc_auc,roc_auc_score(pred.y,pred[model+'_score']),atol=1e-12)
            np.testing.assert_allclose(r.balanced_accuracy,balanced_accuracy_score(pred.y,pred[model+'_class']),atol=1e-12)
            np.testing.assert_array_equal([r.tn,r.fp,r.fn,r.tp],confusion_matrix(pred.y,pred[model+'_class'],labels=[0,1]).ravel())
        cv=pd.read_csv(result/'cv-folds.csv')
        assert len(cv)==35 and (cv.groupby('model').size()==5).all()
        summary=pd.read_csv(result/'cross-validation.csv').set_index('model')
        for model,d in cv.groupby('model'):
            np.testing.assert_allclose([summary.loc[model,'roc_auc_mean'],summary.loc[model,'roc_auc_sd']],
                                      [d.roc_auc.mean(),d.roc_auc.std(ddof=1)],atol=1e-12)
        for mode in (('row','recording') if name=='ctg' else ('row',)):
            stability=pd.read_csv(result/f'prediction-stability-{mode}.csv')
            for _,r in stability.iterrows():
                ps=np.load(result/f'stability-{mode}-{r.model}.npz')['probabilities']
                assert ps.shape==(30,len(pred))
                sd=ps.std(axis=0).mean();share=(ps>=.5).mean(axis=0)
                flips=((share>0)&(share<1)).mean()
                np.testing.assert_allclose([r.prediction_sd_mean,r.class_flip_rate],[sd,flips],atol=1e-12)
        boost=pd.read_csv(result/'boosting-curves.csv')
        assert len(boost)==1500
        for _,d in boost.groupby('learning_rate'):assert d.stage.tolist()==list(range(1,501))
        checks[name+'_prediction_metrics_cv_stability_consistent']=True
    md=(REPORT/'report.md').read_text(encoding='utf-8')
    assert '{{' not in md and '\ufffd' not in md
    assert len(re.findall(r'^!\[',md,re.M))==12
    assert md.count('```math')==10
    memos=re.findall(r'^> (本研究.+)',md,re.M)
    assert len(memos)==2
    assert all(250<=len(m)<=400 for m in memos),[len(m) for m in memos]
    checks['memo_character_counts']=[len(m) for m in memos]
    h=(REPORT/'index.html').read_text(encoding='utf-8')
    p=Parser();p.feed(h)
    assert not p.remote_assets
    assert set(p.fragments).issubset(p.ids)
    assert h.count('<figure>')==12 and h.count('data:image/svg+xml;base64,')==12
    assert h.count('<div class="formula-block">')==10
    assert h.count('<blockquote class="speaker">')==10
    doc=Document(REPORT/'report.docx')
    assert len(doc.inline_shapes)==12
    expected_tables=len(re.findall(r'^\|[^\n]*\n\|(?:[ :|-])+\|$',md,re.M))
    assert len(doc.tables)==expected_tables,(len(doc.tables),expected_tables)
    assert doc._element.xml.count('<m:oMath>')==21
    for svg in (REPORT/'figures').glob('*.svg'):etree.parse(str(svg))
    checks.update({'figures':12,'main_figures':11,'supplement_figures':1,'tables':len(doc.tables),
                   'formula_blocks':10,'editable_word_equation_lines':21,'speaker_notes':10,
                   'html_self_contained':True,'html_fragment_links_valid':True,'report_characters':len(md)})

    pdf=pdfium.PdfDocument(REPORT/'report.pdf')
    checks['pdf_pages']=len(pdf)
    texts=[];thumbs=[]
    for index,page in enumerate(pdf):
        tp=page.get_textpage();text=tp.get_text_range();texts.append(text)
        assert len(text)>150,(index+1,len(text))
        assert '\ufffd' not in text
        thumb=page.render(scale=.5).to_pil().convert('RGB')
        canvas=Image.new('RGB',(thumb.width,thumb.height+24),'#dce5ea');canvas.paste(thumb,(0,24))
        ImageDraw.Draw(canvas).text((10,6),str(index+1),fill='black');thumbs.append(canvas)
    whole='\n'.join(texts)
    for phrase in ('摘要','公式注释','备忘录示例','参考资料','测试标签'):
        assert phrase in whole,phrase
    for start in range(0,len(thumbs),12):
        chunk=thumbs[start:start+12];w,h=chunk[0].size
        sheet=Image.new('RGB',(w*4,h*3),'#c6d1d8')
        for j,im in enumerate(chunk):sheet.paste(im,((j%4)*w,(j//4)*h))
        sheet.save(REVIEW/f'contact-{start//12+1}.png')
    (REVIEW/'pdf-page-text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{text}' for i,text in enumerate(texts)),encoding='utf-8')
    checks['pdf_text_readable_no_blank_pages']=True
    checks['status']='passed'
    (REVIEW/'quality-check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
