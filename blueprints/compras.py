from flask import Blueprint, render_template
from flask_login import login_required
from models import Compra

compras_bp = Blueprint("compras", __name__)

@compras_bp.route("/")
@login_required
def index():
    compras = Compra.query.order_by(Compra.fecha.desc()).limit(100).all()
    return render_template("compras/index.html", compras=compras)
