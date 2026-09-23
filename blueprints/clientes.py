from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models import Cliente
clientes_bp=Blueprint('clientes',__name__)
@clientes_bp.route('/',methods=['GET','POST'])
@login_required
def index():
    if request.method=='POST':
        db.session.add(Cliente(nombre=request.form['nombre'].strip(),telefono=request.form.get('telefono'),email=request.form.get('email'),notas=request.form.get('notas'))); db.session.commit(); flash('Cliente guardado.','success'); return redirect(url_for('clientes.index'))
    q=request.args.get('q','').strip(); query=Cliente.query.order_by(Cliente.nombre)
    if q: query=query.filter(Cliente.nombre.ilike(f'%{q}%'))
    return render_template('clientes/index.html',clientes=query.all())
