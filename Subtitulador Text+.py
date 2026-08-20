# -*- coding: utf-8 -*-
"""
Subtitulador Text+  (EXPERIMENTAL)
----------------------------------
Igual que el Subtitulador_IA, pero en vez de una pista de subtitulos crea
un objeto Text+ por cada frase (texto totalmente editable/animable).

Se ejecuta desde:  Area de trabajo -> Secuencias de comandos

AVISO: insertar Text+ por API puede variar entre versiones. PRUEBALO EN UNA
COPIA DEL TIMELINE (clic derecho sobre el timeline en el Media Pool ->
Duplicar linea de tiempo) para no arriesgar tu edicion.
"""
import os
import sys
import json
import time
import glob
import subprocess


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


def cargar_config():
    ruta = os.path.join(os.environ.get("APPDATA", ""), "SubtituladorIA", "config.json")
    if not os.path.exists(ruta):
        raise RuntimeError("No encuentro la configuracion en:\n  " + ruta +
                           "\nEjecuta primero el instalador del Subtitulador.")
    with open(ruta, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def renderizar_audio_timeline(resolve, project, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    for viejo in glob.glob(os.path.join(carpeta, "audio_timeline*")):
        try:
            os.remove(viejo)
        except OSError:
            pass
    resolve.OpenPage("deliver")
    try:
        project.SetCurrentRenderFormatAndCodec("wav", "LinearPCM")
    except Exception:
        pass
    try:
        project.SetRenderSettings({
            "TargetDir": carpeta, "CustomName": "audio_timeline",
            "SelectAllFrames": 1, "ExportVideo": False, "ExportAudio": True,
        })
    except Exception:
        pass
    job = project.AddRenderJob()
    if not job:
        return None
    print("[plugin] Renderizando audio del timeline...")
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


# --- SRT -> Text+ -----------------------------------------------------------
def _fps(timeline, project):
    for obj in (timeline, project):
        try:
            v = obj.GetSetting("timelineFrameRate")
            if v:
                return float(v)
        except Exception:
            pass
    return 30.0


def _tc_a_seg(tc):
    # "HH:MM:SS,mmm" -> segundos
    hh, mm, resto = tc.strip().split(":")
    ss, ms = resto.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def _frames_a_tc(frame_abs, fps):
    f = int(round(fps))
    ff = int(frame_abs % f)
    secs = int(frame_abs // f)
    hh = secs // 3600
    mm = (secs % 3600) // 60
    ss = secs % 60
    return "%02d:%02d:%02d:%02d" % (hh, mm, ss, ff)


def parse_srt(ruta):
    with open(ruta, "r", encoding="utf-8-sig") as f:
        contenido = f.read()
    cues = []
    for bloque in contenido.replace("\r", "").split("\n\n"):
        lineas = [l for l in bloque.split("\n") if l.strip() != ""]
        if len(lineas) < 2:
            continue
        # localizar la linea de tiempos
        idx = 0
        if "-->" not in lineas[0] and len(lineas) >= 2 and "-->" in lineas[1]:
            idx = 1
        if "-->" not in lineas[idx]:
            continue
        ini, fin = lineas[idx].split("-->")
        texto = "\n".join(lineas[idx + 1:]).strip()
        if texto:
            cues.append((_tc_a_seg(ini), _tc_a_seg(fin), texto))
    return cues


def _set_texto_textplus(item, texto):
    try:
        comp = item.GetFusionCompByIndex(1)
    except Exception:
        comp = None
    if not comp:
        return False
    tool = None
    try:
        tool = comp.FindTool("Template")
    except Exception:
        tool = None
    if not tool:
        try:
            lst = comp.GetToolList(False, "TextPlus")
            if lst:
                tool = list(lst.values())[0]
        except Exception:
            pass
    if not tool:
        return False
    try:
        tool.SetInput("StyledText", texto)
        return True
    except Exception:
        return False


def crear_textplus(resolve, project, timeline, ruta_srt):
    resolve.OpenPage("edit")
    fps = _fps(timeline, project)
    inicio = timeline.GetStartFrame()
    cues = parse_srt(ruta_srt)
    print("[plugin] Frases a crear: " + str(len(cues)) + "  (fps=" + str(fps) + ")")

    metodo = None
    for nombre in ("InsertFusionTitleIntoTimeline", "InsertTitleIntoTimeline"):
        if getattr(timeline, nombre, None):
            metodo = nombre
            break
    if not metodo:
        print("[plugin] Esta version de Resolve no permite insertar Text+ por script.")
        return 0

    # PROTEGER el video/audio: bloquear todas las pistas existentes para que
    # la insercion de Text+ no las mueva. Luego creamos una pista nueva
    # (queda desbloqueada) donde caeran los Text+.
    bloqueadas = []
    for tt in ("video", "audio"):
        try:
            cnt = timeline.GetTrackCount(tt)
        except Exception:
            cnt = 0
        for i in range(1, cnt + 1):
            try:
                if timeline.SetTrackLock(tt, i, True):
                    bloqueadas.append((tt, i))
            except Exception:
                pass
    try:
        timeline.AddTrack("video")
    except Exception:
        pass

    n = 0
    for (ini_s, fin_s, texto) in cues:
        f_abs = inicio + int(round(ini_s * fps))
        try:
            timeline.SetCurrentTimecode(_frames_a_tc(f_abs, fps))
        except Exception:
            pass
        try:
            item = getattr(timeline, metodo)("Text+")
        except Exception as e:
            print("[plugin] Insertar Text+ fallo: " + str(e))
            item = None
        if not item:
            continue
        _set_texto_textplus(item, texto)
        n += 1

    # Desbloquear lo que habiamos bloqueado
    for (tt, i) in bloqueadas:
        try:
            timeline.SetTrackLock(tt, i, False)
        except Exception:
            pass
    return n


def main():
    resolve = obtener_resolve()
    if resolve is None:
        print("ERROR: No pude conectar con DaVinci Resolve.")
        return
    cfg = cargar_config()
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        print("ERROR: No hay proyecto abierto.")
        return
    timeline = project.GetCurrentTimeline()
    if not timeline:
        print("ERROR: No hay timeline activo.")
        return

    print("[plugin] Timeline: " + str(timeline.GetName()))
    print("[plugin] (Recomendado: trabajar sobre una COPIA del timeline)")

    temp = os.path.join(os.environ.get("TEMP", os.getcwd()), "SubtituladorIA")
    audio = None
    try:
        audio = renderizar_audio_timeline(resolve, project, temp)
    except Exception as e:
        print("[plugin] Render fallo: " + str(e))
    if not (audio and os.path.exists(audio)):
        audio = obtener_archivo_fuente(timeline)
        if not audio:
            print("ERROR: No encontre audio en el timeline.")
            return
    print("[plugin] Audio: " + audio)

    carpeta_srt = os.path.join(os.path.dirname(cfg["worker"]), "Subtitulos")
    os.makedirs(carpeta_srt, exist_ok=True)
    nombre = "".join(c if c.isalnum() or c in " -_" else "_" for c in str(timeline.GetName())).strip()
    ruta_srt = os.path.join(carpeta_srt, nombre + "_" + time.strftime("%Y%m%d_%H%M%S") + ".srt")

    cmd = [cfg["python_venv"], cfg["worker"], "--input", audio, "--output", ruta_srt,
           "--idioma", cfg.get("idioma", "es"), "--modelo", cfg.get("modelo", "small"),
           "--max_caracteres", str(cfg.get("max_caracteres", 42))]
    print("[plugin] Transcribiendo con Whisper...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.stdout:
        print(proc.stdout)
    if proc.returncode != 0 or not os.path.exists(ruta_srt):
        print("ERROR en la transcripcion:")
        print(proc.stderr)
        return

    try:
        if audio and os.path.dirname(audio) == temp and os.path.exists(audio):
            os.remove(audio)
    except Exception:
        pass

    n = crear_textplus(resolve, project, timeline, ruta_srt)
    print("")
    if n > 0:
        print("[OK] Cree " + str(n) + " Text+ en el timeline (texto editable).")
        print("     Ajusta estilo seleccionando un Text+ y abriendo el Inspector.")
        print("     Nota: revisa las DURACIONES; si se solapan o quedan largas,")
        print("     dime y lo afino (es la parte delicada de esta version).")
    else:
        print("[OK] No se pudieron crear Text+ en esta version de Resolve.")
        print("     Usa el otro plugin (Subtitulador_IA) que crea la pista de subtitulos.")
        print("     SRT: " + ruta_srt)


if __name__ == "__main__":
    main()
