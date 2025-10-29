Proyecto modernizado generado automáticamente.

Estructura:
- app.py                -> Aplicación Flask principal
- templates/            -> Plantillas Jinja2 (base, index, reservas, nueva reserva)
- static/               -> CSS y JS
- data/reservas.db      -> Base de datos SQLite (se crea al iniciar)
- data/import_reservas.csv -> Si colocas aquí un CSV con reservas, se importará al iniciar

Instrucciones rápidas:
1. Crear un entorno virtual:
   python -m venv venv
   source venv/bin/activate   (Linux/macOS)
   venv\Scripts\activate      (Windows)

2. Instalar dependencias:
   pip install -r requirements.txt

3. Ejecutar:
   python app.py

La app correrá en http://127.0.0.1:5000/
