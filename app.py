from flask import Flask
from config import Config
from extensions import db, login_manager
import models  # <--- Importar todo el archivo models asegura que SQLAlchemy registre todas las tablas

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.productos import productos_bp
    from blueprints.inventario import inventario_bp
    from blueprints.ventas import ventas_bp
    from blueprints.compras import compras_bp
    from blueprints.mercadolibre import mercadolibre_bp
    from blueprints.clientes import clientes_bp
    from blueprints.reportes import reportes_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(productos_bp, url_prefix="/productos")
    app.register_blueprint(inventario_bp, url_prefix="/inventario")
    app.register_blueprint(ventas_bp, url_prefix="/ventas")
    app.register_blueprint(compras_bp, url_prefix="/compras")
    app.register_blueprint(mercadolibre_bp, url_prefix="/mercadolibre")
    app.register_blueprint(clientes_bp, url_prefix="/clientes")
    app.register_blueprint(reportes_bp, url_prefix="/reportes")
    
    with app.app_context():
        db.create_all()  # Ahora sí detectará y creará 'venta_detalle' y el resto de tablas
        if not models.Usuario.query.filter_by(usuario="admin").first():
            u = models.Usuario(usuario="admin", nombre="Administrador", rol="ADMIN", activo=True)
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)