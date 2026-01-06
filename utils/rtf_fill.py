from pathlib import Path
import re

PLACEHOLDER_PATTERN_HASH = re.compile(r"#\*([A-Za-z0-9_]+)\*#")

def fill_rtf_template(template_path: str, context: dict, output_dir: str = "documentos/generated") -> str:
    """
    Lee una plantilla .rtf, reemplaza placeholders del tipo #*KEY*# y {{KEY}} por los valores
    en `context`, guarda el .rtf resultante en `output_dir` y devuelve la ruta al archivo generado.
    """
    tpl = Path(template_path)
    if not tpl.exists():
        raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")

    # Leer contenido (ignorando errores de codificación si los hay)
    text = tpl.read_text(encoding="utf-8", errors="ignore")

    # Reemplazo para formato #*KEY*#
    def repl_hash(match):
        key = match.group(1)
        return str(context.get(key, ""))

    text = PLACEHOLDER_PATTERN_HASH.sub(repl_hash, text)

    # Reemplazo para formato {{KEY}}
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", str(value))

    # Preparar carpeta de salida
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Guardar con sufijo _filled.rtf
    out_path = outdir / (tpl.stem + "_filled.rtf")
    out_path.write_text(text, encoding="utf-8")
    return str(out_path)