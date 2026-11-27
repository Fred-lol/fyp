"""Replay the checked-in v3 benchmark using the same boxes and lorries."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from optimization.optimizer import generate_plan, gap_measurements
from optimization.cavities import internal_gaps, lateral_contact
from optimization.validation import validate_plan


def measures(result, lorry):
    if not result['success']:
        return {'success': False, 'message': result['message']}
    p = result['placements']
    return dict(success=True, **internal_gaps(p),
                depth_cm=gap_measurements(p,lorry)['occupied_length_cm'],
                side_contact_cm2=lateral_contact(p),
                stacked_boxes=sum(x['z']>1e-7 for x in p),
                seconds=result['metrics']['optimization_seconds'])


if __name__ == '__main__':
    old=json.loads((ROOT/'optimization/refinement_evaluation.json').read_text())
    rows=[]
    for case in old['scenarios']:
        lorry,boxes=case['lorry'],case['boxes']
        result=generate_plan(lorry,boxes)
        if result['success']:
            assert validate_plan(result['placements'],lorry,sum(b['loaded_weight'] for b in boxes),expected_boxes=boxes)[0]
        rows.append(dict(seed=case['seed'],before=measures(case['after'],lorry),after=measures(result,lorry),
                         after_coordinates=result.get('placements',[]),optimizer=result.get('metrics',{})))
        print('Evaluated',case['seed'],flush=True)
    both=[r for r in rows if r['before']['success'] and r['after']['success']]
    summary=dict(cases=len(rows),valid_before=sum(r['before']['success'] for r in rows),
                 valid_after=sum(r['after']['success'] for r in rows),
                 gap_improved=sum(r['after']['internal_gap_volume_cm3']<r['before']['internal_gap_volume_cm3'] for r in both),
                 gap_worsened=sum(r['after']['internal_gap_volume_cm3']>r['before']['internal_gap_volume_cm3'] for r in both))
    for metric in ['internal_gap_volume_cm3','depth_cm','side_contact_cm2','stacked_boxes','seconds']:
        summary[metric]={key:sum(r[key][metric] for r in both) for key in ['before','after']}
    (ROOT/'optimization/cavity_evaluation.json').write_text(json.dumps(dict(summary=summary,scenarios=rows),indent=2)+'\n')
    print(json.dumps(summary,indent=2))
