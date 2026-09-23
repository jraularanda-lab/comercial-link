from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, flash
from flask_login import login_required
from datetime import datetime, timedelta
from extensions import db
from models import CuentaMercadoLibre, OrdenML, NotificacionML
from services.mercadolibre import exchange_code, get_me, get_order

mercadolibre_bp=Blueprint('mercadolibre',__name__)

@mercadolibre_bp.get('/')
@login_required
def index():
    return render_template('mercadolibre/index.html', cuentas=CuentaMercadoLibre.query.filter_by(activo=True).all(), ordenes=OrdenML.query.order_by(OrdenML.sincronizado.desc()).limit(100).all())

@mercadolibre_bp.get('/oauth')
@login_required
def oauth():
    cid=current_app.config.get('ML_CLIENT_ID',''); uri=current_app.config.get('ML_REDIRECT_URI','')
    if not cid or not uri: flash('Faltan ML_CLIENT_ID y ML_REDIRECT_URI en .env','danger'); return redirect(url_for('mercadolibre.index'))
    import urllib.parse
    q=urllib.parse.urlencode({'response_type':'code','client_id':cid,'redirect_uri':uri})
    return redirect('https://auth.mercadolibre.com.mx/authorization?'+q)

@mercadolibre_bp.get('/callback')
def callback():
    code=request.args.get('code')
    if not code: return 'Falta code',400
    try:
        data=exchange_code(current_app.config['ML_CLIENT_ID'],current_app.config['ML_CLIENT_SECRET'],code,current_app.config['ML_REDIRECT_URI'])
        me=get_me(data['access_token'])
        acc=CuentaMercadoLibre.query.filter_by(ml_user_id=me.get('id')).first()
        if not acc: acc=CuentaMercadoLibre(ml_user_id=me.get('id')); db.session.add(acc)
        acc.nickname=me.get('nickname'); acc.access_token=data['access_token']; acc.refresh_token=data.get('refresh_token'); acc.expires_at=datetime.utcnow()+timedelta(seconds=int(data.get('expires_in',21600))); acc.activo=True
        db.session.commit(); return redirect(url_for('mercadolibre.index'))
    except Exception as e:
        return f'Error conectando Mercado Libre: {e}',400

@mercadolibre_bp.post('/webhook')
def webhook():
    payload=request.get_json(silent=True) or {}
    n=NotificacionML(topic=payload.get('topic',''),resource=payload.get('resource'),ml_user_id=payload.get('user_id'),datos=payload,procesada=False)
    db.session.add(n); db.session.commit()
    return '',200

@mercadolibre_bp.post('/sincronizar/<int:order_id>')
@login_required
def sync_order(order_id):
    acc=CuentaMercadoLibre.query.filter_by(activo=True).first()
    if not acc: flash('Primero conecta una cuenta de Mercado Libre.','danger'); return redirect(url_for('mercadolibre.index'))
    try:
        data=get_order(order_id,acc.access_token)
        o=OrdenML.query.filter_by(order_id=order_id).first()
        if not o: o=OrdenML(order_id=order_id); db.session.add(o)
        o.ml_user_id=acc.ml_user_id; o.estado=data.get('status'); o.total=data.get('total_amount') or 0; o.comprador=((data.get('buyer') or {}).get('nickname')); o.shipping_id=((data.get('shipping') or {}).get('id')); o.datos=data; o.sincronizado=datetime.utcnow(); db.session.commit(); flash('Orden sincronizada.','success')
    except Exception as e: flash(f'Error: {e}','danger')
    return redirect(url_for('mercadolibre.index'))
