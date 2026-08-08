# Subtitulador IA para DaVinci Resolve

Genera **subtítulos automáticos en español** a partir del audio de tus videos,
directamente dentro de **DaVinci Resolve** (versión gratis o Studio).

La transcripción usa inteligencia artificial (**Whisper**) que corre **en tu
propio PC**: es gratis, privado y funciona sin conexión (salvo la primera vez,
para descargar el modelo). No requiere cuentas, ni claves, ni suscripciones.

---

## Características

- Detecta el audio del **timeline editado** y lo convierte a texto.
- Genera un archivo de subtítulos `.srt` con tiempos sincronizados.
- Se integra en el menú de DaVinci: **Área de trabajo → Secuencias de comandos**.
- Edición total de **texto, tipografía, color y posición** con las herramientas
  nativas de Resolve.
- 100% local: tus videos no salen de tu computadora.

---

## Instalación fácil (recomendada)

La versión lista para usar (con todo incluido, no necesitas instalar nada más):

1. **Descarga el paquete:** [Descargar Subtitulador IA (Windows)](https://drive.google.com/uc?export=download&id=1vusWGEnYlYRtgbeYyYKmU9NZ-wckmkc9)
2. Descomprime la carpeta en un lugar fijo de tu PC.
3. Doble clic en **`Instalar.bat`**.
4. Abre DaVinci Resolve → **Área de trabajo → Secuencias de comandos → Subtitulador_IA**.

Guía detallada paso a paso: ver **`LEEME.txt`**.

---

## Instalación desde el código (avanzado)

Si prefieres construirlo tú mismo con tu propio Python:

**Requisitos:** Windows 10/11, Python 3.13 (con *Add to PATH*), DaVinci Resolve.

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

El script crea un entorno con `faster-whisper`, guarda la configuración y copia
el plugin en la carpeta de scripts de DaVinci Resolve.

---

## Configuración

Archivo: `%APPDATA%\SubtituladorIA\config.json`

| Opción           | Valores                                   | Descripción                          |
|------------------|-------------------------------------------|--------------------------------------|
| `idioma`         | `es`, `en`, `auto`                        | Idioma del audio                     |
| `modelo`         | `tiny`, `base`, `small`, `medium`, `large-v3` | Precisión vs. velocidad          |
| `max_caracteres` | número (ej. `42`)                         | Máximo de caracteres por línea       |

---

## Estructura del proyecto

| Archivo               | Descripción                                             |
|-----------------------|---------------------------------------------------------|
| `Subtitulador_IA.py`  | Plugin que corre dentro de DaVinci Resolve              |
| `transcribir_worker.py` | Motor de transcripción (Whisper)                      |
| `Instalar.bat`        | Instalador de un clic (para el paquete con todo incluido) |
| `instalar.ps1`        | Instalador desde código fuente                          |
| `LEEME.txt`           | Guía de instalación y uso para el usuario final         |

---

## Licencia

MIT. Ver [LICENSE](LICENSE).
