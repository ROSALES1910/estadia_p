from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from bson import ObjectId
from datetime import datetime

from models import (
    alumnos_col,
    alumnos_password_col,
    alumnos_servicio_col,
    alumnos_servicio_new_col,
    asistencia_col,
    asistencia_new_col,
    colegios_col,
    comentarios_col,
    horarios_col,
    proyectos_col,
    usuarios_col,
    instituciones_col,
    logs_col
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "clave_secreta_segura"

# ========== LOGIN ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Buscar por nombre_usuario en lugar de username
        usuario = usuarios_col.find_one({"nombre_usuario": username}, {"_id": 0})

        # Validar credenciales y que el usuario esté activo
        if usuario and usuario.get("password") == password and usuario.get("status") == "Activo":
            session['usuario'] = usuario['nombre_usuario']
            session['rol'] = usuario.get('rol', 'alumno')  # si no existe rol, por defecto 'alumno'
            return redirect('/dashboard')
        else:
            return render_template('auth/login.html', error="Credenciales inválidas o usuario inactivo")

    return render_template('auth/login.html')
# ========== LOGOUT ==========
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))  # Redirige al login institucional

# ========== DASHBOARD ==========
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect('/login')

    rol = session.get('rol', 'alumno')
    usuario = session.get('usuario')

    return render_template('dashboard/index.html', rol=rol, usuario=usuario)

# ========== ADMIN DASHBOARD ==========
@app.route('/admin')
def admin_dashboard():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect('/login')
    return render_template('admin/dashboard.html', usuario=session['usuario'])

# ========== ADMIN USUARIOS ==========
@app.route('/admin/usuarios', methods=['GET', 'POST'])
def admin_usuarios():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        rol = request.form.get('rol', 'alumno')

        usuarios_col.insert_one({
            "username": username,
            "password": password,
            "rol": rol,
            "created_at": datetime.now()
        })

        flash("Usuario creado correctamente", "success")
        return redirect(url_for('admin_usuarios'))

    return render_template('admin/usuarios.html', usuario=session['usuario'])

# ========== ADMIN CONFIGURACIÓN ==========
@app.route('/admin/configuracion', methods=['GET', 'POST'])
def admin_configuracion():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        institucion = request.form.get('institucion', '').strip()
        max_alumnos = int(request.form.get('max_alumnos', 0))

        logs_col.insert_one({
            "accion": "configuracion",
            "institucion": institucion,
            "max_alumnos": max_alumnos,
            "usuario": session['usuario'],
            "fecha": datetime.now()
        })

        flash("Configuración guardada correctamente", "success")
        return redirect(url_for('admin_configuracion'))

    return render_template('admin/configuracion.html', usuario=session['usuario'])



# ========== ALUMNOS ==========
@app.route('/alumnos/registrar', methods=['GET', 'POST'])
def registrar_alumno():
    if request.method == 'POST':
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "apellido_paterno": request.form.get("apellido_paterno", "").strip(),
            "apellido_materno": request.form.get("apellido_materno", "").strip(),
            "matricula": request.form.get("matricula", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "email": request.form.get("email", "").strip(),
            "escolaridad": request.form.get("escolaridad", "").strip(),
            "semestre": request.form.get("semestre", "").strip(),
            "institucion": request.form.get("institucion", "").strip(),
            "clave_institucion": request.form.get("clave_institucion", "").strip(),
            "ocupacion": request.form.get("ocupacion", "").strip(),
            "comentarios": request.form.get("comentarios", "").strip(),
            "documentacion": request.form.get("documentacion", "").strip(),
            "estado": "Activo"
        }

        campos_obligatorios = ["nombre", "apellido_paterno", "matricula"]
        faltantes = [campo for campo in campos_obligatorios if not datos[campo]]
        if faltantes:
            error = f"Faltan campos obligatorios: {', '.join(faltantes)}"
            return render_template("alumnos/registrar_nuevo_alumno.html", error=error, datos=datos)

        if alumnos_col.find_one({"matricula": datos["matricula"]}):
            error = "Ya existe un alumno con esa matrícula."
            return render_template("alumnos/registrar_nuevo_alumno.html", error=error, datos=datos)

        try:
            alumnos_col.insert_one(datos)
            return redirect(url_for("registrar_alumno", mensaje="Alumno registrado correctamente"))
        except Exception as e:
            error = f"Ocurrió un error al registrar: {str(e)}"
            return render_template("alumnos/registrar_nuevo_alumno.html", error=error, datos=datos)

    # ← Aquí está el cambio importante: pasar datos vacíos en GET
    mensaje = request.args.get("mensaje")
    return render_template("alumnos/registrar_nuevo_alumno.html", mensaje=mensaje, datos={})

@app.route('/alumnos/activar', methods=['GET', 'POST'])
def activar_alumno():
    mensaje = None
    error = None

    if request.method == 'POST':
        matricula = request.form.get('alumno')
        nuevo_estado = request.form.get('estado')

        if not matricula or not nuevo_estado:
            error = "Debes seleccionar un alumno y un estado."
        else:
            try:
                alumnos_col.update_one(
                    {"matricula": matricula},
                    {"$set": {"estado": nuevo_estado.capitalize()}}
                )
                mensaje = f"Estado actualizado a {nuevo_estado.capitalize()} correctamente."
            except Exception as e:
                error = f"Ocurrió un error al actualizar: {str(e)}"

    alumnos = list(alumnos_col.find({}, {"matricula": 1, "nombre": 1}))
    return render_template(
        'alumnos/activar_e_inactivar_alumno.html',
        alumnos=alumnos,
        mensaje=mensaje,
        error=error
    )

@app.route('/alumnos/modificar', methods=['GET', 'POST'])
def modificar_alumno():
    mensaje = None
    error = None

    if request.method == 'POST':
        alumno_id = request.form.get('alumno')
        if not alumno_id:
            error = "Debes seleccionar un alumno."
        else:
            cambios = {
                "nombre": request.form.get("nombre", "").strip(),
                "apellido_paterno": request.form.get("apellido_paterno", "").strip(),
                "apellido_materno": request.form.get("apellido_materno", "").strip(),
                "telefono": request.form.get("telefono", "").strip(),
                "email": request.form.get("email", "").strip(),
                "matricula": request.form.get("matricula", "").strip(),
                "escolaridad": request.form.get("escolaridad", "").strip(),
                "semestre": request.form.get("semestre", "").strip(),
                "institucion": request.form.get("institucion", "").strip(),
                "carrera": request.form.get("carrera", "").strip(),
                "comentarios": request.form.get("comentarios", "").strip()
            }

            cambios = {k: v for k, v in cambios.items() if v}

            try:
                alumnos_col.update_one(
                    {"_id": ObjectId(alumno_id)},
                    {"$set": cambios}
                )
                mensaje = "Datos del alumno actualizados correctamente."
            except Exception as e:
                error = f"Ocurrió un error al actualizar: {str(e)}"

    alumnos = list(alumnos_col.find({}, {"_id": 1, "nombre": 1}))
    return render_template(
        'alumnos/modificar_datos_alumno.html',
        alumnos=alumnos,
        mensaje=mensaje,
        error=error
    )
    
@app.route('/alumnos/asignar-proyecto', methods=['GET', 'POST'])
def asignar_proyecto():
    mensaje = None
    error = None

    if request.method == 'POST':
        alumno_matricula = request.form.get('alumno')
        proyecto_nombre = request.form.get('proyecto')
        descripcion = request.form.get('descripcion', '').strip()

        if not alumno_matricula or not proyecto_nombre:
            error = "Debes seleccionar un alumno y un proyecto."
        else:
            proyecto = proyectos_col.find_one({"nombre": proyecto_nombre})
            if not proyecto:
                error = "El proyecto seleccionado no existe."
            else:
                try:
                    alumnos_col.update_one(
                        {"matricula": alumno_matricula},
                        {"$set": {
                            "proyecto": proyecto_nombre,
                            "descripcion_proyecto": descripcion,
                            "id_proyecto": proyecto.get("id", proyecto.get("_id"))
                        }}
                    )
                    mensaje = f"Proyecto asignado correctamente a {alumno_matricula}."
                except Exception as e:
                    error = f"Ocurrió un error al asignar el proyecto: {str(e)}"

    alumnos = list(alumnos_col.find({}, {"matricula": 1, "nombre": 1}))
    proyectos = list(proyectos_col.find({}, {"id": 1, "nombre": 1}))
    return render_template(
        'alumnos/asignar_cambiar_proyecto.html',
        alumnos=alumnos,
        proyectos=proyectos,
        mensaje=mensaje,
        error=error
    )
    
@app.route('/alumnos/desasignar-proyecto', methods=['GET', 'POST'])
def desasignar_proyecto():
    mensaje = None
    error = None

    if request.method == 'POST':
        alumno_matricula = request.form.get('alumno')

        if not alumno_matricula:
            error = "Debes seleccionar un alumno."
        else:
            try:
                alumnos_col.update_one(
                    {"matricula": alumno_matricula},
                    {"$unset": {
                        "proyecto": "",
                        "descripcion_proyecto": "",
                        "id_proyecto": ""
                    }}
                )
                mensaje = f"Proyecto desasignado correctamente del alumno {alumno_matricula}."
            except Exception as e:
                error = f"Ocurrió un error al desasignar el proyecto: {str(e)}"

    alumnos = list(alumnos_col.find({"proyecto": {"$exists": True}}, {"matricula": 1, "nombre": 1}))
    return render_template(
        'alumnos/desasignar_proyecto.html',  # nombre del archivo HTML
        alumnos=alumnos,
        mensaje=mensaje,
        error=error
    )
    
@app.route('/alumnos/modificar-contrasena', methods=['GET', 'POST'])
def modificar_contrasena():
    mensaje = request.args.get('mensaje')
    error = request.args.get('error')

    if request.method == 'POST':
        alumno_matricula = request.form.get('alumno')
        nueva_contrasena = request.form.get('contrasena')

        if not alumno_matricula or not nueva_contrasena:
            return redirect(url_for('modificar_contrasena', error="Debes seleccionar un alumno y proporcionar una nueva contraseña."))

        try:
            alumnos_col.update_one(
                {"matricula": alumno_matricula},
                {"$set": {"contrasena": nueva_contrasena}}
            )
            return redirect(url_for('modificar_contrasena', mensaje=f"Contraseña actualizada correctamente para el alumno {alumno_matricula}."))
        except Exception as e:
            return redirect(url_for('modificar_contrasena', error=f"Ocurrió un error al actualizar la contraseña: {str(e)}"))

    alumnos = list(alumnos_col.find({}, {"matricula": 1, "nombre": 1}))
    return render_template(
        'alumnos/modificar_contrasena.html',  # 👈 nombre de la plantilla
        alumnos=alumnos,
        mensaje=mensaje,
        error=error
    )
    
@app.route('/alumnos/asignar-horario', methods=['GET', 'POST'])
def asignar_horario():
    mensaje = request.args.get('mensaje')
    id_alumno = request.args.get('id_alumno')
    seleccionado = None
    horario = {}

    if request.method == 'POST':
        id_alumno = request.form.get('id_alumno')
        sin_horario = 'sin_horario' in request.form

        horario = {}
        for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']:
            inicio = request.form.get(f'{dia}_inicio')
            fin = request.form.get(f'{dia}_fin')
            horario[dia] = [inicio, fin]

        alumnos_col.update_one(
            {"id_alumno": id_alumno},
            {"$set": {
                "horario": horario,
                "sin_horario": sin_horario
            }}
        )
        return redirect(url_for('asignar_horario', id_alumno=id_alumno, mensaje='Horario actualizado correctamente'))

    alumnos = list(alumnos_col.find({}, {
        "id_alumno": 1,
        "nombre": 1,
        "apellido_paterno": 1,
        "apellido_materno": 1
    }))

    if id_alumno:
        seleccionado = alumnos_col.find_one({"id_alumno": id_alumno})
        if seleccionado:
            horario = seleccionado.get("horario", {})
        else:
            mensaje = f"No se encontró el alumno con ID {id_alumno}."

    return render_template(
        'alumnos/asignar_cambiar_horario.html',
        alumnos=alumnos,
        seleccionado=seleccionado,
        horario=horario,
        mensaje=mensaje
    )

@app.route('/alumnos/comentarios', methods=['GET', 'POST'])
def comentarios_alumno():
    mensaje = None
    error = None

    if request.method == 'POST':
        matricula = request.form.get('alumno')
        comentario = request.form.get('comentario', '').strip()

        if not matricula or not comentario:
            error = "⚠ Debes seleccionar un alumno y escribir un comentario."
        else:
            alumno = alumnos_col.find_one({"matricula": matricula})
            if alumno:
                comentarios_col.insert_one({
                    "matricula": matricula,
                    "comentario": comentario,
                    "fecha": datetime.now(),
                    "usuario": session.get("usuario", "sistema")
                })
                mensaje = "✅ Comentario guardado correctamente."
            else:
                error = "⚠ La matrícula no corresponde a ningún alumno registrado."

    alumnos = list(alumnos_col.find(
        {"matricula": {"$nin": [None, "", "None", "Sin dato"]}},
        {"_id": 0, "matricula": 1, "nombre": 1}
    ))

    return render_template('alumnos/comentarios_alumno.html',
                           alumnos=alumnos,
                           mensaje=mensaje,
                           error=error)

@app.route('/alumnos/log', methods=['GET', 'POST'])
def log_alumno():
    mensaje = None
    error = None
    resumen = {}
    registros = []

    # Lista de alumnos para el selector
    alumnos_lista = []
    for alumno in alumnos_col.find({
        "matricula": {"$nin": [None, "", "None", "Sin dato"]},
        "nombre": {"$nin": [None, "", "None", "Sin dato"]}
    }, {
        "_id": 0,
        "matricula": 1,
        "nombre": 1
    }).sort("matricula", -1):
        alumnos_lista.append({
            "matricula": alumno["matricula"],
            "nombre": alumno["nombre"].strip()
        })

    # Procesamiento del formulario
    if request.method == 'POST':
        matricula = request.form.get('alumno')
        if not matricula:
            error = "⚠ Debes seleccionar un alumno para generar el log."
        else:
            alumno = alumnos_col.find_one({"matricula": matricula})
            if alumno:
                # Registro de la acción en la colección logs
                logs_col.insert_one({
                    "matricula": matricula,
                    "nombre": alumno.get("nombre", ""),
                    "accion": "Consulta de perfil",
                    "fecha": datetime.now(),
                    "usuario": session.get("usuario", "sistema")
                })

                # Construcción del resumen
                resumen["datos"] = {
                    "matricula": alumno.get("matricula"),
                    "nombre": alumno.get("nombre"),
                    "apellido_paterno": alumno.get("apellido_paterno"),
                    "apellido_materno": alumno.get("apellido_materno"),
                    "correo": alumno.get("correo"),
                    "telefono": alumno.get("telefono"),
                    "fecha_registro": alumno.get("fecha_registro"),
                    "estado": alumno.get("estado"),
                    "activo": alumno.get("activo"),
                    "sin_horario": alumno.get("sin_horario"),
                }

                resumen["proyecto"] = alumno.get("proyecto")
                resumen["institucion"] = alumno.get("institucion")
                resumen["horario"] = alumno.get("horario", {})

                resumen["comentarios"] = list(comentarios_col.find(
                    {"matricula": matricula},
                    {"_id": 0, "comentario": 1, "fecha": 1, "usuario": 1}
                ).sort("fecha", -1))

                registros = list(logs_col.find(
                    {"matricula": matricula},
                    {"_id": 0, "accion": 1, "fecha": 1, "usuario": 1}
                ).sort("fecha", -1))
            else:
                error = "⚠ La matrícula no corresponde a ningún alumno registrado."

    return render_template("alumnos/log_alumno.html",
                           alumnos=alumnos_lista,
                           resumen=resumen,
                           registros=registros,
                           mensaje=mensaje,
                           error=error)

    
@app.route('/alumnos/eliminar', methods=['GET', 'POST'])
def eliminar_alumno():
    if request.method == 'POST':
        alumnos_col.delete_one({"matricula": request.form['alumno']})
        return redirect(url_for('eliminar_alumno'))
    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('alumnos/eliminar.html', alumnos=alumnos)

@app.route('/alumnos/consulta', methods=['GET'])
def consulta_alumnos():
    proyectos = list(proyectos_col.find({}, {"_id": 0, "id": 1, "nombre": 1}))
    instituciones = list(instituciones_col.find({}, {"_id": 0, "id": 1, "nombre": 1}))
    areas = ["Administrativa", "Técnica", "Social"]
    tipos_servicio = ["Prácticas", "Servicio social", "Residencia"]
    documentacion = ["Completa", "Incompleta", "No entregada"]
    estados = ["Activo", "Inactivo", "Finalizado"]

    return render_template('alumnos/consulta_alumnos.html',
                           proyectos=proyectos,
                           instituciones=instituciones,
                           areas=areas,
                           tipos_servicio=tipos_servicio,
                           documentacion=documentacion,
                           estados=estados)

@app.route('/api/alumnos/buscar', methods=['GET'])
def buscar_alumnos():
    nombre = request.args.get('nombre', '').strip()
    if not nombre:
        return jsonify([])

    alumnos = list(alumnos_col.find(
        {"nombre": {"$regex": nombre, "$options": "i"}},
        {"_id": 0, "matricula": 1, "nombre": 1, "apellido_paterno": 1, "apellido_materno": 1}
    ))
    return jsonify(alumnos)

@app.route('/api/alumnos/datos', methods=['GET'])
def obtener_datos_alumno():
    matricula = request.args.get('matricula', '').strip()
    try:
        matricula = int(matricula)
    except ValueError:
        return jsonify({})

    alumno = alumnos_col.find_one({"matricula": matricula}, {"_id": 0})
    return jsonify(alumno if alumno else {})

# ========== ASISTENCIA ==========
@app.route('/asistencia/consulta', methods=['GET', 'POST'])
def consulta_asistencia():
    if request.method == 'POST':
        alumno = request.form['alumno']
        fecha_inicio = request.form['fecha_inicio']
        fecha_termino = request.form['fecha_termino']
        print(f"Asistencia consultada para {alumno} entre {fecha_inicio} y {fecha_termino}")
        return redirect(url_for('consulta_asistencia'))

    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('asistencia/consulta.html', alumnos=alumnos)

@app.route('/asistencia/incidencias', methods=['GET', 'POST'])
def consulta_incidencias():
    if request.method == 'POST':
        alumno = request.form['alumno']
        fecha_inicio = request.form['fecha_inicio']
        fecha_termino = request.form['fecha_termino']
        print(f"Incidencias consultadas para {alumno} entre {fecha_inicio} y {fecha_termino}")
        return redirect(url_for('consulta_incidencias'))

    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('asistencia/incidencias.html', alumnos=alumnos)

# ========== DOCUMENTOS ==========
@app.route('/documentos/aceptacion', methods=['GET', 'POST'])
def carta_aceptacion():
    if request.method == 'POST':
        alumno = request.form['alumno']
        print(f"Generando carta de aceptación para el alumno {alumno}")
        return redirect(url_for('carta_aceptacion'))

    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('documentos/aceptacion.html', alumnos=alumnos)

@app.route('/documentos/terminacion', methods=['GET', 'POST'])
def carta_terminacion():
    if request.method == 'POST':
        alumno = request.form['alumno']
        print(f"Generando carta de terminación para el alumno {alumno}")
        return redirect(url_for('carta_terminacion'))

    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('documentos/terminacion.html', alumnos=alumnos)

@app.route('/documentos/horas', methods=['GET', 'POST'])
def constancia_horas():
    if request.method == 'POST':
        alumno = request.form['alumno']
        print(f"Generando constancia de horas para el alumno {alumno}")
        return redirect(url_for('constancia_horas'))

    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('documentos/horas.html', alumnos=alumnos)
# ========== INSTITUCIONES ==========
@app.route('/instituciones/registrar', methods=['GET', 'POST'])
def registrar_institucion():
    if request.method == 'POST':
        instituciones_col.insert_one({
            "nombre": request.form['nombre'],
            "responsable": request.form['responsable'],
            "cargo": request.form['cargo']
        })
        return redirect(url_for('registrar_institucion'))
    return render_template('instituciones/registrar.html')

@app.route('/instituciones/modificar', methods=['GET', 'POST'])
def modificar_institucion():
    if request.method == 'POST':
        institucion_id = request.form['institucion']
        cambios = {}
        if request.form['nuevo_nombre']:
            cambios['nombre'] = request.form['nuevo_nombre']
        if request.form['nuevo_responsable']:
            cambios['responsable'] = request.form['nuevo_responsable']
        if request.form['nuevo_cargo']:
            cambios['cargo'] = request.form['nuevo_cargo']
        if cambios:
            instituciones_col.update_one({"_id": institucion_id}, {"$set": cambios})
        return redirect(url_for('modificar_institucion'))

    instituciones = list(instituciones_col.find({}, {"_id": 1, "nombre": 1, "responsable": 1, "cargo": 1}))
    return render_template('instituciones/modificar.html', instituciones=instituciones)

@app.route('/instituciones/eliminar', methods=['GET', 'POST'])
def eliminar_institucion():
    if request.method == 'POST':
        institucion_id = request.form['institucion']
        instituciones_col.delete_one({"_id": institucion_id})
        return redirect(url_for('eliminar_institucion'))

    instituciones = list(instituciones_col.find({}, {"_id": 1, "nombre": 1}))
    return render_template('instituciones/eliminar.html', instituciones=instituciones)

@app.route('/instituciones/consulta')
def consulta_instituciones():
    instituciones = list(instituciones_col.find({}, {"_id": 0}))
    return render_template('instituciones/consulta.html', instituciones=instituciones)
# ========== ERROR GENÉRICO ==========
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('utils/error.html', error="Página no encontrada"), 404



# ========== INICIO ==========
if __name__ == '__main__':
    app.run(debug=True)