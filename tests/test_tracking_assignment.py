import sqlite3
from contextlib import contextmanager
import pytest
from services import tracking_assignment_service as service


def row(**changes):
    result = dict(plan_id=7, order_id=10, plan_point_id=2, collection_point_id=2,
                  point_name='LKIM Fisheries Complex Endau', city='Endau', state='Johor',
                  latitude=2.65, longitude=103.62)
    result.update(changes)
    return result


def test_assignment_uses_saved_point():
    result = service.resolve_assignment([row(), row(order_id=11)])
    assert result['valid']
    assert len(result['stops']) == 1
    assert result['stops'][0]['city'] == 'Endau'
    assert result['order_ids'] == [10, 11]


@pytest.mark.parametrize('rows', [[], [row(plan_point_id=3)], [row(latitude=None)],
    [row(longitude=float('nan'))], [row(), row(collection_point_id=3, plan_point_id=3)]])
def test_invalid_assignments_fail_closed(rows):
    assert not service.resolve_assignment(rows)['valid']


@pytest.mark.parametrize('lorry_status,order_status,archived,expected', [
    ('In Transit','Loaded',None,True), ('Available','Loaded',None,False),
    ('In Transit','Completed',None,False), ('In Transit','Cancelled',None,False),
    ('In Transit','Loaded','2026-01-01',False)])
def test_query_excludes_inactive_trips(monkeypatch, lorry_status, order_status, archived, expected):
    db = sqlite3.connect(':memory:')
    db.row_factory = lambda cursor, values: dict(zip([c[0] for c in cursor.description], values))
    db.executescript('''
    CREATE TABLE loading_plans(plan_id,lorry_id,collection_point_id,status,created_at);
    CREATE TABLE lorry_profiles(lorry_id,status);
    CREATE TABLE loading_plan_orders(plan_id,order_id);
    CREATE TABLE seafood_orders(order_id,collection_point_id,status,archived_at,collection_assignment);
    CREATE TABLE collection_points(collection_point_id,point_name,city,state,latitude,longitude);
    INSERT INTO loading_plans VALUES(7,1,2,'Saved','2026-01-01');
    INSERT INTO loading_plan_orders VALUES(7,10);
    INSERT INTO collection_points VALUES(2,'LKIM Endau','Endau','Johor',2.65,103.62);
    ''')
    db.execute('INSERT INTO lorry_profiles VALUES(?,?)',(1,lorry_status))
    db.execute('INSERT INTO seafood_orders VALUES(?,?,?,?,?)',(10,2,order_status,archived,'Customer Selection'))
    @contextmanager
    def session():
        yield db
    monkeypatch.setattr(service,'db_session',session)
    assert service.get_lorry_assignment(1)['valid'] is expected
    assert not service.get_lorry_assignment(999)['valid']
    db.close()
