"""Render compact, journal-style figures for the revised classroom report."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.tmp'/'ensemble_report_deps'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier

SOURCE=ROOT/'results/ensemble-classroom-report'/'results'
OUT=ROOT/'results'/'ensemble-report'
FIG=OUT/'figures'
FIG.mkdir(parents=True,exist_ok=True)
TEAL='#177F88';ORANGE='#B56332';GRAY='#8B959B';BLACK='#283138';BLUE='#526F90'
COLORS={'single_tree':GRAY,'bagging':BLUE,'random_forest':TEAL,'adaboost':'#AC975A',
        'gradient_boosting':ORANGE,'logistic':BLACK,'rbf_svm':'#8A7692'}
LABEL={'single_tree':'Tree','bagging':'Bagging','random_forest':'RF','adaboost':'AdaBoost',
       'gradient_boosting':'GB','logistic':'LR','rbf_svm':'RBF-SVM'}
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,'axes.titlesize':8,
    'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#98A4AC','axes.linewidth':.6,
    'xtick.color':'#53616B','ytick.color':'#53616B','text.color':BLACK,'axes.labelcolor':BLACK,
    'xtick.labelsize':7.2,'ytick.labelsize':7.2,'legend.fontsize':7,'lines.linewidth':1.3,
    'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white',
    'pdf.fonttype':42,'ps.fonttype':42,'mathtext.fontset':'stix'})


def read(name,file):return pd.read_csv(SOURCE/name/file)


def panel(ax,letter,title):
    ax.set_title(title,loc='left',pad=9,fontweight='normal')
    ax.text(-.13,1.07,letter,transform=ax.transAxes,fontweight='bold',fontsize=10)


def save(fig,name):
    fig.savefig(FIG/(name+'.svg'),bbox_inches='tight',pad_inches=.035)
    fig.savefig(FIG/(name+'.png'),dpi=260,bbox_inches='tight',pad_inches=.035)
    plt.close(fig)
    print(name,flush=True)


def data():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.5))
    for ax,name,folder,features,label,letter in [
        (axs[0],'WDBC','data',['worst perimeter','mean concave points'],'malignant','a'),
        (axs[1],'CTG','data-ctg',['Mode','ALTV'],'pathologic','b')]:
        d=pd.read_csv(ROOT/folder/'student'/'train.csv')
        for y,c,mark in [(0,TEAL,'o'),(1,ORANGE,'^')]:
            dd=d[d[label]==y]
            ax.scatter(dd[features[0]],dd[features[1]],s=9 if name=='WDBC' else 7,alpha=.6,
                       c=c,marker=mark,edgecolors='none',label=f'y={y} (n={len(dd)})')
        ax.set(xlabel=features[0],ylabel=features[1]);ax.legend(frameon=False,loc='upper left')
        panel(ax,letter,f'{name}: training observations')
    fig.tight_layout(w_pad=3)
    save(fig,'fig01_data')


def tree():
    d=pd.read_csv(ROOT/'data'/'student'/'train.csv');features=[c for c in d if c not in ['sample_id','malignant']]
    t=DecisionTreeClassifier(max_depth=2,random_state=1010).fit(d[features],d.malignant).tree_
    fig,ax=plt.subplots(figsize=(7.1,2.9));ax.axis('off');ax.set(xlim=(0,1),ylim=(0,1))
    pos={0:(.5,.88),1:(.25,.54),4:(.75,.54),2:(.12,.16),3:(.37,.16),5:(.62,.16),6:(.87,.16)}
    for p,left,right in [(0,1,4),(1,2,3),(4,5,6)]:
        for c,yes in [(left,True),(right,False)]:
            a,b=pos[p],pos[c];color=ORANGE if (p,c) in [(0,4),(4,6)] else '#BCC5CA'
            ax.plot([a[0],b[0]],[a[1]-.06,b[1]+.065],color=color,lw=1.6 if color==ORANGE else .8,zorder=0)
            ax.text((a[0]+b[0])/2+(-.02 if yes else .02),(a[1]+b[1])/2,'yes' if yes else 'no',
                    ha='center',fontsize=7,color=color)
    for n,(x,y) in pos.items():
        if t.children_left[n]>=0:
            text=f'{features[t.feature[n]]}\n'+r'$\leq$'+f' {t.threshold[n]:.5f}'
            fc='#F7F9F9';ec='#929FA7'
        else:
            v=t.value[n,0];p=v[1]/v.sum();count=t.weighted_n_node_samples[n]
            n1=round(count*p);n0=round(count)-n1
            text=f'benign {n0} / malignant {n1}\n'+r'$\hat{p}$'+f' = {p:.3f}'
            fc='#FBF4EE' if n==6 else '#FFFFFF';ec=ORANGE if n==6 else '#A9B5BC'
        ax.text(x,y,text,ha='center',va='center',fontsize=7.3,
                bbox=dict(boxstyle='round,pad=.48',fc=fc,ec=ec,lw=.7))
    save(fig,'fig02_tree')


def depth():
    fig,axs=plt.subplots(2,2,figsize=(7.1,3.9),gridspec_kw={'height_ratios':[1.2,1]})
    for j,name in enumerate(['wdbc','ctg']):
        d=read(name,'tree-depth.csv');ax=axs[0,j];x=np.arange(5)
        ax.plot(x,d.train_accuracy,'o-',ms=3,color=GRAY,label='Train')
        ax.plot(x,d.accuracy,'o-',ms=3,color=TEAL,label='Validation')
        ax.set_xticks(x,['1','2','3','4','None']);ax.set(xlabel='Maximum depth',ylabel='Accuracy',ylim=(.88,1.01))
        ax.legend(frameon=False,loc='lower right');panel(ax,'ab'[j],name.upper()+': depth control')
        roots=read(name,'bootstrap-roots.csv').feature.value_counts().sort_values()
        ax=axs[1,j];ax.barh(range(len(roots)),roots.values,color=TEAL,height=.5)
        ax.set_yticks(range(len(roots)),roots.index,fontsize=6.8);ax.set(xlabel='Root selections in 10 resamples',xlim=(0,8))
        for i,v in enumerate(roots.values):ax.text(v+.12,i,str(v),va='center',fontsize=7)
        panel(ax,'cd'[j],name.upper()+': bootstrap roots')
    fig.tight_layout(h_pad=2,w_pad=3)
    save(fig,'fig03_depth')


def voting():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.5));ax=axs[0]
    values=[.2,.6,.65,(.2+.6+.65)/3]
    ax.bar(range(4),values,width=.55,color=[GRAY,GRAY,GRAY,TEAL])
    ax.axhline(.5,color=ORANGE,ls='--',lw=.9,label='Threshold 0.5')
    ax.set_xticks(range(4),['Model 1','Model 2','Model 3','Mean']);ax.set(ylabel='Positive-class probability',ylim=(0,.83))
    for i,v in enumerate(values):ax.text(i,v+.025,f'{v:.3f}',ha='center',fontsize=7)
    ax.legend(frameon=False,loc='upper left');panel(ax,'a','Worksheet sample B')
    b=np.arange(1,301);ax=axs[1]
    for rho,color in [(0,TEAL),(.3,BLUE),(.8,ORANGE),(1,GRAY)]:
        ax.plot(b,rho+(1-rho)/b,label=fr'$\rho={rho:g}$',color=color)
    ax.set(xlabel='Number of models B',ylabel=r'$\mathrm{Var}(\bar f)/\sigma^2$',ylim=(0,1.05),xlim=(1,300))
    ax.legend(frameon=False,loc='center right');panel(ax,'b','Equal-variance theoretical model')
    fig.tight_layout(w_pad=3);save(fig,'fig04_voting')


def bootstrap():
    d=pd.read_csv(SOURCE/'bootstrap-simulation.csv');fig,axs=plt.subplots(1,2,figsize=(7.1,2.5))
    small=d[d.n==5];v,c=np.unique(small.unique_fraction,return_counts=True)
    axs[0].bar(v,c/len(small),width=.095,color=TEAL)
    axs[0].axvline(1-(4/5)**5,color=ORANGE,ls='--',lw=1,label='Expected: 0.67232')
    axs[0].set(xlabel='Fraction of distinct records',ylabel='Relative frequency',xlim=(0,1.05))
    axs[0].legend(frameon=False);panel(axs[0],'a','Bootstrap: n = 5')
    for n,col in [(341,TEAL),(1279,ORANGE)]:
        ds=d[d.n==n];axs[1].hist(ds.oob_fraction,bins=25,density=True,alpha=.48,color=col,label=f'n = {n}')
    axs[1].axvline(np.exp(-1),color=BLACK,ls='--',lw=.9,label=r'$e^{-1}$')
    axs[1].set(xlabel='Out-of-bag fraction',ylabel='Density');axs[1].legend(frameon=False)
    panel(axs[1],'b','Classroom sample sizes')
    fig.tight_layout(w_pad=3);save(fig,'fig05_bootstrap')


def forest():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.5))
    for ax,name,letter in zip(axs,['wdbc','ctg'],'ab'):
        d=read(name,'tree-count-curve.csv')
        for m in ['bagging','random_forest']:
            s=d[d.model==m];ax.plot(s.n_trees,s.validation_roc_auc,'o-',ms=3,color=COLORS[m],label=LABEL[m])
        ax.set(xscale='log',xlabel='Number of trees',ylabel='Validation ROC-AUC',ylim=(.82,1.01))
        ax.set_xticks([1,10,50,100,300],['1','10','50','100','300']);ax.legend(frameon=False,loc='lower right')
        panel(ax,letter,name.upper())
    fig.tight_layout(w_pad=3);save(fig,'fig06_forest')


def stability():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.6));models=['single_tree','bagging','random_forest']
    for j,name in enumerate(['wdbc','ctg']):
        d=read(name,'prediction-stability-row.csv').set_index('model').loc[models]
        for k,col in enumerate(['prediction_sd_mean','class_flip_rate']):
            ax=axs[k];x=np.arange(3)+j*4
            ax.bar(x,d[col],color=[COLORS[m] for m in models],width=.58)
            for xi,v in zip(x,d[col]):ax.text(xi,v+(0.002 if k==0 else .007),f'{v:.3f}' if k==0 else f'{v:.1%}',ha='center',fontsize=6.6)
    for k,ax in enumerate(axs):
        ax.set_xticks([0,1,2,4,5,6],['Tree','Bag','RF','Tree','Bag','RF'])
        ax.set(xlabel='WDBC                       CTG',ylabel='Mean prediction SD' if k==0 else 'Fraction ever changing class')
        ax.set_ylim(0,.105 if k==0 else .30);panel(ax,'ab'[k],'Training-row bootstrap, R = 30')
    fig.tight_layout(w_pad=3);save(fig,'fig07_stability')


def ada():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.5))
    for ax,name,letter in zip(axs,['wdbc','ctg'],'ab'):
        d=read(name,'adaboost-weight-trace.csv')
        ax.plot(d.stage,d.wrong_mass_before,'o-',ms=3,color=TEAL,label='Before update')
        ax.plot(d.stage,d.wrong_mass_after,'o--',ms=2,color=ORANGE,label='After update')
        ax.set(xlabel='Boosting round',ylabel='Weight mass of current mistakes',ylim=(0,.56),xticks=[1,3,5,7,10])
        ax.legend(frameon=False,loc='lower right');panel(ax,letter,name.upper()+': same mistakes, changed weights')
    fig.tight_layout(w_pad=3);save(fig,'fig08_adaboost')


def gb():
    fig,axs=plt.subplots(2,2,figsize=(7.1,3.0));colors={.03:BLUE,.1:TEAL,.3:ORANGE}
    for j,name in enumerate(['wdbc','ctg']):
        d=read(name,'boosting-curves.csv')
        for rate,color in colors.items():
            g=d[np.isclose(d.learning_rate,rate)]
            axs[0,j].plot(g.stage,g.validation_log_loss,color=color,label=fr'$\eta={rate}$')
            axs[1,j].plot(g.stage,g.validation_auc,color=color)
            if rate==.1:axs[0,j].plot(g.stage,g.train_log_loss,color=color,ls='--',lw=.9,label='Train, 0.1')
        for row in range(2):axs[row,j].set(xlabel='Boosting round',xlim=(1,500))
        axs[0,j].set_ylabel('Log loss');axs[1,j].set_ylabel('Validation ROC-AUC')
        axs[0,j].legend(frameon=False,ncol=2,fontsize=6,handlelength=1.5,columnspacing=.8)
        panel(axs[0,j],'ab'[j],name.upper()+': probability loss')
        panel(axs[1,j],'cd'[j],name.upper()+': ranking')
    fig.tight_layout(h_pad=1.7,w_pad=3);save(fig,'fig09_gradient')


def importance():
    fig,axs=plt.subplots(2,2,figsize=(7.1,3.9))
    for j,name in enumerate(['wdbc','ctg']):
        d=read(name,'feature-importance.csv')
        for row,col in enumerate(['impurity_importance','permutation_auc_drop_mean']):
            top=d.nlargest(5,col).sort_values(col);ax=axs[row,j]
            ax.barh(range(5),top[col],xerr=top.permutation_auc_drop_sd if row else None,
                color=TEAL if row else GRAY,height=.55,error_kw={'lw':.6,'capsize':1.8,'ecolor':BLACK})
            ax.set_yticks(range(5),top.feature,fontsize=6.8)
            ax.set_xlabel('Normalized impurity decrease' if row==0 else 'Validation AUC decrease')
            panel(ax,'abcd'[row*2+j],name.upper()+(': impurity' if row==0 else ': permutation'))
    fig.tight_layout(w_pad=3,h_pad=2);save(fig,'fig10_importance')


def comparison():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.9));order=list(LABEL)
    for ax,name,letter in zip(axs,['wdbc','ctg'],'ab'):
        cv=read(name,'cross-validation.csv').set_index('model').loc[order];fold=read(name,'cv-folds.csv')
        for i,m in enumerate(order):
            vals=fold[fold.model==m].roc_auc.to_numpy()
            ax.scatter(vals,i+np.linspace(-.11,.11,5),color=COLORS[m],s=9,alpha=.45)
            ax.errorbar(cv.loc[m,'roc_auc_mean'],i,xerr=cv.loc[m,'roc_auc_sd'],fmt='o',ms=3.3,
                        color=COLORS[m],capsize=2,lw=1)
        ax.set_yticks(range(7),[LABEL[m] for m in order]);ax.invert_yaxis()
        ax.set(xlabel='CV ROC-AUC (mean and fold SD)',xlim=(.845 if name=='wdbc' else .65,1.009))
        panel(ax,letter,name.upper()+(': stratified folds' if name=='wdbc' else ': recording-grouped folds'))
    fig.tight_layout(w_pad=3);save(fig,'fig11_comparison')


def groups():
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.6));models=['single_tree','random_forest','logistic']
    row=read('ctg','ctg-row-cv-diagnostic.csv');group=read('ctg','cv-folds.csv')
    for j,(d,label,color) in enumerate([(row,'Row split',ORANGE),(group,'Recording split',TEAL)]):
        means=[d[d.model==m].roc_auc.mean() for m in models];sds=[d[d.model==m].roc_auc.std(ddof=1) for m in models]
        axs[0].bar(np.arange(3)+(j-.5)*.32,means,width=.30,yerr=sds,color=color,label=label,
                   error_kw={'lw':.6,'capsize':2,'ecolor':BLACK})
    axs[0].set_xticks(range(3),[LABEL[m] for m in models]);axs[0].set(ylim=(.65,1.045),ylabel='CV ROC-AUC')
    axs[0].legend(frameon=False,loc='lower right');panel(axs[0],'a','CTG: evaluation unit')
    models=['single_tree','bagging','random_forest']
    for j,(mode,label,color) in enumerate([('row','Row bootstrap',GRAY),('recording','Recording bootstrap',TEAL)]):
        d=read('ctg',f'prediction-stability-{mode}.csv').set_index('model')
        vals=[d.loc[m,'prediction_sd_mean'] for m in models]
        axs[1].bar(np.arange(3)+(j-.5)*.32,vals,width=.30,color=color,label=label)
    axs[1].set_xticks(range(3),[LABEL[m] for m in models]);axs[1].set_ylabel('Mean prediction SD')
    axs[1].legend(frameon=False,fontsize=6.5);panel(axs[1],'b','CTG: training-resampling unit')
    fig.tight_layout(w_pad=3);save(fig,'fig12_groups')


if __name__=='__main__':
    for f in [data,tree,depth,voting,bootstrap,forest,stability,ada,gb,importance,comparison,groups]:f()
