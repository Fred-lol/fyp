import pytest
from optimization.optimizer import _floor_contact_positions, gap_measurements, generate_plan
from scripts.train_strategy_model import scenario
from optimization.validation import validate_plan

def p(x,y,l=20,w=20):
 return dict(x=x,y=y,z=0,placed_length=l,placed_width=w,placed_height=20,loaded_weight=10)

def test_projected_edges_include_cross_box_corner():
 truck=dict(internal_length=200,internal_width=100)
 assert (40,30,0) in set(_floor_contact_positions([p(20,0),p(0,10)],truck,(10,10,10)))

def test_gap_measurement_excludes_unused_margin():
 truck=dict(internal_length=200,internal_width=100,internal_height=100)
 assert gap_measurements([p(0,0),p(0,30)],truck)['internal_floor_row_gap_cm2']==200
 assert gap_measurements([p(0,0),p(0,20)],truck)['internal_floor_row_gap_cm2']==0

def test_projected_search_closes_regression_gap():
 truck,boxes=scenario(86)
 result=generate_plan(truck,boxes)
 assert result['success']
 assert result['metrics']['ml_inference_used']
 assert result['metrics']['internal_floor_row_gap_cm2']==0
 assert validate_plan(result['placements'],truck,sum(b['loaded_weight'] for b in boxes),expected_boxes=boxes)[0]
