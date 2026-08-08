# -*- coding: utf-8 -*-
"""
Subtitulador_IA.py
------------------
Plugin para DaVinci Resolve (version GRATIS o Studio).
Se ejecuta desde:  Area de trabajo -> Secuencias de comandos -> Subtitulador_IA

Flujo:
  1. Renderiza el AUDIO DEL TIMELINE EDITADO a un WAV temporal
     (asi los subtitulos coinciden con tus cortes).
  2. Lo transcribe con faster-whisper (entorno externo).
  3. Guarda el .srt en la carpeta del plugin y abre esa carpeta.
  4. Arrastras el .srt al Media Pool y luego al timeline.
"""
import os
import sys
import json
import time
import glob
import subprocess


# --- 1. Conexion con Resolve ------------------------------------------------
def obtener_resolve():
    try:
        return resolve
    except NameError:
        pass
    try:
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")
    except Exception:
        api = os.environ.get(
            "RESOLVE_SCRIPT_API",
            r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
        sys.path.append(os.path.join(api, "Modules"))
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")


# --- 2. Configuracion -------------------------------------------------------
def cargar_config():
    ruta = os.path.join(os.environ.get("APPDATA", ""), "SubtituladorIA", "config.json")
    if not os.path.exists(ruta):
        raise RuntimeError("No encuentro la configuracion en:\n  " + ruta +
                           "\nEjecuta primero 'instalar.ps1'.")
    with open(ruta, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# --- 3a. Renderizar el AUDIO del timeline editado ---------------------------
def renderizar_audio_timeline(resolve, project, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    for viejo in glob.glob(os.path.join(carpeta, "audio_timeline*")):
        try:
            os.remove(viejo)
        except OSError:
            pass

    resolve.OpenPage("deliver")

    # Elegir formato WAV + PCM (audio puro)
    ok_fmt = False
    try:
        ok_fmt = project.SetCurrentRenderFormatAndCodec("wav", "LinearPCM")
    except Exception as e:
        print("[plugin] Aviso al fijar formato wav: " + str(e))
    print("[plugin] Formato wav/LinearPCM -> " + str(ok_fmt))

    try:
        project.SetRenderSettings({
            "TargetDir": carpeta,
            "CustomName": "audio_timeline",
            "SelectAllFrames": 1,
            "ExportVideo": False,
            "ExportAudio": True,
        })
    except Exception as e:
        print("[plugin] Aviso en SetRenderSettings: " + str(e))

    job = project.AddRenderJob()
    print("[plugin] AddRenderJob -> " + str(job))
    if not job:
        return None

    print("[plugin] Renderizando audio del timeline editado...")
    try:
        project.StartRendering([job])
    except Exception:
        project.StartRendering(job)
    while project.IsRenderingInProgress():
        time.sleep(1)

    resolve.OpenPage("edit")
    hits = glob.glob(os.path.join(carpeta, "audio_timeline*.wav"))
    if not hits:
        hits = glob.glob(os.path.join(carpeta, "audio_timeline*"))
    return hits[0] if hits else None


# --- 3b. Plan B: archivo original crudo del timeline ------------------------
def obtener_archivo_fuente(timeline):
    for tipo in ("video", "audio"):
        try:
            n = timeline.GetTrackCount(tipo)
        except Exception:
            n = 1
        for i in range(1, n + 1):
            try:
                items = timeline.GetItemListInTrack(tipo, i)
            except Exception:
                items = None
            if not items:
                continue
            for it in items:
                mp = it.GetMediaPoolItem()
                if not mp:
                    continue
                ruta = mp.GetClipProperty("File Path")
                if ruta and os.path.exists(ruta):
                    return ruta
    return None


# --- 4. Importar el SRT (intento automatico) --------------------------------
def importar_srt(media_pool, ruta_srt):
    try:
        items = media_pool.ImportMedia([ruta_srt])
        if items:
            ok = media_pool.AppendToTimeline(items)
            return bool(ok)
    except Exception as e:
        print("[plugin] Import automatico fallo: " + str(e))
    return False


# --- Programa principal -----------------------------------------------------
def main():
    resolve = obtener_resolve()
    if resolve is None:
        print("ERROR: No pude conectar con DaVinci Resolve.")
        return

    cfg = cargar_config()
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    if not project:
        print("ERROR: No hay proyecto abierto.")
        return
    timeline = project.GetCurrentTimeline()
    if not timeline:
        print("ERROR: No hay timeline activo. Abre uno en la pagina Edit.")
        return

    print("[plugin] Timeline: " + str(timeline.GetName()))

    temp = os.path.join(os.environ.get("TEMP", os.getcwd()), "SubtituladorIA")

    # 1) Intentar el audio EDITADO del timeline (sincronizacion correcta)
    audio = None
    try:
        audio = renderizar_audio_timeline(resolve, project, temp)
    except Exception as e:
        print("[plugin] El render de audio fallo: " + str(e))

    origen = "timeline editado"
    if audio and os.path.exists(audio):
        print("[plugin] Audio del timeline renderizado OK.")
    else:
        # 2) Plan B: archivo original crudo (ojo: ignora tus cortes)
        print("[plugin] No pude renderizar el audio del timeline.")
        print("[plugin] Uso el archivo ORIGINAL como respaldo (puede haber desfase).")
        audio = obtener_archivo_fuente(timeline)
        origen = "archivo original (sin edicion)"
        if not audio:
            print("ERROR: Tampoco encontre un archivo de audio/video en el timeline.")
            return

    print("[plugin] Fuente de audio: " + origen)
    print("[plugin] Archivo: " + audio)

    # Carpeta de salida clara: Documentos\Subtitulos IA (o Desktop de respaldo)
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    if not os.path.isdir(docs):
        docs = os.path.join(os.path.expanduser("~"), "Desktop")
    carpeta_srt = os.path.join(docs, "Subtitulos IA")
    os.makedirs(carpeta_srt, exist_ok=True)
    nombre_limpio = "".join(c if c.isalnum() or c in " -_" else "_"
                            for c in str(timeline.GetName())).strip()
    marca = time.strftime("%Y%m%d_%H%M%S")
    ruta_srt = os.path.join(carpeta_srt, nombre_limpio + "_" + marca + ".srt")

    cmd = [
        cfg["python_venv"],
        cfg["worker"],
        "--input", audio,
        "--output", ruta_srt,
        "--idioma", cfg.get("idioma", "es"),
        "--modelo", cfg.get("modelo", "small"),
        "--max_caracteres", str(cfg.get("max_caracteres", 42)),
    ]
    print("[plugin] Transcribiendo con Whisper...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.stdout:
        print(proc.stdout)
    if proc.returncode != 0:
        print("ERROR en la transcripcion:")
        print(proc.stderr)
        return
    if not os.path.exists(ruta_srt):
        print("ERROR: El worker no genero el archivo SRT.")
        return

    # Limpiar el audio temporal renderizado (NO el video original del usuario).
    try:
        if audio and os.path.dirname(audio) == temp and os.path.exists(audio):
            os.remove(audio)
            print("[plugin] Audio temporal eliminado.")
    except Exception:
        pass

    print("")
    print("[OK] Subtitulos guardados en:")
    print("     " + ruta_srt)

    media_pool = project.GetMediaPool()
    if importar_srt(media_pool, ruta_srt):
        print("[OK] Intente importarlos automaticamente. Si NO ves la pista de")
        print("     subtitulos arriba en el timeline, usa el metodo manual de abajo.")

    print("")
    print("PARA PONERLOS EN EL VIDEO:")
    print("  1. Se abrio la carpeta con el .srt.")
    print("  2. Arrastra el .srt a la ZONA DE MEDIOS (Media Pool).")
    print("  3. Desde el Media Pool, arrastralo al timeline -> crea la pista.")

    try:
        os.startfile(carpeta_srt)
    except Exception:
        pass


if __name__ == "__main__":
    main()
