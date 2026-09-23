from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default="USER")
    activo = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    productos = db.relationship(
        'Producto',
        primaryjoin='Categoria.id == foreign(Producto.id_categoria)',
        backref='categoria',
        lazy=True,
        viewonly=True
    )


class Marca(db.Model):
    __tablename__ = 'marca'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    productos = db.relationship(
        'Producto',
        primaryjoin='Marca.id == foreign(Producto.id_marca)',
        backref='marca',
        lazy=True,
        viewonly=True
    )


class Ubicacion(db.Model):
    __tablename__ = 'ubicacion'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    inventarios = db.relationship(
        'Inventario',
        primaryjoin='Ubicacion.id == foreign(Inventario.id_ubicacion)',
        backref='ubicacion',
        lazy=True,
        viewonly=True
    )


class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    
    ventas = db.relationship(
        'Venta',
        primaryjoin='Cliente.id == foreign(Venta.id_cliente)',
        backref='cliente',
        lazy=True,
        viewonly=True
    )


class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    
    compras = db.relationship(
        'Compra',
        primaryjoin='Proveedor.id == foreign(Compra.id_proveedor)',
        backref='proveedor',
        lazy=True,
        viewonly=True
    )


class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sku = db.Column(db.String(80), unique=True, nullable=False)
    codigo_barras = db.Column(db.String(100), unique=True, nullable=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    id_categoria = db.Column(db.BigInteger, nullable=True)
    id_marca = db.Column(db.BigInteger, nullable=True)
    modelo = db.Column(db.String(100), nullable=True)
    condicion = db.Column(db.String(30), nullable=False, default='Nuevo')
    precio_costo = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    precio_venta = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    precio_minimo = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_alta = db.Column(db.DateTime, nullable=True)
    costo = db.Column(db.Numeric(10, 2), default=0.0)
    precio = db.Column(db.Numeric(10, 2), default=0.0)

    @property
    def codigo(self):
        return self.sku
    
    @codigo.setter
    def codigo(self, value):
        self.sku = value

    inventarios = db.relationship(
        'Inventario',
        primaryjoin='Producto.id == foreign(Inventario.id_producto)',
        backref='producto',
        lazy=True,
        viewonly=True
    )
    
    detalles_venta = db.relationship(
        'VentaDetalle',
        primaryjoin='Producto.id == foreign(VentaDetalle.id_producto)',
        backref='producto',
        lazy=True,
        viewonly=True
    )
    
    detalles_compra = db.relationship(
        'CompraDetalle',
        primaryjoin='Producto.id == foreign(CompraDetalle.id_producto)',
        backref='producto_compra',
        lazy=True,
        viewonly=True
    )


class Inventario(db.Model):
    __tablename__ = 'inventarios'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_producto = db.Column(db.BigInteger, nullable=False)
    id_ubicacion = db.Column(db.BigInteger, nullable=True, default=1)
    existencia = db.Column(db.Integer, nullable=False, default=0)
    apartado = db.Column(db.Integer, nullable=False, default=0)


class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    folio = db.Column(db.String(40), unique=True, nullable=False)
    id_cliente = db.Column(db.BigInteger, nullable=True)
    canal = db.Column(db.String(30), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), default=0.0)
    descuento = db.Column(db.Numeric(12, 2), default=0.0)
    total = db.Column(db.Numeric(12, 2), default=0.0)
    estatus = db.Column(db.String(30), nullable=False, default='COMPLETADA')
    id_usuario = db.Column(db.BigInteger, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship(
        'VentaDetalle',
        primaryjoin='Venta.id == foreign(VentaDetalle.id_venta)',
        backref='venta',
        cascade="all, delete-orphan",
        lazy=True,
        viewonly=True
    )


class VentaDetalle(db.Model):
    __tablename__ = 'venta_detalles'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_venta = db.Column(db.BigInteger, nullable=False)
    id_producto = db.Column(db.BigInteger, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    costo_unitario = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    descuento = db.Column(db.Numeric(12, 2), nullable=True, default=0.0)
    # Las relaciones producto y venta se crean vía backref arriba


class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    folio = db.Column(db.String(50), unique=True, nullable=False)
    id_proveedor = db.Column(db.BigInteger, nullable=True)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2), default=0.0)
    total = db.Column(db.Numeric(10, 2), default=0.0)
    estatus = db.Column(db.String(30), default='COMPLETADA')

    detalles = db.relationship(
        'CompraDetalle',
        primaryjoin='Compra.id == foreign(CompraDetalle.id_compra)',
        backref='compra',
        cascade="all, delete-orphan",
        lazy=True,
        viewonly=True
    )


class CompraDetalle(db.Model):
    __tablename__ = 'compra_detalle'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_compra = db.Column(db.BigInteger, nullable=False)
    id_producto = db.Column(db.BigInteger, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    costo_unitario = db.Column(db.Numeric(10, 2), nullable=False)


class CuentaMercadoLibre(db.Model):
    __tablename__ = 'cuenta_mercadolibre'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(50))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)


class OrdenML(db.Model):
    __tablename__ = 'orden_ml'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False)
    id_cuenta = db.Column(db.BigInteger, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), default=0.0)
    estatus = db.Column(db.String(50))


class NotificacionML(db.Model):
    __tablename__ = 'notificacion_ml'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    resource = db.Column(db.String(255))
    topic = db.Column(db.String(100))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)