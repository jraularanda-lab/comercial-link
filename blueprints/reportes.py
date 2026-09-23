from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from models import Venta
from datetime import datetime, timedelta
import csv, io
reportes_bp=Blueprint('reportes',__name__)
@reportes_bp.get('/')
@login_required
def index():
    start=request.args.get('start') or datetime.now().strftime('%Y-%m-01'); end=request.args.get('end') or datetime.now().strftime('%Y-%m-%d')
    s=datetime.fromisoformat(start); e=datetime.fromisoformat(end)+timedelta(days=1)
    ventas=Venta.query.filter(Venta.fecha>=s,Venta.fecha<e).order_by(Venta.fecha.desc()).all()
    total=sum((v.total or 0) for v in ventas)
    return render_template('reportes/index.html',ventas=ventas,total=total,start=start,end=end)
@reportes_bp.get('/ventas.csv')
@login_required
def csv_ventas():
    start=request.args.get('start'); end=request.args.get('end'); s=datetime.fromisoformat(start); e=datetime.fromisoformat(end)+timedelta(days=1)
    ventas=Venta.query.filter(Venta.fecha>=s,Venta.fecha<e).order_by(Venta.fecha).all(); out=io.StringIO(); w=csv.writer(out); w.writerow(['Folio','Fecha','Canal','Subtotal','Descuento','Total','Estatus'])
    for v in ventas:w.writerow([v.folio,v.fecha,v.canal,v.subtotal,v.descuento,v.total,v.estatus])
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=ventas.csv'})
