# Comercial Link — versión completa funcional

Sistema Flask + MySQL para catálogo, inventario, compras, ventas, clientes, reportes y Mercado Libre.

## Instalación Windows
1. Instala Python 3.13 y MySQL 8.
2. Ejecuta `database/schema.sql` desde Navicat/MySQL.
3. Copia `.env.example` a `.env` y coloca la clave de MySQL.
4. Ejecuta `INSTALAR.bat`.
5. Ejecuta `INICIAR.bat`.
6. Abre `http://127.0.0.1:5000`.

Usuario inicial: `admin` / `admin123`. Cambia esta contraseña después del primer acceso.

## Mercado Libre
Configura `ML_CLIENT_ID`, `ML_CLIENT_SECRET` y `ML_REDIRECT_URI`. El callback debe coincidir exactamente con el registrado en Mercado Libre Developers. El webhook de ventas queda en `/mercadolibre/webhook` y está preparado para recibir `orders_v2`. La sincronización de una orden por ID usa el endpoint oficial de órdenes.

## Producción
Usa HTTPS, Nginx y Gunicorn. No publiques Flask directamente a Internet. Mantén secretos solamente en `.env`.
