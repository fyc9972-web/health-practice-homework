"""Reproduce worksheet A-H using student development data only.

Run from the project root: python ensemble-classroom-report/scripts/run_experiments.py
Optional dependencies may live in .tmp/ensemble_report_deps.
"""
from pathlib import Path
import sys
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
ROOT = Path(__file__).resolve().parents[3]
DEPS = ROOT / ".tmp" / "ensemble_report_deps"
if DEPS.exists():
    sys.path.insert(0, str(DEPS))
import json
import hashlib
import importlib.util
import platform
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.base import clone
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, log_loss, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from threadpoolctl import threadpool_limits

REPORT = Path(__file__).resolve().parents[1]
OUT = REPORT / "results"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 1010
spec = importlib.util.spec_from_file_location("classroom_demo", ROOT / "scripts" / "demo_ensemble.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def write(frame, path):
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def scores(model, X):
    return model.decision_function(X) if hasattr(model, "decision_function") else model.predict_proba(X)[:, 1]


def metrics(model, X, y):
    pred = model.predict(X)
    s = scores(model, X)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"roc_auc": roc_auc_score(y, s), "ap": average_precision_score(y, s),
            "balanced_accuracy": balanced_accuracy_score(y, pred),
            "accuracy": accuracy_score(y, pred), "sensitivity": tp / (tp + fn),
            "specificity": tn / (tn + fp), "tn": tn, "fp": fp, "fn": fn, "tp": tp}


def resampling_stability(X, y, Xv, resamples, out, mode):
    summary = []
    individual = []
    for name in ("single_tree", "bagging", "random_forest"):
        ps = np.asarray([clone(demo.models()[name]).fit(X.iloc[idx], y.iloc[idx]).predict_proba(Xv)[:, 1]
                         for idx in resamples])
        np.savez_compressed(out / f"stability-{mode}-{name}.npz", probabilities=ps)
        sd = ps.std(axis=0, ddof=0)
        share = (ps >= .5).mean(axis=0)
        flip = (share > 0) & (share < 1)
        summary.append({"model": name, "resampling": mode, "prediction_sd_mean": sd.mean(),
                        "prediction_sd_max": sd.max(), "class_flip_rate": flip.mean(), "refits": len(resamples)})
        individual.extend({"model": name, "validation_index": i, "prediction_sd": sd[i],
                           "class_flip": int(flip[i]), "mean_probability": ps[:, i].mean()} for i in range(len(Xv)))
        print(f"  stability {mode}: {name}", flush=True)
    write(pd.DataFrame(summary), out / f"prediction-stability-{mode}.csv")
    write(pd.DataFrame(individual), out / f"prediction-stability-individual-{mode}.csv")


def run_dataset(name):
    out = OUT / name
    out.mkdir(exist_ok=True)
    train, valid, features, label, group = demo.load(name)
    X, y = train[features], train[label]
    Xv, yv = valid[features], valid[label]
    dev = pd.concat([train, valid], ignore_index=True)
    Xd, yd = dev[features], dev[label]
    if group:
        assert set(train[group]).isdisjoint(valid[group])
    print(f"START {name}: train={len(train)}, validation={len(valid)}", flush=True)
    info = {"name": name, "label": label, "features": features, "n_features": len(features),
            "n_train": len(y), "n_validation": len(yv), "train_positive": int(y.sum()),
            "validation_positive": int(yv.sum()), "group": group,
            "n_groups_train": int(train[group].nunique()) if group else None,
            "n_groups_validation": int(valid[group].nunique()) if group else None}
    (out / "data-info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    rows = []
    models = {}
    predictions = {"sample_id": valid["sample_id"], "y": yv}
    if group:
        predictions[group] = valid[group]
    for key, model in demo.models().items():
        model.fit(X, y)
        models[key] = model
        rows.append({"model": key, **metrics(model, Xv, yv)})
        predictions[f"{key}_score"] = scores(model, Xv)
        predictions[f"{key}_class"] = model.predict(Xv)
    write(pd.DataFrame(rows), out / "model-comparison.csv")
    write(pd.DataFrame(predictions), out / "validation-predictions.csv")
    print("  fixed validation models done", flush=True)

    cv = StratifiedGroupKFold(5, shuffle=True, random_state=SEED) if group else StratifiedKFold(5, shuffle=True, random_state=SEED)
    folds = list(cv.split(Xd, yd, dev[group] if group else None))
    fold_rows = []
    for key, factory in demo.models().items():
        for fold, (tr, va) in enumerate(folds):
            if group:
                assert set(dev.iloc[tr][group]).isdisjoint(dev.iloc[va][group])
            model = clone(factory).fit(Xd.iloc[tr], yd.iloc[tr])
            fold_rows.append({"model": key, "fold": fold + 1, **metrics(model, Xd.iloc[va], yd.iloc[va]),
                              "n_train": len(tr), "n_validation": len(va)})
        print(f"  CV {key}", flush=True)
    fold_frame = pd.DataFrame(fold_rows)
    write(fold_frame, out / "cv-folds.csv")
    summary = fold_frame.groupby("model", sort=False).agg(
        roc_auc_mean=("roc_auc", "mean"), roc_auc_sd=("roc_auc", "std"),
        ap_mean=("ap", "mean"), ap_sd=("ap", "std"),
        balanced_accuracy_mean=("balanced_accuracy", "mean"), balanced_accuracy_sd=("balanced_accuracy", "std"))
    write(summary.reset_index(), out / "cross-validation.csv")

    depth_rows = []
    for depth in (1, 2, 3, 4, None):
        tree = DecisionTreeClassifier(max_depth=depth, random_state=SEED).fit(X, y)
        depth_rows.append({"max_depth": str(depth), "leaves": tree.get_n_leaves(),
                           "train_accuracy": accuracy_score(y, tree.predict(X)), **metrics(tree, Xv, yv)})
    write(pd.DataFrame(depth_rows), out / "tree-depth.csv")
    tree2 = DecisionTreeClassifier(max_depth=2, random_state=SEED).fit(X, y)
    (out / "tree-depth-2.txt").write_text(export_text(tree2, feature_names=features, decimals=5), encoding="utf-8")
    rng = np.random.default_rng(SEED)
    resamples = [rng.choice(len(y), len(y), replace=True) for _ in range(30)]
    root_rows = []
    for i, idx in enumerate(resamples[:10]):
        tree = DecisionTreeClassifier(max_depth=2, random_state=SEED).fit(X.iloc[idx], y.iloc[idx])
        root_rows.append({"repeat": i+1, "feature": features[tree.tree_.feature[0]],
                          "threshold": tree.tree_.threshold[0]})
    write(pd.DataFrame(root_rows), out / "bootstrap-roots.csv")
    resampling_stability(X, y, Xv, resamples, out, "row")
    if group:
        gids = train[group].unique()
        group_rows = {g: np.flatnonzero(train[group].to_numpy() == g) for g in gids}
        grng = np.random.default_rng(SEED)
        group_samples = [np.concatenate([group_rows[g] for g in grng.choice(gids, len(gids), replace=True)])
                         for _ in range(30)]
        resampling_stability(X, y, Xv, group_samples, out, "recording")

    write(demo.tree_count_curve(X, y, Xv, yv), out / "tree-count-curve.csv")
    # Match implementations and all settings except node feature randomization.
    matched = []
    for max_features in (1.0, "sqrt"):
        forest = RandomForestClassifier(n_estimators=100, max_features=max_features, random_state=SEED, n_jobs=1).fit(X, y)
        matched.append({"max_features": str(max_features), **metrics(forest, Xv, yv)})
    write(pd.DataFrame(matched), out / "matched-feature-randomization.csv")
    print("  tree count and matched randomization done", flush=True)

    curve_rows = []
    for rate in (.03, .1, .3):
        gb = GradientBoostingClassifier(learning_rate=rate, n_estimators=500, max_depth=3, random_state=SEED).fit(X, y)
        for stage, (pt, pv) in enumerate(zip(gb.staged_predict_proba(X), gb.staged_predict_proba(Xv)), 1):
            curve_rows.append({"learning_rate": rate, "stage": stage,
                               "train_log_loss": log_loss(y, pt, labels=[0,1]),
                               "validation_log_loss": log_loss(yv, pv, labels=[0,1]),
                               "validation_auc": roc_auc_score(yv, pv[:,1])})
    write(pd.DataFrame(curve_rows), out / "boosting-curves.csv")
    ada = models["adaboost"]
    weights = np.ones(len(y)) / len(y)
    ada_rows = []
    for stage, (est, alpha) in enumerate(zip(ada.estimators_[:10], ada.estimator_weights_[:10]), 1):
        wrong = est.predict(X.to_numpy()) != y.to_numpy()
        err = weights[wrong].sum()
        new_weights = weights * np.exp(alpha * wrong)
        new_weights /= new_weights.sum()
        ada_rows.append({"stage":stage, "weighted_error":err, "estimator_weight":alpha,
                         "wrong_mass_before":err, "wrong_mass_after":new_weights[wrong].sum(),
                         "wrong_count":int(wrong.sum())})
        weights = new_weights
    write(pd.DataFrame(ada_rows), out / "adaboost-weight-trace.csv")
    print("  boosting curves and AdaBoost weights done", flush=True)

    importance = demo.feature_importance(X, y, Xv, yv)
    write(importance, out / "feature-importance.csv")
    corr = X.corr()
    corr.to_csv(out / "training-correlation.csv", encoding="utf-8-sig")
    pair_rows = [{"feature_1":features[i], "feature_2":features[j], "r":corr.iloc[i,j]}
                 for i in range(len(features)) for j in range(i+1,len(features)) if abs(corr.iloc[i,j])>.9]
    write(pd.DataFrame(pair_rows, columns=["feature_1","feature_2","r"]), out / "high-correlation-pairs.csv")
    print("  importance and correlations done", flush=True)

    # Conditional paired validation bootstrap, not a final test or a retraining interval.
    bs_rows = []
    bs_rng = np.random.default_rng(SEED)
    yy = yv.to_numpy()
    p_rf = scores(models["random_forest"], Xv)
    p_lr = scores(models["logistic"], Xv)
    if group:
        gids = valid[group].unique()
        mapping = {g:np.flatnonzero(valid[group].to_numpy()==g) for g in gids}
    for r in range(1000):
        idx = (np.concatenate([mapping[g] for g in bs_rng.choice(gids,len(gids),replace=True)])
               if group else bs_rng.choice(len(yy),len(yy),replace=True))
        if len(np.unique(yy[idx])) < 2:
            continue
        a = roc_auc_score(yy[idx], p_rf[idx])
        b = roc_auc_score(yy[idx], p_lr[idx])
        bs_rows.append({"repeat":r+1,"rf_auc":a,"lr_auc":b,"difference_rf_minus_lr":a-b})
    write(pd.DataFrame(bs_rows), out / "conditional-validation-bootstrap.csv")

    if group:
        naive_rows=[]
        row_folds = list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(Xd, yd))
        for key in ("single_tree", "random_forest", "logistic"):
            for fold, (tr,va) in enumerate(row_folds,1):
                overlap = len(set(dev.iloc[tr][group]) & set(dev.iloc[va][group]))
                model=clone(demo.models()[key]).fit(Xd.iloc[tr],yd.iloc[tr])
                naive_rows.append({"model":key,"fold":fold,"overlapping_recordings":overlap,
                                   **metrics(model,Xd.iloc[va],yd.iloc[va])})
        write(pd.DataFrame(naive_rows), out / "ctg-row-cv-diagnostic.csv")
    print(f"DONE {name}", flush=True)


def main():
    sim_rows=[]
    for n in (5,341,1279):
        rng=np.random.default_rng(SEED)
        for r in range(1000):
            unique=len(np.unique(rng.choice(n,n,replace=True)))/n
            sim_rows.append({"n":n,"repeat":r+1,"unique_fraction":unique,"oob_fraction":1-unique,
                             "expected_oob":(1-1/n)**n})
    write(pd.DataFrame(sim_rows),OUT / "bootstrap-simulation.csv")
    with threadpool_limits(limits=1):
        for name in ("wdbc","ctg"):
            run_dataset(name)
    inputs = [ROOT/"materials/student-worksheet.md", ROOT / "slides" / "ensemble-pbl.pptx", ROOT / "scripts" / "demo_ensemble.py"]
    inputs += [ROOT / folder / "student" / fn for folder in ("data","data-ctg") for fn in ("train.csv","validation.csv")]
    manifest={"python":platform.python_version(),"sklearn":sklearn.__version__,"numpy":np.__version__,
              "scipy":scipy.__version__,"seed":SEED,"timestamp_utc":datetime.now(timezone.utc).isoformat(),
              "input_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              "test_labels_read":False,"cv_folds":5,"stability_refits":30,"importance_repeats":20,
              "conditional_validation_bootstrap_attempts":1000,
              "note":"No teacher or locked-test files are opened. Reference results are not used as new measurements."}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("ALL EXPERIMENTS COMPLETE",flush=True)


if __name__=="__main__":
    main()
