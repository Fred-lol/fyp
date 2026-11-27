from time import perf_counter
import pytest
from optimization.cavities import internal_gaps
from optimization.optimizer import generate_plan, _compactness_score
from optimization.backtracking import repack
from optimization.validation import validate_plan


def p(x,y,z=0,l=10,w=10,h=10):
    return dict(x=x,y=y,z=z,placed_length=l,placed_width=w,placed_height=h,loaded_weight=10)


@pytest.mark.parametrize('placements,expected', [
    ([p(0,0),p(20,0)],1000),  # longitudinal gap missed by old y-only metric
    ([p(0,0),p(0,20)],1000),
    ([p(0,0,20)],2000),  # unsupported air below a floating box
    ([p(0,0),p(0,0,20)],1000),  # cavity below upper cargo
    ([p(0,0),p(10,0)],0),
    ([p(0,0),p(10,0,h=20)],0),  # spare height above a shorter box isn't internal
])
def test_exact_3d_gap_measurement(placements,expected):
    result=internal_gaps(placements,include_regions=True)
    assert result['internal_gap_volume_cm3']==expected
    assert sum(r['length']*r['width']*r['height'] for r in result['gap_regions'])==expected


def test_repacking_real_dimensions_closes_previously_unmeasured_cavity():
    lorry=dict(internal_length=290,internal_width=160,internal_height=160,max_weight=1000)
    dimensions=[(82.5,50,41,100),(72,48.5,38.5,75),*( [(51,34.5,34,35)]*3 ),(30,35,35,20)]
    boxes=[dict(order_id=1,box_profile_id=i,box_instance=i,length=l,width=w,height=h,loaded_weight=weight) for i,(l,w,h,weight) in enumerate(dimensions,1)]
    result=generate_plan(lorry,boxes)
    assert result['success']
    assert result['metrics']['ml_inference_used']
    assert result['metrics']['internal_gap_volume_cm3']==0
    assert result['metrics']['occupied_length_cm']<288
    assert result['metrics']['stacked_box_count']==0
    assert validate_plan(result['placements'],lorry,300,expected_boxes=boxes)[0]


def test_backtracking_explores_rotations_and_complete_alternatives():
    lorry=dict(internal_length=60,internal_width=80,internal_height=30,max_weight=100)
    boxes=[dict(order_id=1,box_profile_id=i,box_instance=i,length=l,width=w,height=30,loaded_weight=20) for i,l,w in [(1,60,40),(2,40,60)]]
    candidates,stats=repack(lorry,boxes,_compactness_score,perf_counter()+3)
    assert stats['backtracking_complete']>1
    assert candidates
    assert all(validate_plan(c,lorry,40,expected_boxes=boxes)[0] for c in candidates)
    assert min(internal_gaps(c)['internal_gap_volume_cm3'] for c in candidates)==0


def test_timeout_does_not_return_partial_success():
    candidates,stats=repack({},[{}],_compactness_score,perf_counter()-1)
    assert candidates==[]
