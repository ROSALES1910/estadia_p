from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

alumnos_col = db["alumnos"]
alumnos_password_col = db["alumnos_password"]
alumnos_servicio_col = db["alumnos_servicio"]
alumnos_servicio_new_col = db["alumnos_servicio_new"]
asistencia_col = db["asistencia"]
asistencia_new_col = db["asistencia_new"]
colegios_col = db["colegios"]
comentarios_col = db["comentarios"]
horarios_col = db["horarios"]
proyectos_col = db["proyectos"]
usuarios_col = db["usuarios"]
instituciones_col = db["instituciones"] 