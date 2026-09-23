from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Producto, Ubicacion
from sqlalchemy import text

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/', methods=['GET'])
@login_required
def index():
    """Muestra la lista de inventario uniendo productos y existencias directamente."""
    try:
        ubicaciones = Ubicacion.query.all() if hasattr(Ubicacion, 'query') else []
        productos_dropdown = Producto.query.filter_by(activo=True).all()
        
        # Consulta SQL directa para asegurar que leemos las existencias reales
        stock_results = db.session.execute(text("""
            SELECT p.id, p.sku, p.nombre, COALESCE(i.existencia, 0) AS stock_actual
            FROM productos p
            LEFT JOIN inventarios i ON p.id = i.id_producto
        """)).fetchall()

    except Exception as e:
        productos_dropdown = []
        ubicaciones = []
        stock_results = []
        flash(f"Error al cargar inventario: {str(e)}", "danger")

    return render_template('inventario/index.html', productos=productos_dropdown, stock_results=stock_results, ubicaciones=ubicaciones)


@inventario_bp.route('/guardar', methods=['POST'])
@login_required
def guardar_inicial():
    """Agrega o actualiza el inventario inicial."""
    try:
        producto_id = int(request.form.get('id_producto') or request.form.get('producto_id'))
        cantidad = int(request.form.get('cantidad', 0))
        ubicacion_id = int(request.form.get('id_ubicacion') or 1)

        query = text("""
            INSERT INTO inventarios (id_producto, id_ubicacion, existencia, apartado) 
            VALUES (:prod_id, :ubic_id, :cant, 0)
            ON DUPLICATE KEY UPDATE existencia = :cant
        """)
        db.session.execute(query, {'prod_id': producto_id, 'ubic_id': ubicacion_id, 'cant': cantidad})
        db.session.commit()
        
        flash('✅ Inventario actualizado correctamente.', 'success')

    except Exception as e:
        db.session.rollback()
        print("❌ ERROR EN INVENTARIO:", str(e))
        flash(f'Error al guardar inventario: {str(e)}', 'danger')

    return redirect(url_for('inventario.index'))