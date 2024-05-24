import os
from models import db
from flask import Flask

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mascotas.db"
app.config["SECRET_KEY"] = "aramicys"
## RUTA DE CARGA DE ARCHIVOS
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(),'upload')
## TAMAÑO MAXIMO DE ARCHIVO A 16MB
app.config["MAX_CONTENT_PATH"] = 16*1024*1024

db.init_app(app)

with app.app_context():
    db.create_all()