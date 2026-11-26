from copy import deepcopy
import pytest
from optimization.optimizer import generate_plan, _compactness_score
from optimization.constraints import loading_sequence_key, stack_loads_valid
from optimization.validation import validate_plan

@pytest.mark.parametrize("dimensions,payload", [((200,120,120),1000),((430,210,210),3000)])
def test_actual_profiles_and_mixed_boxes(dimensions,payload):
    lorry=dict(zip(("internal_length","internal_width","internal_height"),dimensions),max_weight=payload)
    boxes=[dict(order_id=1,box_profile_id=i,box_instance=i,capacity_litre=litres,
                length=l,width=w,height=h,loaded_weight=weight)
           for i,(litres,l,w,h,weight) in enumerate([(20,30,35,35,20),(35,51,34.5,34,35),
                (50,67.5,40.5,36,50),(75,72,48.5,38.5,60),(100,82.5,50,41,70)],1)]
    result=generate_plan(lorry,boxes)
    assert result["success"],result["message"]
    p=result["placements"]
    assert validate_plan(p,lorry,235,expected_boxes=boxes)[0]
    assert p==sorted(p,key=loading_sequence_key)
    assert result["metrics"]["lorry_volume"]==dimensions[0]*dimensions[1]*dimensions[2]
    assert result["metrics"]["weight_utilization"]==pytest.approx(235/payload*100)
    assert result["metrics"]["optimization_seconds"]<10

def test_cumulative_stack_load_rejects_three_equal_boxes():
    boxes=[dict(x=0,y=0,z=z,placed_length=50,placed_width=40,placed_height=30,loaded_weight=20) for z in (0,30,60)]
    assert stack_loads_valid(boxes[:2])
    assert not stack_loads_valid(boxes)

def test_compactness_measures_occupied_length_after_mirroring():
    lorry=dict(internal_length=500,internal_width=100,internal_height=100,max_weight=1000)
    p=[dict(x=450,y=0,z=0,placed_length=50,placed_width=40,placed_height=30,loaded_weight=20)]
    assert _compactness_score(p,lorry)[2]==50


def test_floor_layout_preferred_when_stacking_is_unnecessary():
    lorry=dict(internal_length=500,internal_width=100,internal_height=100,max_weight=1000)
    def box(x,z):
        return dict(x=x,y=0,z=z,placed_length=50,placed_width=40,placed_height=30,loaded_weight=20)
    stacked=[box(450,0),box(450,30)]
    floor=[box(450,0),box(400,0)]
    assert _compactness_score(floor,lorry) < _compactness_score(stacked,lorry)


def test_default_plan_fills_floor_rows_without_unnecessary_stacking():
    lorry=dict(internal_length=200,internal_width=100,internal_height=100,max_weight=1000)
    boxes=[dict(order_id=1,box_profile_id=1,box_instance=i,length=50,width=50,height=30,loaded_weight=20)
           for i in range(1,7)]
    result=generate_plan(lorry,boxes)
    assert result['success'],result['message']
    placements=result['placements']
    assert all(p['z']==0 for p in placements)
    assert sorted((p['x'],p['y']) for p in placements)==[(50,0),(50,50),(100,0),(100,50),(150,0),(150,50)]
    assert validate_plan(placements,lorry,120,expected_boxes=boxes)[0]


def test_stack_when_floor_is_full():
    lorry=dict(internal_length=100,internal_width=100,internal_height=60,max_weight=1000)
    boxes=[dict(order_id=1,box_profile_id=1,box_instance=i,length=50,width=50,height=30,loaded_weight=20)
           for i in range(1,7)]
    result=generate_plan(lorry,boxes)
    assert result['success'],result['message']
    assert sum(p['z']>0 for p in result['placements'])==2
    assert validate_plan(result['placements'],lorry,120,expected_boxes=boxes)[0]
