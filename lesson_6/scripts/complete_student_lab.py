"""Execute a submission copy of the supplied notebook; preserve its source file.

Run with the existing Anaconda interpreter. D requires --release-confirmed.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import math
import os
import sys

BASE = Path(__file__).resolve().parents[1]
os.chdir(BASE)
sys.dont_write_bytecode = True
CACHE = BASE / '.tmp/naive-bayes/submission-runtime'
CACHE.mkdir(parents=True, exist_ok=True)
for key in ['JUPYTER_CONFIG_DIR', 'JUPYTER_DATA_DIR', 'JUPYTER_RUNTIME_DIR', 'IPYTHONDIR', 'MPLCONFIGDIR']:
    os.environ[key] = str(CACHE / key.lower())
os.environ['MPLBACKEND'] = 'Agg'
os.environ['JUPYTER_ALLOW_INSECURE_WRITES'] = 'true'

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

parser = argparse.ArgumentParser()
parser.add_argument('--release-confirmed', action='store_true')
args = parser.parse_args()
OUT = BASE / 'results'
ASSETS = OUT / 'images'
ASSETS.mkdir(parents=True, exist_ok=True)
source = BASE / 'notebooks/naive-bayes-lab.ipynb'
nb = nbformat.read(source, as_version=4)
setup = nb.cells[1].source
setup = setup.replace("OUT = REPO/'.tmp/naive-bayes/student-results'", "OUT = BASE/'.tmp/naive-bayes/submission-runtime/results'")
setup = setup.replace('FREEZE_CONFIRMED = False\nOPEN_LOCKED_TEST = False',
                      f'FREEZE_CONFIRMED = {args.release_confirmed}\nOPEN_LOCKED_TEST = {args.release_confirmed}')
setup += "\n%matplotlib inline\n"
nb.cells[1].source = setup
# Keep the optional transfer section visible without running a second task.
nb.cells[15].metadata['tags'] = ['skip-execution']
km = KernelManager(kernel_name='python3')
km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
client = NotebookClient(nb, timeout=240, km=km, resources={'metadata': {'path': str(BASE)}},
                        skip_cells_with_tag='skip-execution')
client.execute()
nbformat.write(nb, OUT / 'naive-bayes-lab-completed.ipynb')
for cell, name in [(7, 'B-ranking'), (9, 'C-reliability')]:
    images = [o['data']['image/png'] for o in nb.cells[cell].get('outputs', [])
              if 'image/png' in o.get('data', {})]
    if not images:
        raise RuntimeError(f'Notebook cell {cell} produced no embedded image')
    (ASSETS / f'{name}.png').write_bytes(base64.b64decode(images[-1]))

# Independent arithmetic checks and machine-readable evidence use train/val only.
sys.path.insert(0, str(BASE / 'scripts'))
from lab_utils import *
train = pd.read_csv(BASE/'data/student/train.csv')
val = pd.read_csv(BASE/'data/student/validation.csv')
target = 'bladder_inflammation'
model = fit_model(train)
vp = model.predict_proba(val[FEATURES])[:, 1]
hand, weights, posterior = hand_calculation(train, [0,0,0,1,1,1])
hand.to_csv(OUT/'bayes-handcheck.csv', index=False, encoding='utf-8-sig')
table = threshold_table(val[target], vp)
table.to_csv(OUT/'validation-thresholds.csv', index=False, encoding='utf-8-sig')
threshold = choose_threshold(table)
freeze = dict(target=target, features=FEATURES, alpha=1, fever_cutoff=38,
              training_ids=train.sample_id.tolist(), threshold=threshold,
              refit_train_plus_validation=False,
              teacher_release_confirmed=args.release_confirmed,
              status='executed_after_user_confirmation' if args.release_confirmed else 'awaiting_teacher_release')
(OUT/'fixed-protocol.json').write_text(json.dumps(freeze, indent=2, ensure_ascii=False), encoding='utf-8')
dup = []
examples = []
for copies in [0,1,5]:
    tx, vx = train[FEATURES].copy(), val[FEATURES].copy()
    for i in range(copies):
        tx[f'copy_{i}'] = tx.lumbar_pain
        vx[f'copy_{i}'] = vx.lumbar_pain
    dm = BernoulliNB(alpha=1, binarize=None).fit(tx, train[target])
    dp = dm.predict_proba(vx)[:,1]
    dup.append(dict(copies=copies, **scores(val[target], dp)))
    if copies == 5:
        frame = pd.DataFrame(dict(sample_id=val.sample_id, y=val[target], lumbar_pain=val.lumbar_pain,
                                  original_p=vp, duplicate_p=dp, change=abs(dp-vp)))
        examples = frame.sort_values('change', ascending=False).head(3).to_dict('records')
evidence = dict(source_notebook_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                versions={x.__name__: x.__version__ for x in [np,pd,__import__('sklearn'),__import__('matplotlib')]},
                hand=hand.to_dict('records'),weights=weights.tolist(),posterior=posterior,
                sklearn_p=float(model.predict_proba(pd.DataFrame([[0,0,0,1,1,1]],columns=FEATURES))[0,1]),
                train=scores(train[target],model.predict_proba(train[FEATURES])[:,1]),
                validation=scores(val[target],vp), baseline=scores(val[target],np.full(len(val),train[target].mean())),
                thresholds=table.to_dict('records'), duplicates=dup, duplicate_examples=examples,
                reliability=reliability(val[target],vp).to_dict('records'),
                dependence=dependence(train).to_dict('records'),
                train_profiles=len(train[FEATURES].drop_duplicates()),
                validation_profiles_seen=sum(tuple(x) in set(map(tuple,train[FEATURES].to_numpy())) for x in val[FEATURES].to_numpy()),
                test_opened=args.release_confirmed)
if args.release_confirmed:
    test = pd.read_csv(BASE/'data/student/locked-test-features.csv').merge(pd.read_csv(BASE/'data/teacher/locked-test-labels.csv'),on='sample_id',validate='one_to_one')
    evidence['test'] = scores(test[target],model.predict_proba(test[FEATURES])[:,1],threshold)
    evidence['test_profiles_seen'] = sum(tuple(x) in set(map(tuple,train[FEATURES].to_numpy())) for x in test[FEATURES].to_numpy())
def json_safe(value):
    if isinstance(value, dict):
        return {k: json_safe(v) for k,v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value

(OUT/'experiment-evidence.json').write_text(json.dumps(json_safe(evidence), indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
assert abs(posterior-evidence['sklearn_p']) < 1e-12
assert evidence['validation']['accuracy'] == 1
print(json.dumps(evidence,ensure_ascii=False,indent=2))
