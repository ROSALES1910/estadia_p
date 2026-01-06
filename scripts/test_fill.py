from pathlib import Path
from utils.rtf_fill import fill_rtf_template

TEMPLATE = "templates/documentos/rtf/terminacion.rtf"

context = {
    "DIA": "15",
    "MES": "enero",
    "ANO": "2026",
    "RESPONSABLE": "Ing. María López",
    "CARGO": "Jefa de Vinculación",
    "NOMBRE": "Karla Martínez",
    "ESCOLARIDAD": "Licenciatura",
    "CARRERA": "Ingeniería en Sistemas",
    "CONTROL": "20210001",
    "TIPO": "Servicio Social",
    "HORAS": "480",
    "DIAINC": "01",
    "MESINC": "febrero",
    "ANOINC": "2026",
    "DIAFN": "31",
    "MESFN": "julio",
    "ANOFN": "2026",
}

output_dir = Path("documentos") / "generated"
output_dir.mkdir(parents=True, exist_ok=True)

out = fill_rtf_template(TEMPLATE, context, output_dir=str(output_dir))
print("RTF generado en:", out)