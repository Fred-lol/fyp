"""Compare identical held-out loads with and without physical refinement."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.train_strategy_model import scenario
from optimization.optimizer import generate_plan
from optimization.validation import validate_plan

def evaluate():
    rows=[]
    for seed in range(80,100):
        lorry,boxes=scenario(seed)
        row=dict(seed=seed,lorry=lorry,boxes=boxes)
        for key,enabled in [('before',False),('after',True)]:
            r=generate_plan(lorry,boxes,refine=enabled)
            if r['success']:
                assert validate_plan(r['placements'],lorry,sum(b['loaded_weight'] for b in boxes),expected_boxes=boxes)[0]
            row[key]=r
        rows.append(row)
    both=[r for r in rows if r['before']['success'] and r['after']['success']]
    metric=lambda r,k,m:r[k]['metrics'][m]
    summary=dict(source='Synthetic held-out cases; production-plan replay is a separate local artifact',cases=20,valid_before=sum(r['before']['success'] for r in rows),valid_after=sum(r['after']['success'] for r in rows),improved=sum(metric(r,'after','selected_score')<metric(r,'before','selected_score') for r in both),worse=sum(metric(r,'after','selected_score')>metric(r,'before','selected_score') for r in both))
    for name in ['internal_floor_row_gap_cm2','occupied_length_cm','stacked_box_count','optimization_seconds']:
        summary[name]={key:sum(metric(r,key,name) for r in both) for key in ['before','after']}
    Path('optimization/refinement_evaluation.json').write_text(json.dumps(dict(summary=summary,scenarios=rows),indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': evaluate()
