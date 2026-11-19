import ast
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
import pytest
from services import payment_service as payment
from services import order_service as orders
from components.charts import capacity_chart, bar_chart

@pytest.mark.parametrize("number", ['0123456789','01112345678','+60123456789','+601112345678','60123456789','012-345 6789'])
def test_valid_mobile(number):
    assert payment._valid_malaysian_mobile(number)

@pytest.mark.parametrize("number", ['', '0111234567','01212345678','+600123456789','0151234567','019123','abc','01234567890'])
def test_invalid_mobile(number):
    assert not payment._valid_malaysian_mobile(number)

@pytest.mark.parametrize("method,details", [
 ('Credit / Debit Card', {'cardholder':'Test Customer','card_number':'4242 4242 4242 4242','expiry':'12/29','cvv':'123'}), ('Online Banking (FPX)', {'bank':'Maybank2u'}),
 ('DuitNow Mobile Number',{'mobile':'01112345678'}), ('E-Wallet',{'wallet':'Boost','mobile':'01112345678'})])
def test_demo_methods(method,details):
    if method == 'DuitNow Mobile Number':
        assert not payment.validate_payment_details(method, details)
    else:
        assert 'demo_confirmed' in payment.validate_payment_details(method, details)
        assert not payment.validate_payment_details(method, dict(details,demo_confirmed=True))

@pytest.mark.parametrize("method,details,field", [
 (None,{},'method'),('unknown',{},'method'),('Online Banking (FPX)',{'bank':'Fake'},'bank'),
 ('E-Wallet',{'wallet':'Fake','mobile':'0123456789'},'wallet'),('E-Wallet',{'wallet':'Boost','mobile':''},'mobile'),
 ('DuitNow Mobile Number',{'mobile':''},'mobile')])
def test_invalid_demo_selection(method, details, field):
    assert field in payment.validate_payment_details(method,dict(details,demo_confirmed=True))

@pytest.mark.parametrize('field,value', [
    ('card_number','4111111111111111'),
    ('card_number','4242424242424241'),
    ('card_number','123'),
    ('cardholder',''),
    ('expiry','01/20'),
    ('expiry','13/29'),
    ('cvv','12'),
])
def test_invalid_test_card_fields(field,value):
    details={'cardholder':'Test Customer','card_number':'4242424242424242','expiry':'12/29','cvv':'123','demo_confirmed':True}
    details[field]=value
    assert field in payment.validate_payment_details('Credit / Debit Card',details)

class Result:
    def __init__(self, value): self.value=value
    def fetchone(self): return self.value

class PaymentConnection:
    def __init__(self): self.existing=None; self.calls=[]
    def execute(self, sql, params=()):
        self.calls.append((sql,params))
        if sql.startswith('SELECT order_id FROM payments'): return Result(self.existing)
        if 'SUM(oi.quantity' in sql: return Result({'amount':275.0})
        if 'INSERT INTO payments' in sql: self.existing={'order_id':42}
        return Result(None)


def setup_payment(monkeypatch, connection, place):
    @contextmanager
    def session(): yield connection
    monkeypatch.setattr(payment,'db_session',session)
    monkeypatch.setattr(payment,'initialize_schema',lambda:None)
    monkeypatch.setattr(payment,'place_order',place)


def test_duplicate_reference_and_authoritative_price(monkeypatch):
    conn=PaymentConnection(); calls=[]
    def place(*args,**kwargs):
        calls.append(kwargs); assert kwargs['_connection'] is conn
        return True,'ok',42
    setup_payment(monkeypatch,conn,place)
    args=(1,[(7,10)],'DuitNow Mobile Number',{'mobile':'0123456789'},3)
    token=str(uuid4())
    assert payment.complete_demo_payment(*args,submission_key=token)[2]==42
    result=payment.complete_demo_payment(*args,submission_key=token)
    assert result[2]==42 and 'already submitted' in result[1]
    assert len(calls)==1
    inserts=[params for sql,params in conn.calls if 'INSERT INTO payments' in sql]
    assert len(inserts)==1 and inserts[0][2]==275.0 and inserts[0][4]=='Simulated'
    assert inserts[0][5].startswith('AQDEMO-')


def test_failed_stock_keeps_payment_unwritten(monkeypatch):
    conn=PaymentConnection()
    setup_payment(monkeypatch,conn,lambda *a,**k:(False,'Only 5 kg available.',None))
    result=payment.complete_demo_payment(1,[(7,10)],'DuitNow Mobile Number',{'mobile':'0123456789'},3,submission_key=str(uuid4()))
    assert result==(False,'Only 5 kg available.',None)
    assert not any('INSERT' in sql for sql,_ in conn.calls)


def test_missing_point_and_expired_token():
    assert not payment.complete_demo_payment(1,[], 'DuitNow Mobile Number', {'mobile':'0123456789'})[0]
    assert not payment.complete_demo_payment(1,[], 'DuitNow Mobile Number', {'mobile':'0123456789'},3)[0]

@pytest.mark.parametrize('quantity',[0,-1,9,float('nan'),float('inf')])
def test_server_minimum_and_finite(monkeypatch,quantity):
    monkeypatch.setattr(orders,'initialize_schema',lambda:None)
    assert not orders.place_order(1,[(1,quantity)],1)[0]


def test_capacity_above_100_visible():
    figure=capacity_chart([{'plan_id':1,'space_utilization':115,'weight_utilization':44}])
    assert figure.layout.yaxis.range[1] > 115
    assert list(figure.data[0].y)==[115]
    assert list(figure.data[1].y)==[44]
    assert figure.layout.barmode=='group'


def test_count_axes():
    fig=bar_chart(['LKIM Fisheries Complex Kuala Perlis'],[3],'Plans',horizontal=True,counts=True)
    assert fig.layout.xaxis.dtick==1 and fig.layout.xaxis.tickformat==',d'
    assert fig.data[0].orientation=='h'


def test_active_renderers_replaced():
    catalogue=Path('pages/order_seafood.py').read_text(encoding='utf-8')
    reports=Path('pages/reports_analytics.py').read_text(encoding='utf-8')
    checkout=Path('pages/payment.py').read_text(encoding='utf-8')
    assert 'product_card(' in catalogue and 'seafood-card-' not in catalogue
    assert 'alt.Chart' not in reports and 'st.altair_chart' not in reports
    assert 'payment_card_number' in checkout and 'payment_expiry' in checkout
    assert 'payment_method_select_' in checkout and 'st.radio(' not in checkout
    for page in ['homepage.py','pages/about_aquaload.py','pages/who_we_serve.py']:
        source=Path(page).read_text(encoding='utf-8')
        assert 'render_homepage_header(' in source and 'render_homepage_footer(' in source
    shell=Path('components/public_shell.py').read_text(encoding='utf-8')
    assert 'def render_sample_plan' in shell
    assert 'aq-public-main' in shell and 'prefers-color-scheme' not in shell


def test_catalogue_details_remain_in_authenticated_page_session():
    catalogue=Path('pages/order_seafood.py').read_text(encoding='utf-8')
    open_handler=catalogue.split('def _open_product_details',1)[1].split('def _back_to_catalogue',1)[0]
    assert 'st.switch_page(' not in open_handler
    assert 'require_role(ROLES["CUSTOMER"])' in catalogue
    assert 'selected = get_product(int(selected_id))' in catalogue
    assert 'favorite_product_ids' in catalogue
