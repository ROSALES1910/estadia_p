from flask import Flask, render_template, request, redirect, url_for
from models import (
    alumnos_col, alumnos_password_col, alumnos_servicio_col, alumnos_servicio_new_col,
    asistencia_col, asistencia_new_col, colegios_col, comentarios_col,
    horarios_col, proyectos_col, usuarios_col, instituciones_col
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# ========== DASHBOARD ==========
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard/index.html')

# ========== ALUMNOS ==========
@app.route('/alumnos/registrar', methods=['GET', 'POST'])
def registrar_alumno():
    if request.method == 'POST':
        alumnos_col.insert_one({
            "nombre": request.form['nombre'],
            "apellido_paterno": request.form['apellido_paterno'],
            "apellido_materno": request.form['apellido_materno'],
            "matricula": request.form['matricula'],
            "telefono": request.form['telefono'],
            "email": request.form['email'],
            "escolaridad": request.form['escolaridad'],
            "semestre": request.form['semestre'],
            "institucion": request.form['institucion'],
            "clave_institucion": request.form['clave_institucion'],
            "ocupacion": request.form['ocupacion'],
            "comentarios": request.form['comentarios'],
            "estado": "Activo"
        })
        return redirect(url_for('dashboard'))
    return render_template('alumnos/registrar.html')

@app.route('/alumnos/activar', methods=['GET', 'POST'])
def activar_alumno():
    if request.method == 'POST':
        alumnos_col.update_one(
            {"matricula": request.form['alumno']},
            {"$set": {"estado": request.form['estado']}}
        )
        return redirect(url_for('activar_alumno'))
    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('alumnos/activar.html', alumnos=alumnos)

@app.route('/alumnos/contrasena', methods=['GET', 'POST'])
def modificar_contrasena():
    if request.method == 'POST':
        alumnos_password_col.update_one(
            {"matricula": request.form['alumno']},
            {"$set": {"password": request.form['nueva_contrasena']}},
            upsert=True
        )
        return redirect(url_for('modificar_contrasena'))
    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('alumnos/modificar_contrasena.html', alumnos=alumnos)

@app.route('/alumnos/horario', methods=['GET', 'POST'])
def asignar_horario():
    if request.method == 'POST':
        horarios_col.update_one(
            {"matricula": request.form['alumno']},
            {"$set": {"horario": request.form['horario']}},
            upsert=True
        )
        return redirect(url_for('asignar_horario'))
    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('alumnos/asignar_horario.html', alumnos=alumnos)

@app.route('/alumnos/asignar_proyecto', methods=['GET', 'POST'])
def asignar_proyecto():
    if request.method == 'POST':
        alumno_matricula = request.form['alumno']
        proyecto_nombre = request.form['proyecto']
        descripcion = request.form['descripcion']

        alumnos_col.update_one(
            {"matricula": alumno_matricula},
            {"$set": {
                "proyecto": proyecto_nombre,
                "descripcion_proyecto": descripcion
            }}
        )
        return redirect(url_for('asignar_proyecto'))

    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    proyectos = list(proyectos_col.find({}, {"_id": 0, "id": 1, "nombre": 1}))
    return render_template('alumnos/asignar_proyecto.html', alumnos=alumnos, proyectos=proyectos)

@app.route('/alumnos/comentarios', methods=['GET', 'POST'])
def comentarios_alumno():
    if request.method == 'POST':
        comentarios_col.insert_one({
            "matricula": request.form['alumno'],
            "comentario": request.form['comentario']
        })
        return redirect(url_for('comentarios_alumno'))
    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('alumnos/comentarios.html', alumnos=alumnos)

@app.route('/alumnos/eliminar', methods=['GET', 'POST'])
def eliminar_alumno():
    if request.method == 'POST':
        alumnos_col.delete_one({"matricula": request.form['alumno']})
        return redirect(url_for('eliminar_alumno'))
    alumnos = list(alumnos_col.find({}, {"_id": 0, "matricula": 1, "nombre": 1}))
    return render_template('alumnos/eliminar.html', alumnos=alumnos)

@app.route('/alumnos/consulta', methods=['GET', 'POST'])
def consulta_alumnos():
    proyectos = list(proyectos_col.find({}, {"_id": 0, "id": 1, "nombre": 1}))
    instituciones = list(instituciones_col.find({}, {"_id": 0, "id": 1, "nombre": 1}))
    areas = ["Administrativa", "Técnica", "Social"]
    tipos_servicio = ["Prácticas", "Servicio social", "Residencia"]
    documentacion = ["Completa", "Incompleta", "No entregada"]
    estados = ["Activo", "Inactivo", "Finalizado"]

    if request.method == 'POST':
        filtros = {k: v for k, v in request.form.items() if v}
        alumnos = list(alumnos_col.find(filtros))
        return render_template('alumnos/consulta_resultados.html', alumnos=alumnos)

    return render_template('alumnos/consulta.html', proyectos=proyectos, instituciones=instituciones,
                           areas=areas, tipos_servicio=tipos_servicio,
                           documentacion=documentacion, estados=estados)
 
@app.route('/alumnos/modificar', methods=['GET', 'POST'])
def modificar_alumno():
    if request.method == 'POST':
        alumno_id = request.form['alumno']
        cambios = {
            "nombre": request.form['nombre'],
            "apellido_paterno": request.form['apellido_paterno'],
            "apellido_materno": request.form['apellido_materno'],
            "telefono": request.form['telefono'],
            "email": request.form['email'],
            "matricula": request.form['matricula'],
            "escolaridad": request.form['escolaridad'],
            "semestre": request.form['semestre'],
            "institucion": request.form['institucion'],
            "carrera": request.form['carrera'],
            "comentarios": request.form['comentarios']
        }
        cambios = {k: v for k, v in cambios.items() if v}
        if cambios:
            alumnos_col.update_one({"_id": ObjectId(alumno_id)}, {"$set": cambios})
        return redirect(url_for('modificar_alumno'))

    alumnos = list(alumnos_col.find({}, {"_id": 1, "nombre": 1}))
    return render_template('alumnos/modificar.html', alumnos=alumnos)

@app.route('/alumnos/desasignar_proyecto', methods=['GET', 'POST'])
def desasignar_proyecto():
    if request.method == 'POST':
        alumno_matricula = request.form['alumno']
        alumnos_col.update_one(
            {"matricula": alumno_matricula},
            {"$unset": {
                "proyecto": "",
                "descripcion_proyecto": ""
            }}
        )
        return redirect(url_for('desasignar_proyecto'))

    # Mostrar todos los alumnos que tengan el campo 'proyecto' definido
    alumnos = list(alumnos_col.find(
        {"proyecto": {"$exists": True}},
        {"_id": 0, "matricula": 1, "nombre": 1}
    ))
    return render_template('alumnos/desasignar_proyecto.html', alumnos=alumnos)
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