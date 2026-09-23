import requests
from datetime import datetime, timedelta
API='https://api.mercadolibre.com'

def exchange_code(client_id, client_secret, code, redirect_uri):
    r=requests.post(f'{API}/oauth/token',data={'grant_type':'authorization_code','client_id':client_id,'client_secret':client_secret,'code':code,'redirect_uri':redirect_uri},timeout=30)
    r.raise_for_status(); return r.json()

def refresh(client_id, client_secret, refresh_token):
    r=requests.post(f'{API}/oauth/token',data={'grant_type':'refresh_token','client_id':client_id,'client_secret':client_secret,'refresh_token':refresh_token},timeout=30)
    r.raise_for_status(); return r.json()

def get_order(order_id, access_token):
    r=requests.get(f'{API}/orders/{order_id}',headers={'Authorization':f'Bearer {access_token}'},timeout=30)
    r.raise_for_status(); return r.json()

def get_me(access_token):
    r=requests.get(f'{API}/users/me',headers={'Authorization':f'Bearer {access_token}'},timeout=30)
    r.raise_for_status(); return r.json()
