"""Scientific figures for the final SVM report; inputs are rerun course results."""
from pathlib import Path
import os, pickle, math, json
from analyze_svm_report import ROOT
OUT=ROOT/'results/svm-report'
FIG=OUT/'figures';FIG.mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'.tmp/report-layout/matplotlib')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from sklearn.metrics import roc_curve
from lab_utils import make_model, FEATURES

T='#167B83';O='#BA6435';I='#252B30';G='#68727A'
plt.rcParams.update({'font.family':'Arial','font.size':8,'text.color':I,
    'axes.labelcolor':I,'axes.edgecolor':'#7C858A','xtick.color':G,'ytick.color':G,
    'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.6,
    'xtick.major.width':.6,'ytick.major.width':.6,'xtick.major.size':3,
    'ytick.major.size':3,'svg.fonttype':'none','pdf.fonttype':42,
    'savefig.facecolor':'white','figure.facecolor':'white'})

def save(fig,name):
    for ext in ['png','svg','pdf']:fig.savefig(FIG/f'{name}.{ext}',dpi=380)
    plt.close(fig)

def panel(ax,letter,title):
    ax.text(-.13,1.06,letter,transform=ax.transAxes,fontsize=11,fontweight='bold',color=I)
    ax.set_title(title,loc='left',fontsize=8.5,pad=9)

def two(height=2.65):
    fig,axs=plt.subplots(1,2,figsize=(7,height))
    fig.subplots_adjust(left=.09,right=.98,bottom=.22,top=.84,wspace=.38)
    return fig,axs

def scatter(ax,X,y,size=14,legend=False):
    for label,col,mark,name in [(0,T,'o','NO'),(1,O,'^','AB')]:
        sel=np.asarray(y)==label
        ax.scatter(X[sel,0],X[sel,1],s=size,c=col,marker=mark,alpha=.8,
                   edgecolors='white',linewidths=.25,label=name,zorder=3)
    if legend:ax.legend(frameon=False,fontsize=7,loc='upper left',handlelength=1)

def plot_all():
    with (OUT/'analysis/development-results.pkl').open('rb') as f:d=pickle.load(f)
    tr,va,geo,grid,models=d['train'],d['validation'],d['geo'],d['grid'],d['models']
    notes={}
    X=tr[FEATURES].to_numpy();y=tr.abnormal.to_numpy()
    fig,axs=two(2.8)
    low,high=np.percentile(X,[0,98],axis=0);pad=.10*np.maximum(high-low,.001)
    for ax,letter,title in zip(axs,['a','b'],['Complete training range','Central display (all points fitted)']):
        scatter(ax,X,y,16,True)
        ax.set(xlabel='Pelvic incidence (source scale)',ylabel='Spondylolisthesis (source scale)')
        if letter=='b':ax.set_xlim(low[0]-pad[0],high[0]+pad[0]);ax.set_ylim(low[1]-pad[1],high[1]+pad[1])
        panel(ax,letter,title)
    outside=int(np.any((X<low-pad)|(X>high+pad),axis=1).sum())
    axs[1].text(.98,.95,f'{outside} records outside display',transform=axs[1].transAxes,
                 ha='right',fontsize=7,color=G)
    notes['full_train_local_display_outside']=outside
    save(fig,'fig01_data')

    z=geo['z'];ym=2*geo['subset'].abnormal.to_numpy()-1
    w=geo['model'].coef_[0];b=float(geo['model'].intercept_[0]);xx=np.linspace(-2.1,1.8,200)
    fig,axs=two(2.9)
    ax=axs[0]
    for off,col,ls in [(-.6,'#A6B2B6','--'),(0,I,'-'),(.6,O,'--')]:
        ax.plot(xx,-(w[0]*xx+b+off)/w[1],color=col,ls=ls,lw=1,label=f'b offset {off:+.1f}')
    scatter(ax,z,geo['subset'].abnormal,24)
    sv=geo['model'].support_;ax.scatter(z[sv,0],z[sv,1],s=80,facecolors='none',edgecolors=I,lw=.8)
    ax.set(xlim=(-2.1,1.8),ylim=(-1.3,2.2),xlabel='z1',ylabel='z2');ax.set_aspect('equal')
    panel(ax,'a','Three zero-error candidates')
    ax=axs[1];v=geo['candidates'].min_signed_distance.to_numpy()
    bars=ax.bar(['−0.6','0','+0.6'],v,color=['#C1CBCE',T,'#C1CBCE'],width=.56)
    for p,num in zip(bars,v):ax.text(p.get_x()+p.get_width()/2,num+.035,f'{num:.3f}',ha='center',fontsize=8)
    ax.set(xlabel='Intercept offset',ylabel='Minimum signed distance',ylim=(0,1.15))
    panel(ax,'b','Nearest-point geometric margin');save(fig,'fig02_margin')

    fig,axs=two(2.8);base=geo['model'].decision_function(z)
    from sklearn.svm import SVC
    for sid,col,ls in [('baseline',I,'-'),('V072',T,':'),('V061',O,'--')]:
        if sid=='baseline':m=geo['model']
        else:
            keep=geo['subset'].sample_id.to_numpy()!=sid
            m=SVC(kernel='linear',C=10000,tol=1e-9,max_iter=200000).fit(z[keep],geo['subset'].abnormal.to_numpy()[keep])
        ww=m.coef_[0];bb=m.intercept_[0]
        axs[0].plot(xx,-(ww[0]*xx+bb)/ww[1],c=col,ls=ls,lw=1.25,label='Original' if sid=='baseline' else f'Delete {sid}')
        if sid!='baseline':
            delta=np.abs(m.decision_function(z)-base)
            axs[1].plot(range(8),delta,c=col,ls=ls,marker='o',ms=3,lw=1,label=f'Delete {sid}')
    scatter(axs[0],z,geo['subset'].abnormal,20)
    axs[0].set(xlim=(-2.1,1.8),ylim=(-1.3,2.2),xlabel='z1',ylabel='z2');axs[0].set_aspect('equal')
    axs[1].set_xticks(range(8));axs[1].set_xticklabels(geo['subset'].sample_id,rotation=45,ha='right',fontsize=6.3)
    axs[1].set(ylabel='Absolute change in score',ylim=(-.015,.49))
    axs[1].legend(frameon=False,fontsize=7)
    panel(axs[0],'a','Refit with the original scaler fixed');panel(axs[1],'b','Changes on the original eight records')
    fig.subplots_adjust(bottom=.28);save(fig,'fig03_support')

    fig,axs=two(2.65);m=np.linspace(-1.5,2.2,400)
    axs[0].plot(m,np.maximum(0,1-m),c=T,lw=1.6,label='Hinge loss')
    axs[0].plot(m,(m<0).astype(float),c=G,lw=1.1,ls='--',label='0/1 error (off boundary)')
    axs[0].axvline(0,c='#C8CFD1',lw=.6);axs[0].axvline(1,c='#C8CFD1',lw=.6,ls=':')
    axs[0].set(xlabel='Labelled score y·f',ylabel='Loss',xlim=(-1.5,2.2),ylim=(-.06,2.65));axs[0].legend(frameon=False,fontsize=7)
    vals=[-.5,.4,1,1.8];loss=np.maximum(0,1-np.array(vals));bars=axs[1].bar(range(4),loss,color=[O,T,'#B6C6C9','#B6C6C9'],width=.55)
    for p,a in zip(bars,loss):axs[1].text(p.get_x()+p.get_width()/2,a+.035,f'{a:g}',ha='center')
    axs[1].set_xticks(range(4));axs[1].set_xticklabels(['−0.5','0.4','1','1.8'])
    axs[1].set(xlabel='Labelled score y·f',ylabel='Hinge loss',ylim=(0,1.8))
    panel(axs[0],'a','A correct prediction may still incur loss');panel(axs[1],'b','Worksheet arithmetic examples')
    save(fig,'fig04_hinge')

    fig,axs=two(2.65)
    ax=axs[0];q=np.linspace(-.3,2.3,100);ax.plot(q,q-1,c=I,lw=1.25)
    ax.scatter([0],[ -1],c=T,s=35,zorder=3);ax.scatter([2],[1],c=O,marker='^',s=35,zorder=3)
    ax.axhline(0,c='#AAB5B7',lw=.7);ax.axvline(1,c=G,ls=':',lw=.8)
    ax.annotate('x = 0, y = −1',(0,-1),xytext=(5,-19),textcoords='offset points',fontsize=7)
    ax.annotate('x = 2, y = +1',(2,1),xytext=(-73,10),textcoords='offset points',fontsize=7)
    ax.set(xlabel='Input x',ylabel='f(x) = x − 1',ylim=(-1.6,1.65))
    panel(ax,'a','Primal solution: w = 1, b = −1')
    a=np.linspace(0,1,300);ax=axs[1];ax.plot(a,2*a-2*a*a,c=T,lw=1.6)
    ax.scatter([.5],[.5],c=O,s=26,zorder=3);ax.axvline(.5,c=G,ls=':',lw=.7)
    ax.annotate('a = 0.5  →  w = 2a = 1',(.5,.5),xytext=(.13,.56),textcoords='data',fontsize=7)
    ax.set(xlabel='Shared dual coefficient a',ylabel='Q(a) = 2a − 2a²',ylim=(-.02,.65),xlim=(0,1))
    panel(ax,'b','Dual solution: same separating function');save(fig,'fig05_duality')

    lin=grid[grid.kernel=='linear']
    fig,axs=plt.subplots(1,3,figsize=(7,2.65));fig.subplots_adjust(left=.075,right=.98,bottom=.23,top=.83,wspace=.55)
    axs[0].loglog(lin.C,lin.linear_width,c=T,marker='o',ms=3,lw=1.3)
    axs[0].set(xlabel='C',ylabel='Canonical band width');axs[0].set_xticks([.01,1,100]);axs[0].set_xticklabels(['0.01','1','100'])
    axs[1].semilogx(lin.C,lin.mean_hinge,c=T,marker='o',ms=3,lw=1.3);axs[1].set(xlabel='C',ylabel='Mean hinge loss')
    axs[2].semilogx(lin.C,lin.train_balanced_accuracy,c=G,ls='--',marker='o',ms=3,label='Training')
    axs[2].semilogx(lin.C,lin.val_balanced_accuracy,c=T,marker='o',ms=3,label='Validation')
    axs[2].set(xlabel='C',ylabel='Balanced accuracy',ylim=(.45,.91));axs[2].legend(frameon=False,fontsize=6.5,loc='lower right')
    for ax,letter,title in zip(axs,'abc',['Reference band','Training violations','Held-out behaviour']):panel(ax,letter,title)
    save(fig,'fig06_linear_c')

    Z=geo['scaler'].transform(tr[FEATURES]);lo,hi=np.percentile(Z,[0,98],axis=0);pad=.12*np.maximum(hi-lo,.001);lo-=pad;hi+=pad
    gx,gy=np.meshgrid(np.linspace(lo[0],hi[0],190),np.linspace(lo[1],hi[1],190))
    zz=np.c_[gx.ravel(),gy.ravel()];raw=geo['scaler'].inverse_transform(zz)
    fig,axs=plt.subplots(1,3,figsize=(7,2.85));fig.subplots_adjust(left=.075,right=.985,bottom=.23,top=.82,wspace=.28)
    outside=int(np.any((Z<lo)|(Z>hi),axis=1).sum());notes['kernel_display_outside']=outside
    for ax,key,letter,title in zip(axs,[('linear',1.,.1),('poly',1.,.1),('rbf',1.,.1)],'abc',['Linear','Polynomial, degree 2','RBF, γ = 0.1']):
        model=models[key];score=model.decision_function(pd.DataFrame(raw,columns=FEATURES)).reshape(gx.shape)
        ax.contourf(gx,gy,score>=0,levels=[-.5,.5,1.5],colors=['#E8F2F2','#FAEDE3'])
        ax.contour(gx,gy,score,levels=[-1,0,1],colors=[G,I,G],linewidths=[.55,1,.55],linestyles=['--','-','--'])
        scatter(ax,Z,y,8);ax.set(xlim=lo[[0]].tolist()+hi[[0]].tolist(),ylim=(lo[1],hi[1]),xlabel='z1',ylabel='z2')
        panel(ax,letter,title)
        ax.text(.98,.025,f'{outside} outside display',transform=ax.transAxes,ha='right',fontsize=6,color=G)
    save(fig,'fig07_kernels')

    fig=plt.figure(figsize=(7,2.8));gs=fig.add_gridspec(1,4,width_ratios=[1.5,1,1,.065],left=.075,right=.955,bottom=.24,top=.84,wspace=.55)
    ax=fig.add_subplot(gs[0]);r=np.linspace(0,4,400)
    for gam,col in [(.1,T),(1,O),(10,I)]:ax.plot(r,np.exp(-gam*r*r),c=col,lw=1.5,label=f'γ = {gam:g}')
    ax.axhline(math.exp(-1),c='#AFB8BB',lw=.7,ls=':');ax.set(xlabel='Distance r',ylabel='Kernel similarity K',xlim=(0,4),ylim=(0,1.04))
    ax.legend(frameon=False,fontsize=7);panel(ax,'a','Distance-dependent similarity')
    gx,gy=np.meshgrid(np.linspace(-4,4,250),np.linspace(-4,4,250))
    for col,gam,letter in [(1,.1,'b'),(2,1,'c')]:
        ax=fig.add_subplot(gs[col]);im=ax.imshow(np.exp(-gam*(gx*gx+gy*gy)),origin='lower',extent=[-4,4,-4,4],cmap='YlGnBu',vmin=0,vmax=1)
        ax.add_patch(Circle((0,0),1/math.sqrt(gam),edgecolor='white',facecolor='none',ls='--',lw=.9))
        ax.scatter([0],[0],s=13,c='white',edgecolors=I,lw=.4);ax.set_xticks([-4,0,4]);ax.set_yticks([-4,0,4]);ax.set_xlabel('Δz1');panel(ax,letter,f'γ = {gam:g}')
    cb=fig.colorbar(im,cax=fig.add_subplot(gs[3]),ticks=[0,.5,1]);cb.outline.set_linewidth(.5)
    save(fig,'fig08_gamma')

    rbf=grid[grid.kernel=='rbf'];fig,axs=two(2.5)
    for ax,table,xcol,letter,title in [(axs[0],rbf[rbf.C==1].sort_values('gamma'),'gamma','a','C = 1: change gamma'),(axs[1],rbf[rbf.gamma==10].sort_values('C'),'C','b','γ = 10: change C')]:
        ax.semilogx(table[xcol],table.train_balanced_accuracy,c=G,ls='--',marker='o',ms=3.7,label='Training')
        ax.semilogx(table[xcol],table.val_balanced_accuracy,c=T,marker='o',ms=3.7,label='Validation')
        ax.set(xlabel='γ' if xcol=='gamma' else 'C',ylabel='Balanced accuracy',ylim=(.45,.97));ax.minorticks_off()
        panel(ax,letter,title)
    axs[0].legend(frameon=False,fontsize=7,loc='lower right');save(fig,'fig09_slices')
    mat=rbf.pivot(index='C',columns='gamma',values='val_balanced_accuracy')
    fig,ax=plt.subplots(figsize=(7,2.45));fig.subplots_adjust(left=.15,right=.87,bottom=.25,top=.86)
    im=ax.imshow(mat.to_numpy(),cmap='YlGnBu',vmin=.5,vmax=.82,aspect='auto')
    for ii in range(4):
        for jj in range(4):
            val=mat.iloc[ii,jj];ax.text(jj,ii,f'{val:.3f}',ha='center',va='center',fontsize=9,color='white' if val>.72 else I)
    ax.set_xticks(range(4));ax.set_xticklabels([f'{x:g}' for x in mat.columns]);ax.set_yticks(range(4));ax.set_yticklabels([f'{x:g}' for x in mat.index]);ax.set(xlabel='gamma',ylabel='C')
    fig.colorbar(im,ax=ax,fraction=.04,pad=.04,label='Validation balanced accuracy')
    save(fig,'fig10_grid')

    scores={};tr2=tr.copy();va2=va.copy();tr2[FEATURES[0]]*=100;va2[FEATURES[0]]*=100
    for scaled in [False,True]:
        for unit,tt,vv in [('original',tr,va),('x100',tr2,va2)]:
            model=make_model('rbf',1,.1,scaled).fit(tt[FEATURES],tt.abnormal)
            scores[(scaled,unit)]=model.decision_function(vv[FEATURES])
    fig,axs=two(2.8)
    for ax,scaled,letter,title in [(axs[0],False,'a','Without scaling'),(axs[1],True,'b','Training-fitted standardization')]:
        x=scores[(scaled,'original')];yy=scores[(scaled,'x100')];col=T if scaled else O
        ax.scatter(x,yy,s=15,color=col,edgecolors='white',linewidth=.3,alpha=.85)
        lo=min(x.min(),yy.min());hi=max(x.max(),yy.max());pad=.1*max(hi-lo,.01)
        ax.plot([lo-pad,hi+pad],[lo-pad,hi+pad],c=G,lw=.8,ls='--')
        ax.set(xlim=(lo-pad,hi+pad),ylim=(lo-pad,hi+pad),xlabel='Score, original unit',ylabel='Score, x1 multiplied by 100')
        ax.set_aspect('equal');panel(ax,letter,title)
        ax.text(.04,.94,'max |Δf| = '+('1.78e-14' if scaled else '1.538'),transform=ax.transAxes,fontsize=7,va='top')
    save(fig,'fig11_scaling')

    fig,axs=plt.subplots(1,3,figsize=(7,2.8));fig.subplots_adjust(left=.075,right=.98,bottom=.26,top=.82,wspace=.55)
    for ax,family,letter in [(axs[0],'linear','a'),(axs[1],'rbf','b')]:
        mm=d['manifest']['validation'][family];mat=np.array([[mm['TN'],mm['FP']],[mm['FN'],mm['TP']]])
        ax.imshow(mat,cmap='YlGnBu',vmin=0,vmax=42)
        for i in range(2):
            for j in range(2):ax.text(j,i,str(mat[i,j]),ha='center',va='center',fontsize=12,color='white' if mat[i,j]>22 else I)
        ax.set_xticks([0,1]);ax.set_xticklabels(['NO','AB']);ax.set_yticks([0,1]);ax.set_yticklabels(['NO','AB'])
        ax.set(xlabel='Predicted',ylabel='Observed');panel(ax,letter,'Linear' if family=='linear' else 'RBF')
    for family,col in [('linear',T),('rbf',O)]:
        score=models[d['configs'][family]].decision_function(va[FEATURES]);fpr,tpr,_=roc_curve(va.abnormal,score)
        auc=d['manifest']['validation'][family]['roc_auc'];axs[2].plot(fpr,tpr,c=col,lw=1.3,label=f'{family}: {auc:.3f}')
    axs[2].plot([0,1],[0,1],c='#BAC3C6',ls='--',lw=.7)
    axs[2].set(xlabel='False-positive rate',ylabel='True-positive rate',xlim=(0,1),ylim=(0,1.03));axs[2].legend(frameon=False,fontsize=6.4,loc='lower right');panel(axs[2],'c','Validation ROC')
    save(fig,'fig12_evaluation')

    fig,axs=two(2.75)
    for family,col in [('linear',T),('rbf',O)]:
        tab=d['noise'][family];x=100*tab.noise_sd_fraction
        axs[0].plot(x,tab.mean_flip_rate,c=col,marker='o',ms=3.5,lw=1.4,label=family)
        axs[1].errorbar(x,tab.mean_balanced_accuracy,yerr=tab.sd_balanced_accuracy,c=col,marker='o',ms=3.5,lw=1.2,capsize=2,label=family)
    axs[0].set(xlabel='Noise SD / training SD (%)',ylabel='Mean prediction flip rate',ylim=(-.008,.26))
    axs[1].set(xlabel='Noise SD / training SD (%)',ylabel='Mean balanced accuracy',ylim=(.59,.86))
    for ax in axs:ax.set_xticks([0,5,10,20]);ax.legend(frameon=False,fontsize=7)
    panel(axs[0],'a','Fixed models, perturbed validation inputs');panel(axs[1],'b','Error bars: SD across noise repeats')
    save(fig,'fig13_noise')
    (OUT/'analysis/figure-notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Saved 13 figures in PNG, SVG and PDF formats.')

if __name__=='__main__':plot_all()
