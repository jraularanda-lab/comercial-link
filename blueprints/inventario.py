from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Producto, Ubicacion
from sqlalchemy import text
from datetime import datetime # Importamos datetime para la fecha

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/', methods=['GET'])
@login_required
def index():
    """Muestra la lista de inventario uniendo productos y existencias."""
    try:
        ubicaciones = Ubicacion.query.all() if hasattr(Ubicacion, 'query') else []
        
        # 1. Traemos todos los productos activos
        productos_db = Producto.query.filter_by(activo=True).order_by(Producto.sku).all()
        
        # 2. Traemos todo el inventario
        inventarios_db = db.session.execute(text("SELECT id_producto, existencia, fecha_actualizacion FROM inventarios")).fetchall()
        
        # 3. Creamos un diccionario para agrupar el stock por ID de producto
        stock_por_producto = {}
        fecha_por_producto = {}
        
        for inv in inventarios_db:
            p_id = inv[0]
            cant = inv[1] or 0
            fecha = inv[2]
            
            # Sumamos las cantidades si el producto está en varias ubicaciones
            stock_por_producto[p_id] = stock_por_producto.get(p_id, 0) + cant
            
            # Guardamos la fecha más reciente
            if fecha:
                if p_id not in fecha_por_producto or fecha > fecha_por_producto[p_id]:
                    fecha_por_producto[p_id] = fecha

        # 4. Armamos la lista final mezclando Producto con su Stock
        stock_results = []
        for p in productos_db:
            stock_actual = stock_por_producto.get(p.id, 0)
            ultima_fecha = fecha_por_producto.get(p.id, None)
            
            stock_results.append({
                'id': p.id,
                'sku': p.sku,
                'nombre': p.nombre,
                'stock_actual': stock_actual,
                'ultima_actualizacion': ultima_fecha
            })

    except Exception as e:
        productos_dropdown = []
        ubicaciones = []
        stock_results = []
        flash(f"Error al cargar inventario: {str(e)}", "danger")
        print("Error Index:", e)

    # Pasamos la misma lista a la tabla y al desplegable
    return render_template('inventario/index.html', productos=stock_results, stock_results=stock_results, ubicaciones=ubicaciones)

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

@inventario_bp.route('/guardar', methods=['POST'])
@login_required
def guardar_inicial():
    """Agrega inventario y guarda el historial del movimiento."""
    try:
        producto_id = int(request.form.get('id_producto') or request.form.get('producto_id'))
        cantidad = int(request.form.get('cantidad', 0))
        ubicacion_id = int(request.form.get('id_ubicacion') or 1)
        ahora = datetime.now()

        if cantidad <= 0:
            flash('⚠️ La cantidad a ingresar debe ser mayor a 0.', 'warning')
            return redirect(url_for('inventario.index'))

        # 1. Obtener el stock actual ANTES de sumar (para el historial)
        stock_actual_query = db.session.execute(text("""
            SELECT COALESCE(existencia, 0) FROM inventarios 
            WHERE id_producto = :prod AND id_ubicacion = :ubic
        """), {'prod': producto_id, 'ubic': ubicacion_id}).scalar()
        
        stock_anterior = stock_actual_query if stock_actual_query else 0
        stock_nuevo = stock_anterior + cantidad

        # 2. Insertar o Actualizar el inventario (Tu código actual)
        query_inventario = text("""
            INSERT INTO inventarios (id_producto, id_ubicacion, existencia, apartado, fecha_actualizacion) 
            VALUES (:prod_id, :ubic_id, :cant, 0, :fecha)
            ON DUPLICATE KEY UPDATE 
                existencia = existencia + :cant,
                fecha_actualizacion = :fecha
        """)
        db.session.execute(query_inventario, {
            'prod_id': producto_id, 'ubic_id': ubicacion_id, 'cant': cantidad, 'fecha': ahora
        })

        # 3. Guardar el historial del movimiento
        query_historial = text("""
            INSERT INTO historial_inventario 
            (id_producto, id_ubicacion, tipo_movimiento, cantidad, stock_anterior, stock_nuevo, fecha_movimiento) 
            VALUES (:prod_id, :ubic_id, 'INGRESO', :cant, :ant, :nuevo, :fecha)
        """)
        db.session.execute(query_historial, {
            'prod_id': producto_id, 
            'ubic_id': ubicacion_id, 
            'cant': cantidad, 
            'ant': stock_anterior, 
            'nuevo': stock_nuevo, 
            'fecha': ahora
        })

        db.session.commit()
        flash(f'✅ Se ingresaron {cantidad} unidades correctamente y se guardó en el historial.', 'success')

    except Exception as e:
        db.session.rollback()
        print("❌ ERROR EN INVENTARIO:", str(e))
        flash(f'Error al guardar inventario: {str(e)}', "danger")

    return redirect(url_for('inventario.index'))


@inventario_bp.route('/historial')
@login_required
def historial():
    """Muestra la tabla con todos los movimientos."""
    try:
        # Consulta que une el historial con el nombre del producto y el almacén
        historial_db = db.session.execute(text("""
            SELECT h.*, p.sku, p.nombre AS producto_nombre, u.nombre AS ubicacion_nombre
            FROM historial_inventario h
            JOIN productos p ON h.id_producto = p.id
            JOIN ubicaciones u ON h.id_ubicacion = u.id
            ORDER BY h.fecha_movimiento DESC
        """)).fetchall()
        
        # Convertimos a lista de diccionarios para que Jinja lo lea fácil
        historial_resultados = [dict(row._mapping) for row in historial_db]

    except Exception as e:
        historial_resultados = []
        flash(f"Error al cargar historial: {str(e)}", "danger")

    return render_template('inventario/historial.html', historial=historial_resultados)