from streamlit.testing.v1 import AppTest
from pathlib import Path
import pytest

@pytest.mark.parametrize('method', ['Credit / Debit Card','Online Banking (FPX)','DuitNow QR','E-Wallet'])
def test_checkout_ui_validation_and_single_summary(monkeypatch, method):
    import bootstrap
    import components.navigation as nav
    import services.payment_service as payment
    import services.collection_point_service as points
    import services.auth_service as auth
    import streamlit as st
    calls={'summary':0,'submit':0,'navigation':[]}
    monkeypatch.setattr(bootstrap,'bootstrap_app',lambda:None)
    monkeypatch.setattr(nav,'customer_sidebar',lambda:None)
    monkeypatch.setattr(auth,'get_user',lambda uid:{'state':'Perlis'})
    monkeypatch.setattr(points,'list_collection_points',lambda status:[{'collection_point_id':1,'point_name':'LKIM Kuala Perlis','state':'Perlis'}])
    def summary(items):
        calls['summary']+=1
        return {'items':[{'product_name':'Fish','quantity':10,'unit_price':20,'line_total':200}],'total_weight_kg':10,'total_amount':200}
    monkeypatch.setattr(payment,'checkout_summary',summary)
    def submit(*args,**kwargs):
        assert not payment.validate_payment_details(args[2],args[3])
        assert args[4]==1 and kwargs['submission_key']
        calls['submit']+=1
        return True,'Demo order submitted',42
    monkeypatch.setattr(payment,'complete_demo_payment',submit)
    monkeypatch.setattr(st,'switch_page',lambda page:calls['navigation'].append(page))
    app=AppTest.from_file(Path('pages/payment.py').resolve())
    app.session_state['user_id']=1
    app.session_state['checkout_cart']=[(1,10)]
    app.session_state['cart']={1:10}
    app.run()
    assert not app.exception
    def press():
        next(button for button in app.button if button.label=='Place Demo Order').click().run()
    press()
    assert calls['submit']==0
    assert 'collection_point' in app.session_state['payment_errors']
    app.radio(key='payment_method').set_value(method).run()
    app.selectbox(key='payment_point_id').set_value(1).run()
    press()
    assert 'demo_confirmed' in app.session_state['payment_errors']
    if method=='Online Banking (FPX)':
        assert 'bank' in app.session_state['payment_errors']
        app.selectbox(key='payment_bank').set_value('Maybank2u')
    elif method=='E-Wallet':
        app.selectbox(key='payment_wallet').set_value('Boost')
        app.text_input(key='payment_wallet_mobile').set_value('011123')
        press()
        assert 'mobile' in app.session_state['payment_errors']
        app.text_input(key='payment_wallet_mobile').set_value('+601112345678')
    app.checkbox(key='demo_confirmed_'+method).check()
    press()
    assert not app.exception
    assert calls['submit']==1 and calls['summary']==1
    assert calls['navigation']==['pages/payment_success.py']
    assert app.session_state['cart']=={}
