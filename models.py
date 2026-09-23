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
    
    productos = db.relationship('Producto', backref='categoria', lazy=True)


class Marca(db.Model):
    __tablename__ = 'marca'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    productos = db.relationship('Producto', backref='marca', lazy=True)


class Ubicacion(db.Model):
    __tablename__ = 'ubicacion'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    inventarios = db.relationship('Inventario', backref='ubicacion', lazy=True)


class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    
    ventas = db.relationship('Venta', backref='cliente', lazy=True)


class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    
    compras = db.relationship('Compra', backref='proveedor', lazy=True)


class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    sku = db.Column(db.String(80), unique=True, nullable=False)
    codigo_barras = db.Column(db.String(100), unique=True, nullable=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    id_categoria = db.Column(db.BigInteger, db.ForeignKey('categoria.id'), nullable=True)
    id_marca = db.Column(db.BigInteger, db.ForeignKey('marca.id'), nullable=True)
    modelo = db.Column(db.String(100), nullable=True)
    condicion = db.Column(db.String(30), nullable=False, default='Nuevo')
    precio_costo = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    precio_venta = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    precio_minimo = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_alta = db.Column(db.DateTime, nullable=True)
    costo = db.Column(db.Numeric(10, 2), default=0.0)
    precio = db.Column(db.Numeric(10, 2), default=0.0)

    # Propiedad para compatibilidad con código que use 'producto.codigo'
    @property
    def codigo(self):
        return self.sku
    
    @codigo.setter
    def codigo(self, value):
        self.sku = value

    inventarios = db.relationship('Inventario', backref='producto', lazy=True)
    detalles_venta = db.relationship('VentaDetalle', foreign_keys='VentaDetalle.id_producto', back_populates='producto', lazy=True)
    detalles_compra = db.relationship('CompraDetalle', backref='producto', lazy=True)


class Inventario(db.Model):
    __tablename__ = 'inventarios'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_producto = db.Column(db.BigInteger, db.ForeignKey('productos.id'), nullable=False)
    id_ubicacion = db.Column(db.BigInteger, db.ForeignKey('ubicacion.id'), default=1)
    existencia = db.Column(db.Integer, nullable=False, default=0)
    apartado = db.Column(db.Integer, nullable=False, default=0)


class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    folio = db.Column(db.String(40), unique=True, nullable=False)
    id_cliente = db.Column(db.BigInteger, db.ForeignKey('cliente.id'), nullable=True)
    canal = db.Column(db.String(30), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), default=0.0)
    descuento = db.Column(db.Numeric(12, 2), default=0.0)
    total = db.Column(db.Numeric(12, 2), default=0.0)
    estatus = db.Column(db.String(30), nullable=False, default='COMPLETADA')
    id_usuario = db.Column(db.BigInteger, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship('VentaDetalle', foreign_keys='VentaDetalle.id_venta', back_populates='venta', cascade="all, delete-orphan", lazy=True)


class VentaDetalle(db.Model):
    __tablename__ = 'venta_detalles'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_venta = db.Column(db.BigInteger, db.ForeignKey('ventas.id'), nullable=False)
    id_producto = db.Column(db.BigInteger, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    costo_unitario = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    descuento = db.Column(db.Numeric(12, 2), nullable=True, default=0.0)

    producto = db.relationship('Producto', foreign_keys=[id_producto], back_populates='detalles_venta')
    venta = db.relationship('Venta', foreign_keys=[id_venta], back_populates='detalles')


class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    folio = db.Column(db.String(50), unique=True, nullable=False)
    id_proveedor = db.Column(db.BigInteger, db.ForeignKey('proveedor.id'))
    fecha = db.Column(db.Date, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2), default=0.0)
    total = db.Column(db.Numeric(10, 2), default=0.0)
    estatus = db.Column(db.String(30), default='COMPLETADA')

    detalles = db.relationship('CompraDetalle', backref='compra', cascade="all, delete-orphan", lazy=True)


class CompraDetalle(db.Model):
    __tablename__ = 'compra_detalle'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id_compra = db.Column(db.BigInteger, db.ForeignKey('compra.id'), nullable=False)
    id_producto = db.Column(db.BigInteger, db.ForeignKey('productos.id'), nullable=False)
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
    id_cuenta = db.Column(db.BigInteger, db.ForeignKey('cuenta_mercadolibre.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), default=0.0)
    estatus = db.Column(db.String(50))


class NotificacionML(db.Model):
    __tablename__ = 'notificacion_ml'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    resource = db.Column(db.String(255))
    topic = db.Column(db.String(100))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)