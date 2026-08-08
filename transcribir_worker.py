# -*- coding: utf-8 -*-
"""
transcribir_worker.py
---------------------
Worker de transcripcion. Corre en el ENTORNO VIRTUAL (venv) que tiene
faster-whisper instalado, NO en el Python interno de DaVinci Resolve.

Recibe un archivo de audio/video y escribe un archivo .srt con los
subtitulos y sus tiempos.

Uso:
    python transcribir_worker.py --input audio.wav --output subs.srt \
           --idioma es --modelo small
"""
import argparse
import sys

# Windows: la salida por defecto es cp1252 y no soporta emojis/acentos raros.
# Forzamos UTF-8 para que no reviente al imprimir nombres con emojis.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def formato_tiempo(segundos: float) -> str:
    """Convierte segundos (float) al formato de tiempo SRT: HH:MM:SS,mmm"""
    if segundos < 0:
        segundos = 0
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    seg = int(segundos % 60)
    milis = int(round((segundos - int(segundos)) * 1000))
    if milis == 1000:  # redondeo hacia arriba
        milis = 0
        seg += 1
    return f"{horas:02d}:{minutos:02d}:{seg:02d},{milis:03d}"


def dividir_texto(texto: str, max_caracteres: int = 42) -> str:
    """
    Divide un texto largo en un maximo de 2 lineas para que el subtitulo
    sea comodo de leer. Si cabe en una linea, lo deja igual.
    """
    texto = texto.strip()
    if len(texto) <= max_caracteres:
        return texto
    palabras = texto.split()
    linea1, linea2 = [], []
    largo1 = 0
    for i, p in enumerate(palabras):
        if largo1 + len(p) + 1 <= max_caracteres and not linea2:
            linea1.append(p)
            largo1 += len(p) + 1
        else:
            linea2.append(p)
    if linea2:
        return " ".join(linea1) + "\n" + " ".join(linea2)
    return " ".join(linea1)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio a SRT con faster-whisper")
    parser.add_argument("--input", required=True, help="Ruta del audio/video de entrada")
    parser.add_argument("--output", required=True, help="Ruta del .srt de salida")
    parser.add_argument("--idioma", default="es", help="Idioma (es, en, auto)")
    parser.add_argument("--modelo", default="small",
                        help="tiny, base, small, medium, large-v3")
    parser.add_argument("--max_caracteres", type=int, default=42,
                        help="Maximo de caracteres por linea de subtitulo")
    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: faster-whisper no esta instalado en este entorno.", file=sys.stderr)
        print("Ejecuta primero instalar.ps1", file=sys.stderr)
        sys.exit(2)

    idioma = None if args.idioma.lower() == "auto" else args.idioma

    print(f"[worker] Cargando modelo '{args.modelo}' (la primera vez se descarga)...",
          flush=True)
    # compute_type='int8' funciona bien en CPU. Con GPU NVIDIA usa 'float16'.
    modelo = WhisperModel(args.modelo, device="auto", compute_type="int8")

    print(f"[worker] Transcribiendo: {args.input}", flush=True)
    segmentos, info = modelo.transcribe(
        args.input,
        language=idioma,
        vad_filter=True,               # filtra silencios -> mejores tiempos
        beam_size=5,
    )
    print(f"[worker] Idioma detectado: {info.language} "
          f"(probabilidad {info.language_probability:.2f})", flush=True)

    lineas_srt = []
    n = 0
    for seg in segmentos:
        texto = seg.text.strip()
        if not texto:
            continue
        n += 1
        lineas_srt.append(str(n))
        lineas_srt.append(f"{formato_tiempo(seg.start)} --> {formato_tiempo(seg.end)}")
        lineas_srt.append(dividir_texto(texto, args.max_caracteres))
        lineas_srt.append("")  # linea en blanco separadora
        print(f"[worker] {n}: {texto}", flush=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas_srt))

    print(f"[worker] Listo. {n} subtitulos escritos en: {args.output}", flush=True)


if __name__ == "__main__":
    main()
