from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Producto, Ubicacion
from sqlalchemy import text
from datetime import datetime # Importamos datetime para la fecha

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/', methods=['GET'])
@login_required
def index():
    """Muestra la lista de inventario uniendo productos y existencias directamente."""
    try:
        ubicaciones = Ubicacion.query.all() if hasattr(Ubicacion, 'query') else []
        
        # Consulta ÚNICA para la tabla y el desplegable
        # Usamos GROUP BY p.id para agrupar si un producto está en varias ubicaciones
        query = text("""
            SELECT 
                p.id,
                p.sku, 
                p.nombre, 
                SUM(COALESCE(i.existencia, 0)) AS stock_actual,
                MAX(i.fecha_actualizacion) AS ultima_actualizacion
            FROM productos p
            LEFT JOIN inventarios i ON p.id = i.id_producto
            WHERE p.activo = 1
            GROUP BY p.id, p.sku, p.nombre
            ORDER BY p.nombre ASC
        """)
        
        resultados = db.session.execute(query).fetchall()
        
        # Pasamos los mismos resultados al desplegable y a la tabla
        productos_dropdown = resultados
        stock_results = resultados

    except Exception as e:
        productos_dropdown = []
        ubicaciones = []
        stock_results = []
        flash(f"Error al cargar inventario: {str(e)}", "danger")

    return render_template('inventario/index.html', productos=productos_dropdown, stock_results=stock_results, ubicaciones=ubicaciones)
@inventario_bp.route('/guardar', methods=['POST'])
@login_required
def guardar_inicial():
    """Agrega o actualiza el inventario sumando la nueva cantidad."""
    try:
        producto_id = int(request.form.get('id_producto') or request.form.get('producto_id'))
        cantidad = int(request.form.get('cantidad', 0))
        ubicacion_id = int(request.form.get('id_ubicacion') or 1)
        
        # Obtenemos la fecha y hora actual
        ahora = datetime.now()

        if cantidad <= 0:
            flash('⚠️ La cantidad a ingresar debe ser mayor a 0.', 'warning')
            return redirect(url_for('inventario.index'))

        # Agregamos fecha_actualizacion al INSERT y al UPDATE
        query = text("""
            INSERT INTO inventarios (id_producto, id_ubicacion, existencia, apartado, fecha_actualizacion) 
            VALUES (:prod_id, :ubic_id, :cant, 0, :fecha)
            ON DUPLICATE KEY UPDATE 
                existencia = existencia + :cant,
                fecha_actualizacion = :fecha
        """)
        
        db.session.execute(query, {
            'prod_id': producto_id, 
            'ubic_id': ubicacion_id, 
            'cant': cantidad,
            'fecha': ahora
        })
        db.session.commit()
        
        flash(f'✅ Se ingresaron {cantidad} unidades correctamente al inventario.', 'success')

    except Exception as e:
        db.session.rollback()
        print("❌ ERROR EN INVENTARIO:", str(e))
        flash(f'Error al guardar inventario: {str(e)}', 'danger')

    return redirect(url_for('inventario.index'))