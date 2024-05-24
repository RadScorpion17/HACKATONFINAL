from flask import Flask, render_template, redirect, url_for, request, session, send_from_directory
from conexion import db, app, os
from datetime import datetime
from functools import wraps
from sqlalchemy.exc import IntegrityError # esta libreria sirve para manejar errores de integracion como por ejemplo
#cuando se guarda un dato duplicado en una clave de tipo unique
from models import Usuario, bcrypt, Busqueda, Mascotas, Encontrado
from werkzeug.utils import secure_filename

def get_id_by_email(user_email):
    usuario = Usuario.query.filter_by(email=user_email).first()    
    return usuario.id

def validar_sesion():
    if not 'logueado' in session:
        return False
    if not session['logueado']:
        return False

    return True

# Decorador utilizado para validar si el usuario esta logueado
def validar_sesion(endpoint):
    @wraps(endpoint)
    def wrapper(*args, **kwargs):
        if not 'logueado' in session or not session['logueado']:
            return redirect(url_for('login'))
        return endpoint(*args, **kwargs)
    return wrapper

# Endpoint para recuperar un archivo del directorio /upload
@app.route('/images/<filename>')
def serve_images(filename):
   return send_from_directory(app.config['UPLOAD_FOLDER'], filename) 

@app.route('/sobre_nosotros')
def sobre_nosotros():
    return render_template('sobre_nosotros.html')

@app.route('/')
def index():
    #aca hago la lista para busquedas
    busquedas = Busqueda.query.all()
    for busqueda in busquedas:
        # Obtener la mascota asociada a la búsqueda actual
        mascota = Mascotas.query.filter_by(id = busqueda.mascota_id).first()
        # Agregar los datos de la mascota a la búsqueda actual
        busqueda.especie = mascota.especie
        busqueda.raza = mascota.raza
        busqueda.edad = mascota.edad
        busqueda.descripcion_mascota = mascota.descripcion_mascota
        busqueda.img = mascota.img
    
    #aca hago la lista para encontrados
    encontrados = Encontrado.query.all()
    for encuentro in encontrados:
        # Obtener la mascota asociada a la búsqueda actual
        mascota = Mascotas.query.filter_by(id = encuentro.mascota_id).first()
        # Agregar los datos de la mascota a la búsqueda actual
        encuentro.especie = mascota.especie
        encuentro.raza = mascota.raza
        encuentro.edad = mascota.edad
        encuentro.descripcion_mascota = mascota.descripcion_mascota
        encuentro.img = mascota.img

    return render_template('index.html', encontrados=encontrados, busquedas=busquedas)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_email = request.form['email']
        password = request.form['password']

        print(f"User email: {user_email}")
        print(f"Password: {password}")

        # Busca el usuario por email
        usuario = Usuario.query.filter_by(email=user_email).first()

        if usuario is None:
            # Caso de que no encuentre email en la base
            print('hola')
            return render_template('login.html', error_message="Usuario no encontrado")
        
        if bcrypt.check_password_hash(usuario.password, password):
            # Caso que coincidan las contraseñas (contraseña correcta)
            session['logueado'] = True
            session['email'] = user_email
            session['usuario_id'] = usuario.id  # guarda el usuario de la sesión en flask
            
            print("Inicio de sesión exitoso")
            print(session['logueado'], session['email'], session['usuario_id'])
            # En caso que coincida
            return redirect(url_for('index'))
        else:
                # Caso que no coincidan las contraseñas
            print("Contraseña incorrecta")
            print(bcrypt.check_password_hash(usuario.password, password))
            return render_template('login.html', error_message="Contraseña incorrecta")

    # Si el método es GET, simplemente renderiza la plantilla del formulario de inicio de sesión.
    return render_template('login.html')


#ruta de registro de usuarios
@app.route('/registro', methods = ['POST','GET'])
def registro():
    if request.method == 'POST':
        try:
            nombre = request.form['nombre']        
            apellido = request.form['apellido']
            email = request.form['email']
            password = request.form['password']            
            telefono = request.form['telefono']
            
            # Validar que los campos no estén vacíos
            if not (nombre and apellido and email and telefono and password):
                return "Todos los campos son obligatorios" 
            
            usuario = Usuario(nombre,apellido,email,telefono,password)
            db.session.add(usuario)
            db.session.commit()
            session['usuario_id'] = usuario.id
            #TODO
        except IntegrityError: #aca lo que hago es que si el usuario carga 2 veces un mismo correo, paro y le pido que guarde otro
            db.session.rollback()  # Deshacer la transacción fallida
            return "El correo electrónico ya está registrado, por favor use otro."
        except Exception as e:
            return "Error al guardar el usuario en la base de datos: " + str(e)
        
        return render_template('index.html')
    
    
    #TODO: retornar los templates
    return render_template('registro.html')

#ruta de cargar una busqueda
@app.route('/cargar_busqueda', methods=['POST', 'GET'])
@validar_sesion #Uso del decorador para validar si el usuario esta logueado
def cargar_busqueda():
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        estado = estado.lower() == 'true'
        usuario_id = session.get("usuario_id") 
        
        # Datos de la mascota
        especie = request.form['especie']
        raza = request.form['raza']
        edad = request.form['edad']
        descripcion_mascota = request.form['descripcion_mascota']  # Corregido el nombre del campo
        img = request.files['img'] # aca trae la imagen en  y  o sea binario
        img_nombre = ''
        if img != None or img.filename != '':
            try:
                img_nombre = secure_filename(img.filename) # comprobar que sea un archivo seguro y que no sea un script
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_nombre)) #metodo q guarda
            except Exception as e:
                print(e)

        # Creamos una instancia de Mascotas con los datos del formulario
        nueva_mascota = Mascotas(especie=especie, raza=raza, edad=edad, descripcion_mascota=descripcion_mascota, img=img_nombre)
        
        # Guardar la nueva instancia de Mascotas en la base de datos
        db.session.add(nueva_mascota)
        db.session.commit()
        
        # Obtener el ID de la mascota recién creada
        mascota_id = nueva_mascota.id
        
        # Creamos una instancia de Busqueda con los datos del formulario
        busqueda_cargada = Busqueda(usuario_id=usuario_id, descripcion=descripcion, estado=estado, mascota_id=mascota_id)
        
        # Añadimos la instancia a la sesión de la base de datos
        db.session.add(busqueda_cargada)
        # Guardamos los cambios en la base de datos
        db.session.commit() 
        
        return redirect (url_for('busquedas'))
         
    return render_template('cargar_busqueda.html')
  

#ver busqueda cargada por usuario
@app.route('/ver_busquedas',methods=['GET', 'POST'])
@validar_sesion
def ver_busquedas():
    usuario_id = session.get('usuario_id')
    busquedas = Busqueda.query.filter_by(usuario_id=usuario_id).all()
    for busqueda in busquedas:
        # Obtener la mascota asociada a la búsqueda actual
        mascota = Mascotas.query.get(busqueda.mascota_id)
        # Agregar los datos de la mascota a la búsqueda actual
        busqueda.especie = mascota.especie
        busqueda.raza = mascota.raza
        busqueda.edad = mascota.edad
        busqueda.descripcion_mascota = mascota.descripcion_mascota
        busqueda.img = mascota.img
        busqueda.fecha_formateada = busqueda.fecha_y_hora.strftime('%Y-%m-%d')
    return render_template('ver_busquedas.html', busquedas=busquedas)

# Todas las busquedas
@app.route('/busquedas',methods=['GET'])
def busquedas():
    busquedas = Busqueda.query.all()
    for busqueda in busquedas:
        # Obtener la mascota asociada a la búsqueda actual
        mascota = Mascotas.query.get(busqueda.mascota_id)
        # Agregar los datos de la mascota a la búsqueda actual
        busqueda.especie = mascota.especie
        busqueda.raza = mascota.raza
        busqueda.edad = mascota.edad
        busqueda.descripcion_mascota = mascota.descripcion_mascota
        busqueda.img = mascota.img
        busqueda.fecha_formateada = busqueda.fecha_y_hora.strftime('%Y-%m-%d')

    return render_template('busquedas.html', busquedas=busquedas)

@app.route('/encuentros',methods=['GET'])
def encuentros():
    encontrados = Encontrado.query.all()
    for encuentro in encontrados:
        # Obtener la mascota asociada a la búsqueda actual
        mascota = Mascotas.query.get(encuentro.mascota_id)
        # Agregar los datos de la mascota a la búsqueda actual
        encuentro.especie = mascota.especie
        encuentro.raza = mascota.raza
        encuentro.edad = mascota.edad
        encuentro.descripcion_mascota = mascota.descripcion_mascota
        encuentro.img = mascota.img
        encuentro.fecha_formateada = encuentro.fecha_y_hora.strftime('%Y-%m-%d')
    return render_template('encuentros.html', encontrados=encontrados)

#ruta para modificar las busquedas
@app.route('/modificar_busqueda/<int:busqueda_id>', methods=['GET', 'POST'])
@validar_sesion
def modificar_busqueda(busqueda_id):
    #creamos una variable para extraer los datos de la busqueda hecha segun el id

    busqueda_a_modificar = Busqueda.query.get(busqueda_id)
    
    mascota_a_modificar = Mascotas.query.get(busqueda_a_modificar.mascota_id)
    
    print(mascota_a_modificar)
    
    #recibimos los datos del formulario 
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        estado = estado.lower() == 'true'
        
        # Datos de la mascota
        especie = request.form['especie']
        raza = request.form['raza']
        edad = request.form['edad']
        descripcion_mascota = request.form['descripcion_mascota']  # Corregido el nombre del campo
        img = request.files['img'] # aca trae la imagen en  y  o sea binario

        if img != None or img.filename != '':
            try:
                img_nombre = secure_filename(img.filename) # comprobar que sea un archivo seguro y que no sea un script
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_nombre)) #metodo q guarda
            except Exception as e:
                print(e)
        else: #Si no hay imagen a modificar, se mantiene la imagen existente
            img_nombre = busqueda_a_modificar.img

                
          # Manejar la fecha de la búsqueda
        fecha_y_hora = request.form['fecha_y_hora']
        if fecha_y_hora:
            busqueda_a_modificar.fecha_y_hora = datetime.strptime(fecha_y_hora, '%Y-%m-%d')


        # Modificamos los valores ya existentes
        busqueda_a_modificar.descripcion = descripcion
        busqueda_a_modificar.estado = estado
        mascota_a_modificar.especie = especie
        mascota_a_modificar.raza = raza
        mascota_a_modificar.edad = edad
        mascota_a_modificar.descripcion_mascota = descripcion_mascota
        mascota_a_modificar.img = img_nombre
        # guardamos lo que hicimos
        db.session.commit()
    # redireccionamos a la pagina ver notas
        return redirect(url_for("ver_busquedas"))
    
    return render_template("modificar_busquedas.html", busqueda_a_modificar = busqueda_a_modificar,mascota_a_modificar=mascota_a_modificar) 

#ruta de borrar una busqueda
@app.route('/eliminar_busqueda/<int:busqueda_id>', methods=['POST'])
@validar_sesion
def eliminar_busqueda(busqueda_id):
    # Obtener la búsqueda a eliminar
    busqueda_a_eliminar = Busqueda.query.get(busqueda_id)

    if busqueda_a_eliminar:
        # Obtener la mascota asociada a la búsqueda
        mascota_a_eliminar = Mascotas.query.get(busqueda_a_eliminar.mascota_id)
        
        if mascota_a_eliminar:
            # Eliminar la mascota asociada a la búsqueda
            db.session.delete(mascota_a_eliminar)
        
        # Eliminar la búsqueda
        db.session.delete(busqueda_a_eliminar)
        
        # Guardar los cambios
        db.session.commit()

        return redirect(url_for('ver_busquedas'))


#ruta de cargar un encuentro o mascota encontrada
@app.route('/cargar_encuentro', methods=['POST', 'GET'])
@validar_sesion
def cargar_encuentro():
    # Verificar si el método de la solicitud es POST
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        estado = estado.lower() == 'true'
        usuario_id = session.get("usuario_id") 
        
        # Datos de la mascota
        especie = request.form['especie']
        raza = request.form['raza']
        edad = request.form['edad']
        descripcion_mascota = request.form['descripcion_mascota']  # Corregido el nombre del campo
        img = request.files['img'] # aca trae la imagen en  y  o sea binario

        if img != None or img.filename != '':
            try:
                img_nombre = secure_filename(img.filename) # comprobar que sea un archivo seguro y que no sea un script
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_nombre)) #metodo q guarda
            except Exception as e:
                print(e)

        # Creamos una instancia de Mascotas con los datos del formulario
        nueva_mascota = Mascotas(especie=especie, raza=raza, edad=edad, descripcion_mascota=descripcion_mascota, img=img_nombre)
        # Guardar la nueva instancia de Mascotas en la base de datos
        db.session.add(nueva_mascota)
        db.session.commit()
        
        # Obtener el ID de la mascota recién creada
        mascota_id = nueva_mascota.id
        
        # Creamos una instancia de Busqueda con los datos del formulario
        encuentro_cargado = Encontrado(usuario_id=usuario_id, descripcion=descripcion, estado=estado, mascota_id=mascota_id)
        
        # Añadimos la instancia a la sesión de la base de datos
        db.session.add(encuentro_cargado)
        # Guardamos los cambios en la base de datos
        db.session.commit()
        
        return redirect (url_for('encuentros'))
    return render_template('cargar_encuentro.html')
  

#ver encuentro cargado
@app.route('/ver_encuentros',methods=['GET', 'POST'])
@validar_sesion
def ver_encuentros():
    usuario_id = session.get('usuario_id')
    encontrados = Encontrado.query.filter_by(usuario_id=usuario_id).all()
    for encuentro in encontrados:
        # Obtener la mascota asociada a la búsqueda actual
        mascota = Mascotas.query.get(encuentro.mascota_id)
        # Agregar los datos de la mascota a la búsqueda actual
        encuentro.especie = mascota.especie
        encuentro.raza = mascota.raza
        encuentro.edad = mascota.edad
        encuentro.descripcion_mascota = mascota.descripcion_mascota
        encuentro.img = mascota.img
        encuentro.fecha_formateada = encuentro.fecha_y_hora.strftime('%Y-%m-%d')
    return render_template('ver_encuentros.html', encontrados=encontrados)

#ruta para modificar encuentros
@app.route('/modificar_encuentro/<int:encontrado_id>', methods=['GET', 'POST'])
@validar_sesion
def modificar_encuentro(encontrado_id):
    #creamos una variable para extraer los datos de la busqueda hecha segun el id
    encuentro_a_modificar = Encontrado.query.get(encontrado_id)
    mascota_a_modificar = Mascotas.query.get(encuentro_a_modificar.mascota_id)
    
    #recibimos los datos del formulario 
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        estado = estado.lower() == 'true'
        
        # Datos de la mascota
        especie = request.form['especie']
        raza = request.form['raza']
        edad = request.form['edad']
        descripcion_mascota = request.form['descripcion']  # Corregido el nombre del campo
        img = request.files['img'] # Recolecta el binario de la imagen del formulario

        if img != None or img.filename != '':
            try:
                img_nombre = secure_filename(img.filename) # comprobar que sea un archivo seguro y que no sea un script
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_nombre)) #metodo q guarda
            except Exception as e:
                print(e)
        else: #Si no hay imagen a modificar, se mantiene la imagen existente
            img_nombre = mascota_a_modificar.img
        
        # Manejar la fecha de la búsqueda
        fecha_y_hora = request.form['fecha_y_hora']
        if fecha_y_hora:
            encuentro_a_modificar.fecha_y_hora = datetime.strptime(fecha_y_hora, '%Y-%m-%d')
        # Modificamos los valores ya existentes
        encuentro_a_modificar.descripcion = descripcion
        encuentro_a_modificar.estado = estado
        mascota_a_modificar.especie = especie
        mascota_a_modificar.raza = raza
        mascota_a_modificar.edad = edad
        mascota_a_modificar.descripcion_mascota = descripcion_mascota
        mascota_a_modificar.img = img_nombre
        
        # guardamos lo que hicimos
        db.session.commit()
    # redireccionamos a la pagina ver notas
        return redirect(url_for("ver_encuentros"))
    
    return render_template("modificar_encuentros.html", encuentro_a_modificar = encuentro_a_modificar, mascota_a_modificar= mascota_a_modificar) 

#ruta de borrar una busqueda
@app.route('/eliminar_encuentro/<int:encontrado_id>', methods=['POST'])
@validar_sesion
def eliminar_encuentro(encuentro_id):
    # Obtener la búsqueda a eliminar
    encuentro_a_eliminar = Encontrado.query.get(encuentro_id)

    if encuentro_a_eliminar:
        # Obtener la mascota asociada a la búsqueda
        mascota_a_eliminar = Mascotas.query.get(encuentro_a_eliminar.mascota_id)
        
        if mascota_a_eliminar:
            # Eliminar la mascota asociada a la búsqueda
            db.session.delete(mascota_a_eliminar)
        
        # Eliminar la búsqueda
        db.session.delete(encuentro_a_eliminar)
        
        # Guardar los cambios
        db.session.commit()

        return redirect(url_for('ver_encuentros'))
    
@app.route('/ver_mascota_buscada/<int:busqueda_id>', methods=['GET'])
def ver_mascota_buscada(busqueda_id):
    busquedas = Busqueda.query.filter_by(id = busqueda_id).first()
    print(busquedas)
    usuario = Usuario.query.filter_by(id = busquedas.usuario_id).first()
    mascota = Mascotas.query.filter_by(id = busquedas.mascota_id).first()
    
    return render_template('ver_mascota_buscada.html' ,busquedas=busquedas, usuario= usuario, mascota=mascota)

@app.route('/ver_mascota_encontrada/<int:encontrado_id>', methods=['GET'])
def ver_mascota_encontrada(encontrado_id):
    encuentros = Encontrado.query.filter_by(id = encontrado_id).first()
    usuario = Usuario.query.filter_by(id = encuentros.usuario_id).first()
    mascota = Mascotas.query.filter_by(id = encuentros.mascota_id).first()
    
    return render_template('ver_mascota_encontrada.html' ,encuentros=encuentros, usuario= usuario, mascota=mascota)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug= True)