"""Check the exported report against its source and experimental records."""
import hashlib
import json
import pickle
import zipfile
from xml.etree import ElementTree as ET
from PIL import Image
from analyze_svm_report import ROOT, metrics

out = ROOT / 'results/svm-report'
analysis = out / 'analysis'
manifest = json.loads((analysis / 'run-manifest.json').read_text(encoding='utf-8'))
structure = json.loads((analysis / 'report-structure.json').read_text(encoding='utf-8'))
pages = json.loads((analysis / 'word-text-by-page.json').read_text(encoding='utf-8-sig'))
with (analysis / 'development-results.pkl').open('rb') as f:
    result = pickle.load(f)

source_checks = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                 for name, digest in manifest['sources'].items()}
assert all(source_checks.values())
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(next(out.glob('*.docx'))) as z:
    names = z.namelist()
    xml = ET.fromstring(z.read('word/document.xml'))
    header_parts = [n for n in names if n.startswith(('word/header', 'word/footer'))]
    assert not header_parts
    assert not xml.findall('.//w:headerReference', ns)
    assert not xml.findall('.//w:footerReference', ns)
    fields = ' '.join(n.text or '' for n in xml.findall('.//w:instrText', ns))
    assert 'PAGE' not in fields
    figures = len(xml.findall('.//a:blip', ns))
    equations = len(xml.findall('.//m:oMath', ns))
    breaks = [b for b in xml.findall('.//w:br', ns)
              if b.get('{%s}type' % ns['w']) == 'page']
assert figures == 13 and equations == 11 and len(breaks) == 12
assert len(pages) == structure['expected_pages'] == 13
for page, title in zip(pages[1:], structure['page_titles'][1:]):
    assert page['text'].lstrip().startswith(title)

fit_checks = []
for key, model in result['models'].items():
    svc = model.named_steps['svc'] if hasattr(model, 'named_steps') else model
    fit_checks.append({'configuration': list(key), 'fit_status': int(svc.fit_status_),
                       'features': int(svc.n_features_in_)})
assert all(m['fit_status'] == 0 and m['features'] == 2 for m in fit_checks)
for family, key in result['configs'].items():
    actual = metrics(result['validation'].abnormal,
                     result['models'][key].decision_function(result['validation'][
                         ['pelvic_incidence', 'degree_spondylolisthesis']]))
    assert actual == manifest['validation'][family]
assert result['test'] is None and not manifest['test_opened']

images = []
for path in sorted((out / 'figures').glob('*.png')):
    with Image.open(path) as im:
        images.append({'file': path.name, 'width': im.width, 'height': im.height})
assert len(images) == 13 and min(i['width'] for i in images) >= 2500
review = {'source_hashes_unchanged': source_checks, 'actual_pages': len(pages),
          'expected_chapter_starts': True, 'header_footer_parts': header_parts,
          'page_number_fields': False, 'embedded_figures': figures,
          'editable_equations': equations, 'explicit_page_breaks': len(breaks),
          'experimental_models': fit_checks, 'validation_metrics_recomputed': True,
          'locked_test_evaluated': False, 'figure_dimensions': images,
          'visual_review': {'all_pages_reviewed': True, 'clipping_or_overflow_found': False,
                            'corrected': ['Legends no longer obscure geometry points.',
                                          'Hand-calculation parameter lines use left alignment.']}}
(analysis / 'layout-review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: 13 pages, 13 figures, 11 equations, source and result checks passed.')
