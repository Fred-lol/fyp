"""Reproducible training on synthetic scenarios; separate scenario holdout."""
import sys, json, random
from pathlib import Path
from time import perf_counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from optimization.ml_ranker import features, FEATURES, MODEL_PATH
from optimization.optimizer import ENHANCED_STRATEGIES, _pack_enhanced_once, _finalise_deep_loading_sequence, _compactness_score
from optimization.validation import validate_plan

def scenario(seed):
    rng=random.Random(seed)
    lorry=dict(internal_length=rng.choice([150,200,300,430]),internal_width=rng.choice([100,120,180,210]),internal_height=rng.choice([80,120,180]),max_weight=3000)
    types=[(30,35,25),(50,40,30),(65,45,35),(80,50,40)]
    boxes=[]
    for i in range(rng.randint(4,18)):
        l,w,h=rng.choice(types)
        boxes.append(dict(order_id=1,box_profile_id=types.index((l,w,h))+1,box_instance=i+1,length=l,width=w,height=h,loaded_weight=l*w*h/1000))
    return lorry,boxes

def labels(lorry,boxes):
    costs=[]
    for ordering,position in ENHANCED_STRATEGIES:
        p=_pack_enhanced_once(lorry,boxes,ordering,position,float('inf'))
        if p: _finalise_deep_loading_sequence(p,lorry)
        if p and validate_plan(p,lorry,sum(b['loaded_weight'] for b in boxes),expected_boxes=boxes)[0]:
            costs.append((0,*_compactness_score(p,lorry)))
        else: costs.append((1,))
    unique=sorted(set(costs))
    return [unique.index(c)/max(1,len(unique)-1) for c in costs]

if __name__=='__main__':
    started=perf_counter(); X=[];Y=[]
    for seed in range(100):
        l,b=scenario(seed);X.append(features(l,b));Y.append(labels(l,b))
        if seed%10==0: print('Generated scenario',seed,flush=True)
    X=np.asarray(X);Y=np.asarray(Y);train=80
    mean=X[:train].mean(axis=0);scale=X[:train].std(axis=0);scale[scale<1e-9]=1
    A=np.column_stack([np.ones(train),(X[:train]-mean)/scale])
    penalty=np.eye(A.shape[1]);penalty[0,0]=0
    coef=np.linalg.solve(A.T@A+penalty,A.T@Y[:train])
    pred=np.column_stack([np.ones(20),(X[train:]-mean)/scale])@coef
    chosen=np.argmin(pred,axis=1)
    report=dict(training_scenarios=80,held_out_scenarios=20,seed_range=[0,99],model='multi-output ridge regression',target='relative rank of independently validated strategy results',held_out_mean_rank=float(Y[train:][np.arange(20),chosen].mean()),original_first_strategy_mean_rank=float(Y[train:,0].mean()),seconds=perf_counter()-started)
    MODEL_PATH.write_text(json.dumps(dict(version=1,features=FEATURES,strategies=ENHANCED_STRATEGIES,mean=mean.tolist(),scale=scale.tolist(),coefficients=coef.tolist(),training=report),indent=2)+'\n')
    print(json.dumps(report,indent=2))
