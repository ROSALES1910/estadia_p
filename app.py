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

from bson import ObjectId
from datetime import datetime


# ========== REGISTRAR ALUMNO ==========

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

    mensaje = request.args.get("mensaje")
    return render_template("alumnos/registrar_nuevo_alumno.html", mensaje=mensaje, datos={})


# ========== ACTIVAR / INACTIVAR ALUMNO ==========

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
    return render_template('alumnos/activar_e_inactivar_alumno.html', alumnos=alumnos, mensaje=mensaje, error=error)


# ========== MODIFICAR ALUMNO (UNIFICADO) ==========

@app.route('/alumnos/modificar', methods=['GET', 'POST'])
def modificar_datos_alumno():
    mensaje = None
    error = None
    alumno_seleccionado = None

    # 1. Recibir matricula desde GET
    matricula = request.args.get('matricula')

    # 2. Si viene matricula, precargar alumno
    if request.method == 'GET' and matricula:
        alumno_seleccionado = alumnos_col.find_one({"matricula": matricula})

    if request.method == 'POST':
        alumno_id = request.form.get('alumno')

        if not alumno_id:
            error = "Debes seleccionar un alumno."
        else:
            # 3. Si solo seleccionó alumno, mostrarlo
            if "nombre" not in request.form:
                try:
                    alumno_seleccionado = alumnos_col.find_one({"_id": ObjectId(alumno_id)})
                except Exception as e:
                    error = f"No se pudo obtener la información del alumno: {str(e)}"
            else:
                # 4. Guardar cambios
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
                    alumnos_col.update_one({"_id": ObjectId(alumno_id)}, {"$set": cambios})
                    mensaje = "Datos del alumno actualizados correctamente."
                    alumno_seleccionado = None
                except Exception as e:
                    error = f"Ocurrió un error al actualizar: {str(e)}"

    alumnos = list(alumnos_col.find({}, {"_id": 1, "nombre": 1, "matricula": 1}))
    return render_template(
        'alumnos/modificar_datos_alumno.html',
        alumnos=alumnos,
        alumno_seleccionado=alumno_seleccionado,
        mensaje=mensaje,
        error=error
    )


# ========== REDIRECCIÓN LEGACY ==========

@app.route('/alumnos/modificar_datos_alumno')
def redireccion_modificar_legacy():
    matricula = request.args.get('matricula')
    return redirect(url_for('modificar_datos_alumno', matricula=matricula))


# ========== MODIFICAR CONTRASEÑA ==========

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
            alumnos_col.update_one({"matricula": alumno_matricula}, {"$set": {"contrasena": nueva_contrasena}})
            return redirect(url_for('modificar_contrasena', mensaje="Contraseña actualizada correctamente."))
        except Exception as e:
            return redirect(url_for('modificar_contrasena', error=f"Ocurrió un error al actualizar la contraseña: {str(e)}"))

    alumnos = list(alumnos_col.find({}, {"matricula": 1, "nombre": 1}))
    return render_template('alumnos/modificar_contrasena.html', alumnos=alumnos, mensaje=mensaje, error=error)


# ========== ASIGNAR PROYECTO ==========

@app.route('/alumnos/asignar-proyecto', methods=['GET', 'POST'])
def asignar_proyecto():
    mensaje = None
    error = None
    alumno_seleccionado = None

    # 1. Recibir matricula desde GET
    matricula = request.args.get('matricula')

    # 2. Si viene matricula, precargar alumno
    if request.method == 'GET' and matricula:
        alumno_seleccionado = alumnos_col.find_one({"matricula": matricula})

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
        alumno_seleccionado=alumno_seleccionado,
        mensaje=mensaje,
        error=error
    )


# ========== REDIRECCIÓN LEGACY ==========

@app.route('/alumnos/asignar_cambiar_proyecto')
def redireccion_asignar_legacy():
    matricula = request.args.get('matricula')
    return redirect(url_for('asignar_proyecto', matricula=matricula))

# ========== DESASIGNAR PROYECTO ==========

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
                    {"$unset": {"proyecto": "", "descripcion_proyecto": "", "id_proyecto": ""}}
                )
                mensaje = f"Proyecto desasignado correctamente del alumno {alumno_matricula}."
            except Exception as e:
                error = f"Ocurrió un error al desasignar el proyecto: {str(e)}"

    alumnos = list(alumnos_col.find({"proyecto": {"$exists": True}}, {"matricula": 1, "nombre": 1}))
    return render_template('alumnos/desasignar_proyecto.html', alumnos=alumnos, mensaje=mensaje, error=error)


# ========== ASIGNAR HORARIO ==========

@app.route('/alumnos/asignar_horario', methods=['GET', 'POST'])
def asignar_horario():
    mensaje = request.args.get('mensaje')
    id_alumno = request.args.get('id_alumno')
    matricula = request.args.get('matricula')
    seleccionado = None
    horario = {}

    if not id_alumno and matricula:
        seleccionado = alumnos_col.find_one({"matricula": matricula})
        if seleccionado:
            id_alumno = seleccionado.get("id_alumno")

    if request.method == 'POST':
        id_alumno = request.form.get('id_alumno')
        sin_horario = 'sin_horario' in request.form

        horario = {
            dia: [
                request.form.get(f'{dia}_inicio'),
                request.form.get(f'{dia}_fin')
            ]
            for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
        }

        alumnos_col.update_one(
            {"id_alumno": id_alumno},
            {"$set": {"horario": horario, "sin_horario": sin_horario}}
        )

        return redirect(url_for(
            'asignar_horario',
            id_alumno=id_alumno,
            mensaje='Horario actualizado correctamente'
        ))

    alumnos = list(alumnos_col.find(
        {},
        {"id_alumno": 1, "nombre": 1, "apellido_paterno": 1, "apellido_materno": 1}
    ))

    if id_alumno and not seleccionado:
        seleccionado = alumnos_col.find_one({"id_alumno": id_alumno})

    if seleccionado:
        horario = seleccionado.get("horario", {})
    elif id_alumno:
        mensaje = f"No se encontró el alumno con ID {id_alumno}."

    return render_template(
        'alumnos/asignar_horario.html',
        alumnos=alumnos,
        seleccionado=seleccionado,
        horario=horario,
        mensaje=mensaje
    )


# ========== REDIRECCIÓN LEGACY ==========

@app.route('/alumnos/asignar_cambiar_horario')
def redireccion_horario_legacy():
    matricula = request.args.get('matricula')
    return redirect(url_for('asignar_horario', matricula=matricula))


# ========== REDIRECCIÓN ALIAS EXTRA ==========

@app.route('/alumnos/asignar-horario')
def redireccion_horario_guion_medio():
    matricula = request.args.get('matricula')
    return redirect(url_for('asignar_horario', matricula=matricula))

# ========== VER COMENTARIOS ==========

@app.route('/alumnos/comentarios', methods=['GET', 'POST'])
def comentarios_alumno():
    mensaje = None
    error = None
    matricula = request.args.get('matricula')
    id_alumno = request.args.get('id_alumno')
    seleccionado = None
    comentarios = []

    if not id_alumno and matricula:
        seleccionado = alumnos_col.find_one({"matricula": matricula})
        if seleccionado:
            id_alumno = seleccionado.get("id_alumno")

    if request.method == 'POST':
        id_alumno = request.form.get('id_alumno')
        nuevo_comentario = request.form.get('comentario', '').strip()

        if not id_alumno:
            error = "Debes seleccionar un alumno."
        elif not nuevo_comentario:
            error = "El comentario no puede estar vacío."
        else:
            alumnos_col.update_one(
                {"id_alumno": id_alumno},
                {"$push": {"comentarios_historial": {
                    "comentario": nuevo_comentario,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
                }}}
            )
            return redirect(url_for(
                'comentarios_alumno',
                id_alumno=id_alumno,
                mensaje="Comentario agregado correctamente"
            ))

    alumnos = list(alumnos_col.find(
        {},
        {"id_alumno": 1, "nombre": 1, "apellido_paterno": 1, "apellido_materno": 1}
    ))

    if id_alumno and not seleccionado:
        seleccionado = alumnos_col.find_one({"id_alumno": id_alumno})

    if seleccionado:
        comentarios = seleccionado.get("comentarios_historial", [])

    return render_template(
        'alumnos/comentarios_alumno.html',
        alumnos=alumnos,
        seleccionado=seleccionado,
        comentarios=comentarios,
        mensaje=mensaje,
        error=error
    )


# ========== REDIRECCIÓN LEGACY ==========

@app.route('/alumnos/ver_comentarios')
def redireccion_comentarios_legacy():
    matricula = request.args.get('matricula')
    return redirect(url_for('comentarios_alumno', matricula=matricula))


# ========== REDIRECCIÓN ALIAS EXTRA ==========

@app.route('/alumnos/comentarios_alumno')
def redireccion_comentarios_alias():
    matricula = request.args.get('matricula')
    return redirect(url_for('comentarios_alumno', matricula=matricula))

# ========== VER LOG ==========

@app.route('/alumnos/log', methods=['GET'])
def ver_log_alumno():
    mensaje = None
    error = None
    matricula = request.args.get('matricula')
    id_alumno = request.args.get('id_alumno')
    seleccionado = None
    log = []

    if not id_alumno and matricula:
        seleccionado = alumnos_col.find_one({"matricula": matricula})
        if seleccionado:
            id_alumno = seleccionado.get("id_alumno")

    alumnos = list(alumnos_col.find(
        {},
        {"id_alumno": 1, "nombre": 1, "apellido_paterno": 1, "apellido_materno": 1}
    ))

    if id_alumno and not seleccionado:
        seleccionado = alumnos_col.find_one({"id_alumno": id_alumno})

    if seleccionado:
        log = seleccionado.get("log_historial", [])

    return render_template(
        'alumnos/log_alumno.html',
        alumnos=alumnos,
        seleccionado=seleccionado,
        log=log,
        mensaje=mensaje,
        error=error
    )


# ========== REDIRECCIÓN LEGACY ==========

@app.route('/alumnos/ver_log')
def redireccion_log_legacy():
    matricula = request.args.get('matricula')
    return redirect(url_for('ver_log_alumno', matricula=matricula))


# ========== REDIRECCIÓN ALIAS EXTRA ==========

@app.route('/alumnos/log_alumno')
def redireccion_log_alias():
    matricula = request.args.get('matricula')
    return redirect(url_for('ver_log_alumno', matricula=matricula))

# ========== ELIMINAR ALUMNO ==========

@app.route('/alumnos/eliminar', methods=['GET', 'POST'])
def eliminar_alumno():
    mensaje = None
    error = None
    matricula = request.args.get('matricula')
    id_alumno = request.args.get('id_alumno')
    seleccionado = None

    if not id_alumno and matricula:
        seleccionado = alumnos_col.find_one({"matricula": matricula})
        if seleccionado:
            id_alumno = seleccionado.get("id_alumno")

    if request.method == 'POST':
        id_alumno = request.form.get('id_alumno')

        if not id_alumno:
            error = "Debes seleccionar un alumno."
        else:
            alumno = alumnos_col.find_one({"id_alumno": id_alumno})

            if not alumno:
                error = "El alumno no existe."
            else:
                alumnos_col.delete_one({"id_alumno": id_alumno})

                return redirect(url_for(
                    'eliminar_alumno',
                    mensaje="Alumno eliminado correctamente"
                ))

    alumnos = list(alumnos_col.find(
        {},
        {"id_alumno": 1, "nombre": 1, "apellido_paterno": 1, "apellido_materno": 1}
    ))

    if id_alumno and not seleccionado:
        seleccionado = alumnos_col.find_one({"id_alumno": id_alumno})

    return render_template(
        'alumnos/eliminar_alumno.html',
        alumnos=alumnos,
        seleccionado=seleccionado,
        mensaje=mensaje,
        error=error
    )


# ========== REDIRECCIÓN LEGACY ==========

@app.route('/alumnos/eliminar_alumno')
def redireccion_eliminar_legacy():
    matricula = request.args.get('matricula')
    return redirect(url_for('eliminar_alumno', matricula=matricula))

# ========== CONSULTA DE ALUMNOS ==========

@app.route('/alumnos/consulta', methods=['GET'])
def consulta_alumnos():
    return render_template('alumnos/consulta_alumnos.html')


# ========== API: BUSCAR ALUMNOS ==========

@app.route('/api/alumnos/buscar', methods=['GET'])
def buscar_alumnos():
    termino = request.args.get('q', '').strip()

    if not termino:
        return jsonify([])

    alumnos = list(alumnos_col.find(
        {
            "$or": [
                {"nombre": {"$regex": termino, "$options": "i"}},
                {"apellido_paterno": {"$regex": termino, "$options": "i"}},
                {"apellido_materno": {"$regex": termino, "$options": "i"}},
                {"matricula": {"$regex": termino, "$options": "i"}}
            ]
        },
        {"_id": 0, "matricula": 1, "nombre": 1, "apellido_paterno": 1, "apellido_materno": 1}
    ))

    return jsonify(alumnos)


# ========== API: OBTENER DATOS DEL ALUMNO ==========

@app.route('/api/alumnos/datos', methods=['GET'])
def obtener_datos_alumno():
    matricula = request.args.get('matricula', '').strip()

    if not matricula:
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

# ========== ALTA DE PROYECTOS ==========

@app.route('/proyectos/registrar', methods=['GET', 'POST'])
def registrar_proyecto():
    mensaje = request.args.get('mensaje')
    error = None

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        area = request.form.get('area')
        alumnos_requeridos = request.form.get('alumnos_requeridos')
        descripcion = request.form.get('descripcion')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        responsable = request.form.get('responsable')

        if not titulo or not area or not alumnos_requeridos or not descripcion or not fecha_inicio or not responsable:
            error = "Todos los campos obligatorios deben ser llenados."
        else:
            try:
                alumnos_requeridos = int(alumnos_requeridos)
            except:
                error = "El número de alumnos debe ser un entero."

        if not error:
            nuevo_proyecto = {
                "titulo": titulo,
                "area": area,
                "alumnos_requeridos": alumnos_requeridos,
                "descripcion": descripcion,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "responsable": responsable,
                "estado": "pendiente"
            }

            proyectos_col.insert_one(nuevo_proyecto)

            return redirect(url_for(
                'registrar_proyecto',
                mensaje="Proyecto registrado correctamente"
            ))

    return render_template(
        'proyectos/registrar.html',
        mensaje=mensaje,
        error=error
    )


# ========== MODIFICAR PROYECTOS ==========

@app.route('/proyectos/modificar', methods=['GET', 'POST'])
def modificar_proyecto():
    mensaje = request.args.get('mensaje')
    error = None

    proyectos = list(proyectos_col.find({}, {"_id": 1, "titulo": 1}))

    proyecto_id_get = request.args.get("id")
    proyecto_seleccionado = None

    if proyecto_id_get:
        try:
            p = proyectos_col.find_one({"_id": ObjectId(proyecto_id_get)})
            if p:
                proyecto_seleccionado = {
                    "_id": str(p["_id"]),
                    "titulo": p.get("titulo", ""),
                    "area": p.get("area", ""),
                    "alumnos_requeridos": p.get("alumnos_requeridos", ""),
                    "descripcion": p.get("descripcion", ""),
                    "fecha_inicio": p.get("fecha_inicio", ""),
                    "fecha_fin": p.get("fecha_fin", ""),
                    "responsable": p.get("responsable", "")
                }
        except:
            proyecto_seleccionado = None

    if request.method == 'POST':
        proyecto_id = request.form.get('proyecto')
        nuevo_nombre = request.form.get('nuevo_nombre')
        nueva_area = request.form.get('nueva_area')
        nuevos_alumnos = request.form.get('nuevos_alumnos')
        nueva_descripcion = request.form.get('nueva_descripcion')
        nueva_fecha_inicio = request.form.get('nueva_fecha_inicio')
        nueva_fecha_fin = request.form.get('nueva_fecha_fin')
        nuevo_responsable = request.form.get('nuevo_responsable')

        if not proyecto_id:
            error = "Debes seleccionar un proyecto."
        else:
            cambios = {}

            if nuevo_nombre:
                cambios["titulo"] = nuevo_nombre

            if nueva_area:
                cambios["area"] = nueva_area

            if nuevos_alumnos:
                try:
                    cambios["alumnos_requeridos"] = int(nuevos_alumnos)
                except:
                    error = "El número de alumnos debe ser un entero."

            if nueva_descripcion:
                cambios["descripcion"] = nueva_descripcion

            if nueva_fecha_inicio:
                cambios["fecha_inicio"] = nueva_fecha_inicio

            if nueva_fecha_fin:
                cambios["fecha_fin"] = nueva_fecha_fin

            if nuevo_responsable:
                cambios["responsable"] = nuevo_responsable

            if cambios and not error:
                proyectos_col.update_one(
                    {"_id": ObjectId(proyecto_id)},
                    {"$set": cambios}
                )

                return redirect(url_for(
                    'modificar_proyecto',
                    mensaje="Proyecto modificado correctamente"
                ))

            elif not error:
                error = "No se ingresaron cambios."

    return render_template(
        'proyectos/modificar.html',
        proyectos=[{
            "id": str(p["_id"]),
            "nombre": p["titulo"]
        } for p in proyectos],
        proyecto=proyecto_seleccionado,
        mensaje=mensaje,
        error=error
    )


# ========== TERMINAR PROYECTOS ==========

@app.route('/proyectos/terminar', methods=['GET', 'POST'])
def terminar_proyecto():
    mensaje = request.args.get('mensaje')
    error = None

    # Lista de proyectos NO finalizados
    proyectos = list(proyectos_col.find(
        {"estado": {"$ne": "finalizado"}},
        {"_id": 1, "titulo": 1}
    ))

    # ID seleccionado desde el SELECT
    proyecto_id_get = request.args.get("proyecto")
    proyecto_seleccionado = None

    # Si el usuario seleccionó un proyecto, cargar detalles
    if proyecto_id_get:
        try:
            p = proyectos_col.find_one({"_id": ObjectId(proyecto_id_get)})
            if p:
                proyecto_seleccionado = {
                    "_id": str(p["_id"]),
                    "titulo": p.get("titulo", ""),
                    "area": p.get("area", ""),
                    "estado": p.get("estado", ""),
                    "responsable": p.get("responsable", ""),
                    "descripcion": p.get("descripcion", ""),
                    "fecha_inicio": p.get("fecha_inicio", ""),
                    "fecha_fin": p.get("fecha_fin", ""),
                    "alumnos_requeridos": p.get("alumnos_requeridos", 0),
                    "alumnos_asignados": len(p.get("alumnos", []))
                }
        except:
            proyecto_seleccionado = None

    # POST → Terminar proyecto
    if request.method == 'POST':
        proyecto_id = request.form.get('proyecto')

        if not proyecto_id:
            error = "Debes seleccionar un proyecto antes de marcarlo como terminado."
        else:
            proyectos_col.update_one(
                {"_id": ObjectId(proyecto_id)},
                {"$set": {"estado": "finalizado"}}
            )

            return redirect(url_for(
                'terminar_proyecto',
                mensaje="Proyecto marcado como terminado correctamente"
            ))

    return render_template(
        'proyectos/terminar.html',
        proyectos=[{
            "id": str(p["_id"]),
            "nombre": p["titulo"]
        } for p in proyectos],
        proyecto=proyecto_seleccionado,
        mensaje=mensaje,
        error=error
    )


# ========== CONSULTA DE PROYECTOS ==========

@app.route('/proyectos/consulta', methods=['GET'])
def consulta_proyectos():
    filtro_nombre = request.args.get('nombre_busqueda', '').strip()
    filtro_area = request.args.get('area', '').strip()
    filtro_estado = request.args.get('estado', '').strip()

    query = {}

    if filtro_nombre:
        query["titulo"] = {"$regex": filtro_nombre, "$options": "i"}

    if filtro_area:
        query["area"] = filtro_area

    if filtro_estado:
        query["estado"] = filtro_estado

    proyectos_cursor = proyectos_col.find(query)

    proyectos = [{
        "id": str(p["_id"]),
        "nombre": p.get("titulo", ""),
        "area": p.get("area", "No especificada"),
        "estado": p.get("estado", "Sin estado"),
        "alumnos_requeridos": p.get("alumnos_requeridos", 0),
        "alumnos_asignados": len(p.get("alumnos", [])),
        "descripcion": p.get("descripcion", ""),
        "fecha_inicio": p.get("fecha_inicio", ""),
        "fecha_fin": p.get("fecha_fin", ""),
        "responsable": p.get("responsable", "")
    } for p in proyectos_cursor]

    areas = sorted([a for a in proyectos_col.distinct("area") if a])
    estados = sorted([e for e in proyectos_col.distinct("estado") if e])

    return render_template(
        'proyectos/consulta.html',
        proyectos_resultados=proyectos,
        areas=areas,
        estados=estados
    )

# ========== SUGERENCIAS DE PROYECTOS ==========

@app.route('/proyectos/sugerencias')
def sugerencias_proyectos():
    texto = request.args.get('texto', '').strip()
    area = request.args.get('area', '').strip()
    estado = request.args.get('estado', '').strip()

    query = {}

    if texto:
        query["titulo"] = {"$regex": texto, "$options": "i"}

    if area:
        query["area"] = area

    if estado:
        query["estado"] = estado

    resultados = proyectos_col.find(query).limit(20)

    sugerencias = [{
        "id": str(p["_id"]),
        "nombre": p.get("titulo", ""),
        "area": p.get("area", "No especificada"),
        "estado": p.get("estado", "Sin estado")
    } for p in resultados]

    return jsonify(sugerencias)


# ========== DETALLES DE PROYECTO ==========

@app.route('/proyectos/detalles/<id>')
def detalles_proyecto(id):
    proyecto = proyectos_col.find_one({"_id": ObjectId(id)})

    if not proyecto:
        return jsonify({"error": "Proyecto no encontrado"}), 404

    detalles = {
        "id": str(proyecto["_id"]),
        "titulo": proyecto.get("titulo", ""),
        "descripcion": proyecto.get("descripcion", ""),
        "area": proyecto.get("area", "No especificada"),
        "estado": proyecto.get("estado", "Sin estado"),
        "fecha_inicio": proyecto.get("fecha_inicio", ""),
        "fecha_fin": proyecto.get("fecha_fin", ""),
        "responsable": proyecto.get("responsable", ""),
        "alumnos": proyecto.get("alumnos_requeridos", 0),
    }

    return jsonify(detalles)

if __name__ == "__main__":
    app.run(debug=True)