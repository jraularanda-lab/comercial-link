from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Producto, Ubicacion
from sqlalchemy import text
from datetime import datetime

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@inventario_bp.route('/', methods=['GET'])
@login_required
def index():
    """Muestra la lista de inventario uniendo productos y existencias."""
    try:
        ubicaciones = Ubicacion.query.all() if hasattr(Ubicacion, 'query') else []
        
        # Traemos todos los productos activos ordenados por SKU
        productos_db = Producto.query.filter_by(activo=True).order_by(Producto.sku).all()
        
        # Traemos todo el inventario
        inventarios_db = db.session.execute(text("SELECT id_producto, existencia, fecha_actualizacion FROM inventarios")).fetchall()
        
        # Agrupamos el stock y fechas por ID de producto
        stock_por_producto = {}
        fecha_por_producto = {}
        
        for inv in inventarios_db:
            p_id = inv[0]
            cant = inv[1] or 0
            fecha = inv[2]
            
            stock_por_producto[p_id] = stock_por_producto.get(p_id, 0) + cant
            
            if fecha:
                if p_id not in fecha_por_producto or fecha > fecha_por_producto[p_id]:
                    fecha_por_producto[p_id] = fecha

        # Armamos la lista final
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

    return render_template('inventario/index.html', productos=stock_results, stock_results=stock_results, ubicaciones=ubicaciones)


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

        # 1. Obtener el stock actual ANTES de sumar
        stock_actual_query = db.session.execute(text("""
            SELECT COALESCE(existencia, 0) FROM inventarios 
            WHERE id_producto = :prod AND id_ubicacion = :ubic
        """), {'prod': producto_id, 'ubic': ubicacion_id}).scalar()
        
        stock_anterior = int(stock_actual_query) if stock_actual_query else 0
        stock_nuevo = stock_anterior + cantidad

        # 2. Insertar o Actualizar el inventario principal
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
        
        # Hacemos un solo commit para ambas operaciones (Inventario e Historial)
        db.session.commit()
        
        flash(f'✅ Se ingresaron {cantidad} unidades correctamente y se guardó en el historial.', 'success')

    except Exception as e:
        db.session.rollback()
        # Este print te dirá exactamente qué está fallando en los logs de Render
        print("❌ ERROR CRÍTICO EN INVENTARIO:", str(e)) 
        flash(f'Error al guardar inventario: {str(e)}', 'danger')

    return redirect(url_for('inventario.index'))


@inventario_bp.route('/historial')
@login_required
def historial():
    """Muestra la tabla con todos los movimientos."""
    try:
        # Forzamos a la sesión a cerrar cualquier transacción pendiente
        db.session.commit() 
        
        # Hacemos la consulta
        historial_db = db.session.execute(text("""
            SELECT h.id, h.cantidad, h.stock_anterior, h.stock_nuevo, h.fecha_movimiento, h.tipo_movimiento,
                   p.sku, p.nombre AS producto_nombre, 
                   u.nombre AS ubicacion_nombre
            FROM historial_inventario h
            LEFT JOIN productos p ON h.id_producto = p.id
            LEFT JOIN ubicacion u ON h.id_ubicacion = u.id
            ORDER BY h.fecha_movimiento DESC
        """)).fetchall()
        
        # Convertimos a lista de diccionarios para que el HTML lo lea bien
        historial_resultados = []
        for row in historial_db:
            historial_resultados.append(dict(row._mapping))

    except Exception as e:
        historial_resultados = []
        # Imprimimos el error en los logs para saber si algo falla
        print("❌ ERROR AL LEER HISTORIAL:", str(e))
        flash(f"Error al cargar historial: {str(e)}", "danger")

    return render_template('inventario/historial.html', historial=historial_resultados)