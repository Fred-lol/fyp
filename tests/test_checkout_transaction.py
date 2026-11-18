"""Opt-in real PostgreSQL checks using ONLY session-local temporary tables.

No production rows or production sequences are changed; the connection always
rolls back. Search path is pg_temp only, so a missing fixture cannot hit public.
"""
import os
from contextlib import contextmanager
from uuid import uuid4
import pytest
from database.db import get_connection
from services import payment_service as payments
from services import order_service as orders

pytestmark=pytest.mark.skipif(os.getenv('AQUALOAD_TEMP_DB_TEST')!='1', reason='opt-in temporary-table PostgreSQL checks')

@pytest.fixture
def checkout_db(monkeypatch):
    conn=get_connection()
    raw=conn._connection
    definitions={
      'users':'user_id bigint primary key, role text, status text, city text, state text',
      'collection_points':'collection_point_id bigint primary key, point_name text, city text, state text, status text',
      'seafood_products':'product_id bigint primary key, product_name text, unit text, unit_price float, stock_quantity float, availability_status text, updated_at timestamptz',
      'seafood_orders':'order_id bigint generated always as identity primary key, customer_id bigint, status text, collection_point_id bigint, collection_point text, collection_assignment text',
      'order_items':'order_item_id bigint generated always as identity primary key, order_id bigint, product_id bigint, quantity float, unit text',
      'seafood_stock_movements':'movement_id bigint generated always as identity primary key, product_id bigint,quantity_change float,movement_type text,reference_order_id bigint,updated_by bigint,note text',
      'order_status_history':'history_id bigint generated always as identity primary key,order_id bigint,status text,updated_by bigint,note text',
      'payments':'payment_id bigint generated always as identity primary key,order_id bigint unique,customer_id bigint,amount float,payment_method text,payment_status text,transaction_reference text unique',
    }
    try:
        raw.execute('SET LOCAL search_path TO pg_temp')
        for table,definition in definitions.items():
            raw.execute(f'CREATE TEMP TABLE {table} ({definition}) ON COMMIT DROP')
        raw.execute("INSERT INTO users VALUES(1,'Customer','Active','Kangar','Perlis')")
        raw.execute("INSERT INTO collection_points VALUES(1,'LKIM Kuala Perlis','Kuala Perlis','Perlis','Available')")
        raw.execute("INSERT INTO seafood_products VALUES(1,'Test Fish','kg',20,100,'Available',now())")
        @contextmanager
        def session():
            with raw.transaction():
                yield conn
        monkeypatch.setattr(payments,'db_session',session)
        monkeypatch.setattr(payments,'initialize_schema',lambda:None)
        monkeypatch.setattr(orders,'initialize_schema',lambda:None)
        yield conn
    finally:
        raw.rollback()
        raw.close()

@pytest.mark.parametrize('method,details',[
 ('Credit / Debit Card',{}),('Online Banking (FPX)',{'bank':'Maybank2u'}),
 ('DuitNow QR',{}),('E-Wallet',{'wallet':'Boost','mobile':'01112345678'})])
def test_real_demo_order_and_retry(checkout_db,method,details):
    token=str(uuid4()); details=dict(details,demo_confirmed=True)
    args=(1,[(1,10)],method,details,1)
    first=payments.complete_demo_payment(*args,submission_key=token)
    second=payments.complete_demo_payment(*args,submission_key=token)
    assert first[0] and first[2]==second[2]
    assert checkout_db.execute('SELECT count(*) AS n FROM seafood_orders').fetchone()['n']==1
    assert checkout_db.execute('SELECT stock_quantity FROM seafood_products').fetchone()['stock_quantity']==90
    row=checkout_db.execute('SELECT * FROM payments').fetchone()
    assert row['amount']==200 and row['payment_status']=='Simulated'
    assert checkout_db.execute('SELECT collection_assignment FROM seafood_orders').fetchone()['collection_assignment']=='Local Pickup'

@pytest.mark.parametrize('cart,point',[([],1), ([(1,101)],1), ([(1,9)],1), ([(1,10)],999), ([(999,10)],1)])
def test_rejected_order_has_no_writes(checkout_db,cart,point):
    result=payments.complete_demo_payment(1,cart,'DuitNow QR',{'demo_confirmed':True},point,submission_key=str(uuid4()))
    assert not result[0]
    assert checkout_db.execute('SELECT count(*) AS n FROM seafood_orders').fetchone()['n']==0
    assert checkout_db.execute('SELECT stock_quantity FROM seafood_products').fetchone()['stock_quantity']==100


def test_payment_failure_rolls_back_order_and_stock(checkout_db):
    checkout_db._connection.execute("ALTER TABLE payments ADD CONSTRAINT forced_failure CHECK(amount<0)")
    with pytest.raises(Exception):
        payments.complete_demo_payment(1,[(1,10)],'DuitNow QR',{'demo_confirmed':True},1,submission_key=str(uuid4()))
    assert checkout_db.execute('SELECT count(*) AS n FROM seafood_orders').fetchone()['n']==0
    assert checkout_db.execute('SELECT stock_quantity FROM seafood_products').fetchone()['stock_quantity']==100
