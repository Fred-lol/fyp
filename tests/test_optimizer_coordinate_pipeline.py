"""Exercise the active save parameters and Three.js input serializer."""
import ast
from contextlib import contextmanager
from pathlib import Path

from optimization.optimizer import generate_plan
from services import optimization_service
from test_optimizer_save_validation import SaveConnection, QueryResult


def test_validated_coordinates_reach_save_and_active_scene_unchanged(monkeypatch):
    truck=dict(lorry_id=1,plate_number='TEST',internal_length=200.,internal_width=100.,
               internal_height=100.,max_weight=1000.,status='Available')
    boxes=[dict(order_id=1,box_profile_id=1,box_instance=i,length=60.,width=40.,height=30.,loaded_weight=20.) for i in (1,2)]
    result=generate_plan(truck,boxes)
    assert result['success']
    result.update(lorry=truck,order_ids=[1],collection_point_id=1)
    rows=[dict(order_id=1,box_profile_id=1,quantity=2,loaded_weight_per_box=20.,
               box_name='Box',capacity_litre=50,length=60.,width=40.,height=30.,customer_name='Test')]

    class Connection(SaveConnection):
        def execute(self,sql,params=()):
            if 'SELECT order_id FROM seafood_orders' in sql:
                return QueryResult(rows=[{'order_id':1}])
            return super().execute(sql,params)

    conn=Connection(truck,rows)
    @contextmanager
    def session():
        yield conn
    monkeypatch.setattr(optimization_service,'db_session',session)
    assert optimization_service.save_optimization(result,created_by=1)[0]
    saved=[params for sql,params in conn.calls if 'INSERT INTO box_placements' in sql]
    for p,params in zip(result['placements'],saved):
        assert tuple(params[5:11])==tuple(p[k] for k in ('x','y','z','placed_length','placed_width','placed_height'))
        assert params[12]==p['sequence_number']
    assert len(saved)==len(boxes)

    source=ast.parse(Path('pages/loading_visualization.py').read_text(encoding='utf-8'))
    assignment=next(n for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scene_data' for t in n.targets))
    plan=dict(truck,placements=result['placements'])
    scene=eval(compile(ast.Expression(assignment.value),'<active scene serializer>','eval'),{'plan':plan})
    assert scene['lorry']['length']==truck['internal_length']
    for p,b in zip(result['placements'],scene['boxes']):
        assert (b['x'],b['y'],b['z'],b['l'],b['w'],b['h'],b['sequence'])==tuple(p[k] for k in ('x','y','z','placed_length','placed_width','placed_height','sequence_number'))
