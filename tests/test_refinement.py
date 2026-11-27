from copy import deepcopy
from time import perf_counter
import pytest
from optimization.optimizer import generate_plan, _make_placement, _compactness_score, gap_measurements
from optimization.refinement import refine_plan, _sequence
from optimization.validation import validate_plan
from optimization.cavities import internal_gaps
from scripts.train_strategy_model import scenario

def protected(p,l):
 m=gap_measurements(p,l)
 return internal_gaps(p)['internal_gap_volume_cm3'],float(l['internal_length'])-max(x['x']+x['placed_length'] for x in p)

def test_refinement_rotates_and_repositions_without_mutating_original():
 truck=dict(internal_length=200,internal_width=100,internal_height=80,max_weight=1000)
 boxes=[dict(order_id=1,box_profile_id=i,box_instance=i,length=l,width=w,height=30,loaded_weight=20) for i,l,w in [(1,60,40),(2,40,60)]]
 original=_sequence([_make_placement(boxes[0],(140,0,0),(60,40,30)),_make_placement(boxes[1],(100,0,0),(40,60,30))])
 before=deepcopy(original)
 after,stats=refine_plan(original,truck,boxes,_compactness_score,perf_counter()+3,protected)
 assert original==before
 assert stats['refinement_moves']>0
 assert gap_measurements(after,truck)['occupied_length_cm']==60
 assert any(p['box_instance']==2 and p['placed_length']==60 for p in after)
 assert validate_plan(after,truck,40,expected_boxes=boxes)[0]
 assert _compactness_score(after,truck)<_compactness_score(original,truck)

def test_expired_refinement_budget_keeps_valid_coordinates():
 l,b=scenario(84);r=generate_plan(l,b,refine=False)
 after,stats=refine_plan(r['placements'],l,b,_compactness_score,perf_counter()-1,protected)
 assert after==r['placements']
 assert stats['refinement_moves']==0

@pytest.mark.parametrize('seed',[80,84,86,89,94,97,99])
def test_default_refinement_never_degrades_protected_geometry(seed):
 l,b=scenario(seed)
 before=generate_plan(l,b,refine=False);after=generate_plan(l,b)
 assert before['success'] and after['success']
 assert all(a<=v+1e-7 for a,v in zip(protected(after['placements'],l),protected(before['placements'],l)))
 assert after['metrics']['selected_score']<=before['metrics']['selected_score']
 assert validate_plan(after['placements'],l,sum(x['loaded_weight'] for x in b),expected_boxes=b)[0]
