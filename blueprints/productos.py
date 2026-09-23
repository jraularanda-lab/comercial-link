from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Producto, Categoria, Marca
from extensions import db

productos_bp = Blueprint("productos", __name__)

@productos_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    consulta = Producto.query
    if q:
        consulta = consulta.filter(
            db.or_(Producto.nombre.ilike(f"%{q}%"), Producto.sku.ilike(f"%{q}%"))
        )
    productos = consulta.order_by(Producto.id.desc()).all()
    return render_template("productos/index.html", productos=productos, q=q)

@productos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    categorias = Categoria.query.filter_by(activo=True).all()
    marcas = Marca.query.filter_by(activo=True).all()
    if request.method == "POST":
        p = Producto(
            sku=request.form["sku"].strip(),
            codigo_barras=request.form.get("codigo_barras") or None,
            nombre=request.form["nombre"].strip(),
            descripcion=request.form.get("descripcion"),
            id_categoria=request.form.get("id_categoria") or None,
            id_marca=request.form.get("id_marca") or None,
            modelo=request.form.get("modelo"),
            condicion=request.form.get("condicion", "NUEVO"),
            precio_costo=request.form.get("precio_costo") or 0,
            precio_venta=request.form.get("precio_venta") or 0,
            precio_minimo=request.form.get("precio_minimo") or 0
        )
        db.session.add(p)
        try:
            db.session.commit()
            flash("Producto creado.", "success")
            return redirect(url_for("productos.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"No se pudo guardar: {e}", "danger")
    return render_template("productos/form.html", producto=None, categorias=categorias, marcas=marcas)
