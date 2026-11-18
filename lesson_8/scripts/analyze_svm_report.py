"""Reproduce course experiments for the final report without changing course files."""
from pathlib import Path
import sys, json, hashlib, pickle, argparse, platform, types
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tmp/report-runtime'))
sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
import pandas as pd
import scipy, sklearn
course_path=ROOT/'scripts/lab_utils.py'
course_source=course_path.read_text(encoding='utf-8')
# The course helper assumes an older, deeper repository path. REPO is unused
# in all its experiments. Adapt only that assignment in memory; retain files.
course_module=types.ModuleType('lab_utils');course_module.__file__=str(course_path)
sys.modules['lab_utils']=course_module
exec(compile(course_source,str(course_path),'exec'),course_module.__dict__)
from lab_utils import (load_development,geometry_experiment,parameter_experiment,
    scaling_experiment,select_validation_configs,noise_experiment,metrics,evaluate_locked)

def run(open_test=False):
    out=ROOT/'results/svm-report/analysis';out.mkdir(parents=True,exist_ok=True)
    train,val=load_development()
    geo=geometry_experiment(train)
    grid,models=parameter_experiment(train,val)
    scaling,changes=scaling_experiment(train,val)
    configs=select_validation_configs(grid)
    for key in ['table','candidates','changes','contradiction']:
        geo[key].to_csv(out/f'geometry-{key}.csv',index=False,encoding='utf-8-sig')
    grid.to_csv(out/'parameter-grid.csv',index=False,encoding='utf-8-sig')
    scaling.to_csv(out/'scaling.csv',index=False,encoding='utf-8-sig')
    noise={family:noise_experiment(models[key],train,val) for family,key in configs.items()}
    for family,table in noise.items():table.to_csv(out/f'noise-{family}.csv',index=False,encoding='utf-8-sig')
    freeze={'features':['pelvic_incidence','degree_spondylolisthesis'],
            'scaler_fit':'Original 186 training records only',
            'selection_rule':'Within each family: max validation balanced accuracy, then min C, then min gamma',
            'configs':configs,'test_threshold':0,'refit_with_validation':False}
    # Configuration file is written before optional test evaluation.
    (out/'frozen-configurations.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2),encoding='utf-8')
    test=None
    if open_test:
        test=evaluate_locked(configs,freeze_confirmed=True,open_test=True)
        test.to_csv(out/'locked-test-results.csv',index=False,encoding='utf-8-sig')
    sources=['svm-pbl-intro-with-kernel.pptx','student-worksheet.md','svm-lab.ipynb',
             'scripts/lab_utils.py','data/student/train.csv','data/student/validation.csv']
    report={'versions':{'python':platform.python_version(),'numpy':np.__version__,
                       'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},
            'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
            'actual_rerun':True,'test_opened':open_test,'configs':configs,'scaling_max_score_changes':changes,
            'runtime_compatibility':'In-memory REPO=BASE assignment replaces unused legacy parent-depth lookup; original course file unchanged.',
            'geometry_w':geo['model'].coef_[0].tolist(),'geometry_b':float(geo['model'].intercept_[0]),
            'validation':{family:metrics(val.abnormal,models[key].decision_function(val[freeze['features']]))
                          for family,key in configs.items()}}
    (out/'run-manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    with (out/'development-results.pkl').open('wb') as f:
        pickle.dump({'train':train,'validation':val,'geo':geo,'grid':grid,'models':models,
                     'scaling':scaling,'changes':changes,'configs':configs,'noise':noise,
                     'manifest':report,'test':test},f)
    assert len(train)==186 and len(val)==62
    assert configs['linear'][1]==1 and configs['rbf'][1:]==(10.,10.)
    assert all(abs(x-y)<1e-5 for x,y in zip(geo['candidates'].min_signed_distance,[.382723,.956807,.382723]))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--open-test',action='store_true')
    run(parser.parse_args().open_test)
