"""Produce original vector and raster scientific figures from the saved experiments."""
from pathlib import Path
import sys
import importlib.util
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".tmp" / "ensemble_report_deps"))
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.tree import DecisionTreeClassifier

REPORT = Path(__file__).resolve().parents[1]
RESULTS = REPORT / "results"
FIG = REPORT / "figures"
FIG.mkdir(exist_ok=True)
for path in font_manager.findSystemFonts():
    if "NotoSansSC-VF" in path:
        font_manager.fontManager.addfont(path)
        FONT = font_manager.FontProperties(fname=path).get_name()
        break
else:
    FONT = "Microsoft YaHei"
plt.rcParams.update({"font.family":FONT, "font.size":10, "axes.titlesize":12,
    "axes.labelsize":10, "axes.spines.top":False, "axes.spines.right":False,
    "axes.edgecolor":"#CBD4DA", "axes.labelcolor":"#263C4C", "text.color":"#18344A",
    "xtick.color":"#526571", "ytick.color":"#526571", "axes.unicode_minus":False,
    "svg.fonttype":"none", "savefig.facecolor":"white", "figure.facecolor":"white"})
NAVY="#18344A"
TEAL="#16877F"
ORANGE="#D87A43"
BLUE="#557BA4"
GRAY="#8998A2"
COLORS={"single_tree":GRAY,"bagging":BLUE,"random_forest":TEAL,"adaboost":"#B49B58",
        "gradient_boosting":ORANGE,"logistic":NAVY,"rbf_svm":"#8C6DA3"}
LABELS={"single_tree":"单树","bagging":"Bagging","random_forest":"随机森林",
        "adaboost":"AdaBoost","gradient_boosting":"梯度提升","logistic":"逻辑回归","rbf_svm":"RBF-SVM"}
DATASETS=("wdbc","ctg")


def read(name,file):
    return pd.read_csv(RESULTS/name/file)


def save(fig,name):
    fig.savefig(FIG/(name+".svg"),bbox_inches="tight",pad_inches=.16)
    fig.savefig(FIG/(name+".png"),dpi=220,bbox_inches="tight",pad_inches=.16)
    plt.close(fig)
    print(name,flush=True)


def panel(ax,letter,title):
    ax.set_title(title,loc="left",pad=13,fontweight="bold")
    ax.text(-.09,1.07,letter,transform=ax.transAxes,fontweight="bold",fontsize=14)


def box(ax,x,y,w,h,text,color=TEAL,fill="#F0F7F6",size=11):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.02",
                               ec=color,fc=fill,lw=1.1))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=size,linespacing=1.6)


def arrow(ax,a,b,color=GRAY):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=13,lw=1.3,color=color))


def overview():
    fig,axs=plt.subplots(1,2,figsize=(12,5.2),gridspec_kw={"width_ratios":[1,1.15]})
    for ax in axs: ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    ax=axs[0]
    panel(ax,"a","相同问题，两套互补数据")
    box(ax,.04,.69,.91,.20,"WDBC：30 特征，恶性为正类\n训练 341  /  验证 114",NAVY,"#F0F4F7")
    box(ax,.04,.40,.91,.20,"CTG：21 特征，病理型为正类\n训练 1,279  /  验证 424；录音不跨集合")
    box(ax,.04,.08,.91,.21,"开发集五折 CV  +  固定验证集\nLR / SVM 折内标准化；测试标签封存",GRAY,"#F7F8F9",10)
    arrow(ax,(.5,.69),(.5,.61)); arrow(ax,(.5,.40),(.5,.30))
    ax=axs[1]
    panel(ax,"b","从机制到证据的研究路线")
    box(ax,.2,.81,.60,.13,"单棵树：拟合能力与不稳定性",NAVY,"#F0F4F7",10)
    box(ax,.02,.49,.45,.18,"Bagging / 随机森林\n独立训练 → 平均\n主要降低方差",TEAL,size=10)
    box(ax,.54,.49,.44,.18,"Boosting\n顺序学习 → 修正\n主要增强拟合能力",ORANGE,"#FCF3EC",10)
    arrow(ax,(.39,.81),(.25,.68)); arrow(ax,(.62,.81),(.75,.68))
    box(ax,.10,.08,.80,.22,"共同评价\n排序与分类表现 · 重训稳定性\n解释成本 · 验证范围",NAVY,"#F0F4F7",10)
    arrow(ax,(.25,.49),(.38,.31)); arrow(ax,(.75,.49),(.63,.31))
    fig.tight_layout(w_pad=3)
    save(fig,"fig01-study-design")


def tree_example():
    path=ROOT/"data"/"student"/"train.csv"
    train=pd.read_csv(path)
    features=[c for c in train if c not in ("sample_id","malignant")]
    tree=DecisionTreeClassifier(max_depth=2,random_state=1010).fit(train[features],train.malignant)
    t=tree.tree_
    fig,ax=plt.subplots(figsize=(12,5.1))
    ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    positions={0:(.5,.88),1:(.25,.57),4:(.75,.57),2:(.12,.21),3:(.37,.21),5:(.62,.21),6:(.87,.21)}
    for parent,left,right in ((0,1,4),(1,2,3),(4,5,6)):
        for child,yes in ((left,True),(right,False)):
            a=positions[parent];b=positions[child]
            highlight=(parent,child) in ((0,4),(4,6))
            ax.plot([a[0],b[0]],[a[1]-.065,b[1]+.065],lw=3 if highlight else 1.1,
                    color=TEAL if highlight else "#BDCAD2",zorder=0)
            ax.text((a[0]+b[0])/2+(-.018 if yes else .018),(a[1]+b[1])/2,
                    "是" if yes else "否",ha="center",fontsize=10,color=TEAL if highlight else GRAY)
    for node,(x,y) in positions.items():
        if t.children_left[node]>=0:
            text=f"{features[t.feature[node]]}\n≤ {t.threshold[node]:.5f}？"
            ax.text(x,y,text,ha="center",va="center",fontsize=10,
                    bbox={"boxstyle":"round,pad=.65","fc":"#F1F6F8","ec":NAVY,"lw":1})
        else:
            v=t.value[node][0]; p=v[1]/v.sum(); n=t.weighted_n_node_samples[node]
            n1=round(n*p);n0=round(n)-n1
            ax.text(x,y,f"良性 {n0} · 恶性 {n1}\nP(恶性) = {p:.3f}",ha="center",va="center",fontsize=10,
                    bbox={"boxstyle":"round,pad=.65","fc":"#EAF5F2" if node==6 else "#F8F9FA",
                          "ec":TEAL if node==6 else "#BDCAD2","lw":1.5 if node==6 else 1})
    ax.text(.5,.005,"课堂样本：worst perimeter = 120；mean concave points = 0.08 → 右、右 → 112 / 115 ≈ 0.974",
            ha="center",fontsize=11,color=TEAL,fontweight="bold")
    save(fig,"fig02-reading-a-tree")


def depths():
    fig,axs=plt.subplots(2,2,figsize=(11.5,8.3))
    for j,name in enumerate(DATASETS):
        d=read(name,"tree-depth.csv")
        ax=axs[0,j]; x=np.arange(len(d))
        ax.plot(x,d.train_accuracy,"o-",color=NAVY,label="训练准确率",lw=2)
        ax.plot(x,d.accuracy,"o-",color=TEAL,label="验证准确率",lw=2)
        ax.set_xticks(x,["1","2","3","4","不限"])
        ax.set(xlabel="树最大深度",ylabel="准确率",ylim=(min(d.accuracy.min(),.85)-.03,1.015))
        ax.legend(frameon=False,fontsize=9,loc="lower right")
        ax.grid(axis="y",alpha=.15)
        panel(ax,"ab"[j],name.upper()+"：训练变好，验证未必同步")
        roots=read(name,"bootstrap-roots.csv").feature.value_counts().sort_values()
        ax=axs[1,j]
        ax.barh(np.arange(len(roots)),roots.values,color=BLUE,height=.58)
        ax.set_yticks(np.arange(len(roots)),roots.index,fontsize=9)
        ax.set(xlabel="10 次训练 bootstrap 中被选为根节点的次数",xlim=(0,max(roots.values)+1))
        for i,v in enumerate(roots.values): ax.text(v+.08,i,str(v),va="center")
        ax.spines[["left","bottom"]].set_visible(False)
        panel(ax,"cd"[j],name.upper()+"：换训练样本，第一道问题会变")
    fig.tight_layout(h_pad=3,w_pad=4)
    save(fig,"fig03-tree-instability")


def voting_variance():
    fig,axs=plt.subplots(1,2,figsize=(11.5,4.3))
    ax=axs[0]; ps=[.2,.6,.65,(.2+.6+.65)/3]
    ax.bar(np.arange(4),ps,color=[GRAY,GRAY,GRAY,TEAL],width=.58)
    ax.axhline(.5,color=ORANGE,lw=1.4,ls="--",label="分类阈值 0.5")
    ax.set_xticks(range(4),["模型 1\n判 0","模型 2\n判 1","模型 3\n判 1","概率平均\n判 0"])
    ax.set(ylabel="正类概率",ylim=(0,.85))
    for i,p in enumerate(ps): ax.text(i,p+.025,f"{p:.3f}",ha="center")
    ax.legend(frameon=False,loc="upper left",fontsize=9)
    panel(ax,"a","工作单 B：硬投票判 1，软投票判 0")
    ax=axs[1]; B=np.arange(1,301)
    for rho,color in ((0,BLUE),(.3,TEAL),(.8,ORANGE),(1,GRAY)):
        ax.plot(B,rho+(1-rho)/B,color=color,lw=2,label=f"ρ = {rho:g}")
    ax.set(xlabel="模型数 B",ylabel="平均预测方差 / 单模型方差",xlim=(1,300),ylim=(0,1.04))
    ax.legend(frameon=False,fontsize=9)
    panel(ax,"b","理论示意：相关性决定降方差的下限")
    fig.tight_layout(w_pad=3)
    save(fig,"fig04-voting-and-variance")


def bootstrap():
    data=pd.read_csv(RESULTS/"bootstrap-simulation.csv")
    fig,axs=plt.subplots(1,2,figsize=(11.5,4))
    d=data[data.n==5]
    vals,counts=np.unique(d.unique_fraction,return_counts=True)
    axs[0].bar(vals,counts/1000,width=.10,color=BLUE)
    axs[0].axvline(1-(4/5)**5,color=ORANGE,ls="--",label="精确期望 67.232%")
    axs[0].set(xlabel="一次抽样中不同原记录的比例",ylabel="1,000 次模拟的相对频数",xlim=(0,1.05))
    axs[0].legend(frameon=False,fontsize=9)
    panel(axs[0],"a","小样本 n=5：不要直接套 63.2%")
    for n,color in ((341,TEAL),(1279,BLUE)):
        d=data[data.n==n]
        axs[1].hist(d.oob_fraction,bins=24,alpha=.48,color=color,label=f"n={n}，均值 {d.oob_fraction.mean():.3f}",density=True)
    axs[1].axvline(np.exp(-1),color=ORANGE,ls="--",label="大样本近似 36.8%")
    axs[1].set(xlabel="一次 bootstrap 的 OOB 比例",ylabel="概率密度")
    axs[1].legend(frameon=False,fontsize=9)
    panel(axs[1],"b","课堂规模：袋外比例围绕理论值波动")
    fig.tight_layout(w_pad=3)
    save(fig,"fig05-bootstrap")


def comparisons():
    fig,axs=plt.subplots(1,2,figsize=(11.8,5))
    order=list(LABELS)
    for ax,name,letter in zip(axs,DATASETS,"ab"):
        cv=read(name,"cross-validation.csv").set_index("model").loc[order]
        folds=read(name,"cv-folds.csv")
        for i,key in enumerate(order):
            vals=folds[folds.model==key].roc_auc.to_numpy()
            ax.scatter(vals,i+np.linspace(-.12,.12,len(vals)),s=18,color=COLORS[key],alpha=.45,zorder=2)
            ax.errorbar(cv.loc[key,"roc_auc_mean"],i,xerr=cv.loc[key,"roc_auc_sd"],fmt="o",color=COLORS[key],capsize=3,lw=1.6,ms=6,zorder=3)
        ax.set_yticks(range(len(order)),[LABELS[k] for k in order])
        ax.invert_yaxis();ax.set(xlabel="开发集五折 ROC-AUC（点：各折；横线：均值 ± SD）",xlim=(max(.65,folds.roc_auc.min()-.025),1.008))
        ax.grid(axis="x",alpha=.15)
        panel(ax,letter,name.upper()+("：分层 CV" if name=="wdbc" else "：按录音分组 CV"))
    fig.tight_layout(w_pad=3)
    save(fig,"fig06-model-comparison")


def stability():
    fig,axs=plt.subplots(2,2,figsize=(11.5,7.5))
    order=["single_tree","bagging","random_forest"]
    for j,name in enumerate(DATASETS):
        s=read(name,"prediction-stability-row.csv").set_index("model").loc[order]
        for row,(col,ylabel) in enumerate((("prediction_sd_mean","平均预测概率 SD"),("class_flip_rate","发生类别翻转的验证样本比例"))):
            ax=axs[row,j]; values=s[col].to_numpy()
            ax.bar(range(3),values,color=[COLORS[k] for k in order],width=.56)
            ax.set_xticks(range(3),[LABELS[k] for k in order]);ax.set_ylabel(ylabel)
            ax.set_ylim(0,max(values)*1.3)
            for i,v in enumerate(values):
                ax.text(i,v+max(values)*.055,f"{v:.3f}" if row==0 else f"{v:.1%}",ha="center",fontsize=10)
            panel(ax,"abcd"[row*2+j],name.upper()+"：相同 30 份训练行重抽样")
    fig.tight_layout(h_pad=3,w_pad=3)
    save(fig,"fig07-prediction-stability")


def tree_count():
    fig,axs=plt.subplots(1,2,figsize=(11.5,4))
    for ax,name,letter in zip(axs,DATASETS,"ab"):
        d=read(name,"tree-count-curve.csv")
        for key in ("bagging","random_forest"):
            g=d[d.model==key]
            ax.plot(g.n_trees,g.validation_roc_auc,"o-",color=COLORS[key],label=LABELS[key],lw=2)
        ax.set(xscale="log",xlabel="树数（对数刻度）",ylabel="固定验证集 ROC-AUC",ylim=(d.validation_roc_auc.min()-.02,1.005))
        ax.set_xticks([1,10,50,100,300],["1","10","50","100","300"])
        ax.legend(frameon=False,fontsize=9);ax.grid(axis="y",alpha=.15)
        panel(ax,letter,name.upper()+"：加树的边际收益")
    fig.tight_layout(w_pad=3)
    save(fig,"fig08-tree-count")


def boosting():
    fig,axs=plt.subplots(2,2,figsize=(11.5,7.7))
    colors={.03:BLUE,.1:TEAL,.3:ORANGE}
    for j,name in enumerate(DATASETS):
        d=read(name,"boosting-curves.csv")
        for rate,color in colors.items():
            g=d[np.isclose(d.learning_rate,rate)]
            axs[0,j].plot(g.stage,g.validation_log_loss,color=color,label=f"η={rate}",lw=1.8)
            if rate==.1:
                axs[0,j].plot(g.stage,g.train_log_loss,color=color,ls="--",lw=1,label="η=0.1 训练")
            axs[1,j].plot(g.stage,g.validation_auc,color=color,lw=1.8,label=f"η={rate}")
        for row in range(2):
            axs[row,j].set_xlabel("提升轮数");axs[row,j].grid(axis="y",alpha=.15)
            axs[row,j].legend(frameon=False,fontsize=8.5,ncol=2)
        axs[0,j].set_ylabel("Log-loss（越低越好）")
        axs[1,j].set_ylabel("验证 ROC-AUC（越高越好）")
        panel(axs[0,j],"ab"[j],name.upper()+"：概率损失随轮数变化")
        panel(axs[1,j],"cd"[j],name.upper()+"：排序表现不必与损失同步")
    fig.tight_layout(h_pad=3,w_pad=3)
    save(fig,"fig09-boosting-curves")


def importance():
    fig,axs=plt.subplots(2,2,figsize=(12,9))
    for j,name in enumerate(DATASETS):
        d=read(name,"feature-importance.csv")
        for row,col in enumerate(("impurity_importance","permutation_auc_drop_mean")):
            top=d.nlargest(7,col).sort_values(col)
            ax=axs[row,j]
            error=top.permutation_auc_drop_sd if row else None
            ax.barh(range(len(top)),top[col],xerr=error,color=BLUE if row==0 else TEAL,height=.63,
                    error_kw={"lw":1,"capsize":2,"ecolor":GRAY})
            ax.set_yticks(range(len(top)),top.feature,fontsize=9)
            ax.set_xlabel("归一化切分贡献" if row==0 else "验证 AUC 降幅（均值 ± 置换 SD）")
            ax.axvline(0,color=GRAY,lw=.8)
            panel(ax,"abcd"[row*2+j],name.upper()+"："+("不纯度重要性" if row==0 else "重复 20 次的置换重要性"))
    fig.tight_layout(w_pad=4,h_pad=3)
    save(fig,"fig10-feature-importance")


def group_diagnostics():
    fig,axs=plt.subplots(1,2,figsize=(11.8,4.7))
    row=read("ctg","ctg-row-cv-diagnostic.csv")
    group=read("ctg","cv-folds.csv")
    keys=["single_tree","random_forest","logistic"]
    for offset,(d,label,color) in enumerate(((row,"按行分层（有录音重叠）",ORANGE),(group,"按录音分组",TEAL))):
        means=[d[d.model==k].roc_auc.mean() for k in keys]
        sds=[d[d.model==k].roc_auc.std(ddof=1) for k in keys]
        axs[0].bar(np.arange(3)+(offset-.5)*.33,means,width=.31,yerr=sds,label=label,color=color,
                    error_kw={"lw":1,"capsize":3,"ecolor":NAVY})
    axs[0].set_xticks(range(3),[LABELS[k] for k in keys]);axs[0].set(ylim=(0.65,1.045),ylabel="CV ROC-AUC（均值 ± 折间 SD）")
    axs[0].legend(frameon=False,fontsize=9,loc="lower right")
    panel(axs[0],"a","CTG：划分改变了评价问题")
    for offset,(mode,label,color) in enumerate((("row","训练片段行 bootstrap",BLUE),("recording","训练录音整组 bootstrap",TEAL))):
        d=read("ctg",f"prediction-stability-{mode}.csv").set_index("model")
        vals=[d.loc[k,"prediction_sd_mean"] for k in keys[:2]]
        axs[1].bar(np.arange(2)+(offset-.5)*.33,vals,width=.31,color=color,label=label)
    axs[1].set_xticks(range(2),[LABELS[k] for k in keys[:2]])
    axs[1].set_ylabel("固定验证样本平均预测 SD")
    axs[1].legend(frameon=False,fontsize=9)
    panel(axs[1],"b","训练重抽样的单位也影响波动")
    fig.tight_layout(w_pad=3)
    save(fig,"fig11-ctg-group-diagnostics")


def correlation():
    names=["worst radius","worst perimeter","worst area"]
    corr=pd.read_csv(RESULTS/"wdbc"/"training-correlation.csv",index_col=0).loc[names,names]
    d=read("wdbc","feature-importance.csv").set_index("feature").loc[names]
    fig,axs=plt.subplots(1,2,figsize=(11.3,4))
    im=axs[0].imshow(corr,vmin=-1,vmax=1,cmap="BrBG")
    axs[0].set_xticks(range(3),["radius","perimeter","area"])
    axs[0].set_yticks(range(3),["worst radius","worst perimeter","worst area"])
    for i in range(3):
        for j in range(3): axs[0].text(j,i,f"{corr.iloc[i,j]:.3f}",ha="center",va="center",color="white" if abs(corr.iloc[i,j])>.6 else NAVY)
    fig.colorbar(im,ax=axs[0],fraction=.046,pad=.04)
    panel(axs[0],"a","WDBC：三个变量表达相近的大小信息")
    x=np.arange(3)
    axs[1].bar(x-.18,d.impurity_importance,width=.34,color=BLUE,label="不纯度重要性")
    axs[1].bar(x+.18,d.permutation_auc_drop_mean,width=.34,color=TEAL,label="置换 AUC 降幅")
    axs[1].set_xticks(x,["worst radius","worst perimeter","worst area"],rotation=15)
    axs[1].set_ylabel("各自定义下的重要性数值")
    axs[1].legend(frameon=False,fontsize=9)
    panel(axs[1],"b","定义与归一化方式不同，不能直接比较倍数")
    fig.tight_layout(w_pad=3)
    save(fig,"fig12-correlated-features")


if __name__=="__main__":
    for func in (overview,tree_example,depths,voting_variance,bootstrap,comparisons,stability,
                 tree_count,boosting,importance,group_diagnostics,correlation):
        func()
