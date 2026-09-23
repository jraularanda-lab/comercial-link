from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from extensions import db
from models import Venta, VentaDetalle, Producto, Inventario, Cliente

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route('/')
def index():
    # Capturar parámetros de la barra de filtros
    filtro_dia = request.args.get('dia', '')
    filtro_mes = request.args.get('mes', '')
    filtro_canal = request.args.get('canal', '')

    query = Venta.query

    # Filtrar por día específico (formato YYYY-MM-DD)
    if filtro_dia:
        try:
            fecha_inicio = datetime.strptime(filtro_dia, '%Y-%m-%d')
            fecha_fin = datetime.strptime(filtro_dia + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(Venta.fecha >= fecha_inicio, Venta.fecha <= fecha_fin)
        except ValueError:
            pass

    # Filtrar por mes (formato YYYY-MM) si no hay un día específico seleccionado
    if filtro_mes and not filtro_dia:
        try:
            partes = filtro_mes.split('-')
            if len(partes) == 2:
                anio = int(partes[0])
                mes = int(partes[1])
                if 1 <= mes <= 12:
                    query = query.filter(
                        db.extract('year', Venta.fecha) == anio,
                        db.extract('month', Venta.fecha) == mes
                    )
        except (ValueError, TypeError):
            pass

    # Filtrar por canal / tipo de venta de forma flexible
    if filtro_canal:
        query = query.filter(Venta.canal.ilike(f"%{filtro_canal}%"))

    # Ordenar de la más nueva a la más antigua
    ventas = query.order_by(Venta.id.desc()).all()
    
    return render_template('ventas/index.html', ventas=ventas, filtro_dia=filtro_dia, filtro_mes=filtro_mes, filtro_canal=filtro_canal)

@ventas_bp.route('/nueva', methods=['GET', 'POST'])
def nueva():
    if request.method == 'POST':
        canal = request.form.get('canal')
        id_cliente = request.form.get('id_cliente')
        fecha_str = request.form.get('fecha')
        
        fecha_venta = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.utcnow().date()
        
        productos_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        precios = request.form.getlist('precio[]')
        
        if not productos_ids:
            flash('Debe agregar al menos un producto a la venta.', 'danger')
            return redirect(url_for('ventas.nueva'))
        
        total_venta = 0
        detalles_temp = []
        
        for i in range(len(productos_ids)):
            p_id = int(productos_ids[i])
            cant = int(cantidades[i])
            precio_u = float(precios[i])
            subtotal = cant * precio_u
            total_venta += subtotal
            
            producto_db = Producto.query.get(p_id)
            costo_u = producto_db.costo if hasattr(producto_db, 'costo') and producto_db.costo else 0.0

            detalles_temp.append({
                'id_producto': p_id,
                'cantidad': cant,
                'precio_unitario': precio_u,
                'costo_unitario': costo_u
            })
        
        ultimo_id = db.session.query(db.func.max(Venta.id)).scalar() or 0
        folio_automatico = f"F-{ultimo_id + 1:05d}"
        
        nueva_venta = Venta(
            folio=folio_automatico,
            canal=canal,
            id_cliente=int(id_cliente) if id_cliente else None,
            fecha=fecha_venta,
            total=total_venta,
            subtotal=total_venta,
            descuento=0.0,
            estatus='COMPLETADA'
        )
        db.session.add(nueva_venta)
        db.session.commit()
        
        for det in detalles_temp:
            detalle_venta = VentaDetalle(
                id_venta=nueva_venta.id,
                id_producto=det['id_producto'],
                cantidad=det['cantidad'],
                precio_unitario=det['precio_unitario'],
                costo_unitario=det['costo_unitario'],
                descuento=0.0
            )
            db.session.add(detalle_venta)
            
            inv = Inventario.query.filter_by(id_producto=det['id_producto'], id_ubicacion=1).first()
            if inv:
                inv.existencia -= det['cantidad']
                if inv.existencia < 0:
                    inv.existencia = 0
                    
        db.session.commit()
        flash('¡Venta registrada con éxito!', 'success')
        return redirect(url_for('ventas.recibo', id_venta=nueva_venta.id))

    clientes = Cliente.query.all()
    productos_stock = db.session.query(Producto, Inventario.existencia)\
        .join(Inventario, Producto.id == Inventario.id_producto)\
        .filter(Inventario.id_ubicacion == 1, Producto.activo == 1).all()
    
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    return render_template('ventas/nueva.html', clientes=clientes, productos=productos_stock, fecha_hoy=fecha_hoy)

@ventas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    venta = Venta.query.get_or_404(id)
    
    if request.method == 'POST':
        canal = request.form.get('canal')
        id_cliente = request.form.get('id_cliente')
        fecha_str = request.form.get('fecha')
        
        if fecha_str:
            try:
                venta.fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            except ValueError:
                pass
                
        if canal:
            venta.canal = canal
            
        venta.id_cliente = int(id_cliente) if id_cliente else None
        
        # 1. Reintegrar el inventario de los detalles anteriores antes de modificarlos
        detalles_actuales = VentaDetalle.query.filter_by(id_venta=venta.id).all()
        for det_viejo in detalles_actuales:
            inv = Inventario.query.filter_by(id_producto=det_viejo.id_producto, id_ubicacion=1).first()
            if inv:
                inv.existencia += det_viejo.cantidad
            db.session.delete(det_viejo)
            
        # 2. Capturar los nuevos productos enviados desde el formulario
        productos_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        precios = request.form.getlist('precio[]')
        
        if not productos_ids:
            flash('La venta debe tener al menos un producto.', 'danger')
            return redirect(url_for('ventas.editar', id=venta.id))
        
        total_venta = 0
        for i in range(len(productos_ids)):
            p_id = int(productos_ids[i])
            cant = int(cantidades[i])
            precio_u = float(precios[i])
            subtotal = cant * precio_u
            total_venta += subtotal
            
            producto_db = Producto.query.get(p_id)
            costo_u = producto_db.costo if hasattr(producto_db, 'costo') and producto_db.costo else 0.0

            # Crear el nuevo detalle
            nuevo_detalle = VentaDetalle(
                id_venta=venta.id,
                id_producto=p_id,
                cantidad=cant,
                precio_unitario=precio_u,
                costo_unitario=costo_u,
                descuento=0.0
            )
            db.session.add(nuevo_detalle)
            
            # Descontar el stock nuevamente según la nueva cantidad
            inv = Inventario.query.filter_by(id_producto=p_id, id_ubicacion=1).first()
            if inv:
                inv.existencia -= cant
                if inv.existencia < 0:
                    inv.existencia = 0
                    
        venta.total = total_venta
        venta.subtotal = total_venta
        
        db.session.commit()
        flash('¡Venta actualizada con éxito!', 'success')
        return redirect(url_for('ventas.recibo', id_venta=venta.id))

    clientes = Cliente.query.all()
    productos_stock = db.session.query(Producto, Inventario.existencia)\
        .join(Inventario, Producto.id == Inventario.id_producto)\
        .filter(Inventario.id_ubicacion == 1, Producto.activo == 1).all()
        
    detalles = VentaDetalle.query.options(db.joinedload(VentaDetalle.producto)).filter_by(id_venta=venta.id).all()
    
    return render_template('ventas/editar.html', venta=venta, clientes=clientes, productos=productos_stock, detalles=detalles)

@ventas_bp.route('/cliente-rapido', methods=['POST'])
def cliente_rapido():
    nombre = request.form.get('nombre')
    telefono = request.form.get('telefono')
    email = request.form.get('email')
    
    if not nombre:
        return jsonify({'success': False, 'message': 'El nombre es obligatorio'})
    
    try:
        nuevo_cliente = Cliente(nombre=nombre, telefono=telefono, email=email)
        db.session.add(nuevo_cliente)
        db.session.commit()
        return jsonify({
            'success': True,
            'cliente': {
                'id': nuevo_cliente.id,
                'nombre': nuevo_cliente.nombre,
                'telefono': nuevo_cliente.telefono
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@ventas_bp.route('/recibo/<int:id_venta>')
def recibo(id_venta):
    venta = Venta.query.get_or_404(id_venta)
    detalles = VentaDetalle.query.options(db.joinedload(VentaDetalle.producto)).filter_by(id_venta=id_venta).all()
    
    # --- DEPURACIÓN RÁPIDA ---
    print(f"--- VENTA ID: {id_venta} ---")
    for d in detalles:
        print(f"ID Detalle: {d.id} | ID Producto: {d.id_producto} | Producto Objeto: {d.producto}")
        if d.producto:
            print(f"   -> Código: {d.producto.codigo} | Nombre: {d.producto.nombre}")
        else:
            print("   -> ¡El objeto producto es None!")
    # -------------------------

    return render_template('ventas/recibo.html', venta=venta, detalles=detalles)

@ventas_bp.route('/reporte-mensual')
def reporte_mensual():
    filtro_mes = request.args.get('mes', '')
    
    # El campo SKU en tu modelo Producto se llama 'codigo'
    col_codigo = Producto.codigo
    
    query = db.session.query(
        db.extract('year', Venta.fecha).label('anio'),
        db.extract('month', Venta.fecha).label('mes'),
        col_codigo.label('sku'),
        Producto.nombre.label('nombre'),
        db.func.sum(VentaDetalle.cantidad).label('total_cantidad'),
        db.func.sum(VentaDetalle.cantidad * VentaDetalle.precio_unitario).label('total_dinero')
    ).select_from(Venta)\
     .join(VentaDetalle, Venta.id == VentaDetalle.id_venta)\
     .join(Producto, VentaDetalle.id_producto == Producto.id)
     
    if filtro_mes:
        anio, mes = filtro_mes.split('-')
        query = query.filter(
            db.extract('year', Venta.fecha) == int(anio),
            db.extract('month', Venta.fecha) == int(mes)
        )
        
    resultados = query.group_by('anio', 'mes', col_codigo, Producto.nombre)\
                      .order_by(db.desc('anio'), db.desc('mes'), db.func.sum(VentaDetalle.cantidad).desc())\
                      .all()
     
    return render_template('ventas/reporte_mensual.html', resultados=resultados, filtro_mes=filtro_mes)