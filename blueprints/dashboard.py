from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from models import Producto, Venta, Inventario

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def index():
    productos = Producto.query.filter_by(activo=True).count()
    ventas = Venta.query.filter(Venta.estatus != "CANCELADA").count()
    inventario_bajo = Inventario.query.filter(Inventario.existencia <= 3).count()
    total_ventas = Venta.query.filter(Venta.estatus != "CANCELADA").with_entities(func.coalesce(func.sum(Venta.total), 0)).scalar()
    return render_template("dashboard.html", productos=productos, ventas=ventas,
                           inventario_bajo=inventario_bajo, total_ventas=total_ventas)
