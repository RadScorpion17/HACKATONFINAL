from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()
bcrypt = Bcrypt()

class Usuario(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    nombre = db.Column(db.String(50), nullable = False)
    apellido = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(100), nullable = False, unique = True)
    password = db.Column(db.String(200), nullable = True)
    telefono = db.Column(db.String(50), nullable = False)
    created_at = db.Column(db.DateTime(50), nullable = False)

    def __init__(self,nombre: str, apellido:str, email:str,telefono:str, password:str):
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.telefono = telefono
        self.password = bcrypt.generate_password_hash(password)
        self.created_at = datetime.now()
            
class Mascotas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    especie = db.Column(db.String(50), nullable= False)
    raza = db.Column(db.String(50), nullable= False)
    edad = db.Column(db.Integer, nullable=False)
    descripcion_mascota = db.Column(db.String(200), nullable = False)
    img = db.Column(db.String(20))
    
    def __init__(self, especie, raza, edad, descripcion_mascota, img):
        self.especie = especie
        self.raza = raza
        self.edad = edad
        self.descripcion_mascota = descripcion_mascota
        self.img = img
        
    
class Busqueda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    descripcion = db.Column(db.String(200), nullable=False)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.now)
    estado = db.Column(db.Boolean, nullable = False)
    
    # Definir la relación con Mascotas
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'))
    mascota = relationship("Mascotas", backref="busquedas")

    def __init__(self, usuario_id, descripcion, estado, mascota_id):
        self.usuario_id = usuario_id
        self.descripcion = descripcion
        self.fecha_y_hora = datetime.now()
        self.estado = estado
        self.mascota_id = mascota_id
        

class Encontrado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    descripcion = db.Column(db.String(200), nullable=False)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.now)
    estado = db.Column(db.Boolean, nullable = False)
    
    # Definir la relación con Mascotas
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'))
    mascota = relationship("Mascotas", backref="encontrados")

    def __init__(self, usuario_id, descripcion, estado, mascota_id):
        self.usuario_id= usuario_id
        self.descripcion = descripcion
        self.fecha_y_hora = datetime.now()
        self.estado = estado
        self.mascota_id = mascota_id
        

