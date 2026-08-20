# Subtitulador Text+ para DaVinci Resolve

Genera subtitulos automaticos en espanol a partir del audio de tus videos y los
crea como objetos **Text+** dentro de **DaVinci Resolve** (version gratis o
Studio), para que puedas editar libremente fuente, tamano, color, contorno y
animacion con las herramientas nativas.

La transcripcion usa inteligencia artificial (**Whisper**) que corre **en tu
propio PC**: es gratis, privado y funciona sin conexion (salvo la primera vez,
para descargar el modelo). No requiere cuentas, ni claves, ni suscripciones.

---

## Caracteristicas

- Detecta el audio del **timeline editado** y lo convierte a texto.
- Crea un **Text+** por cada frase, en su momento correcto.
- Texto totalmente editable con el Inspector y Fusion.
- 100% local: tus videos no salen de tu computadora.

---

## Instalacion facil (recomendada)

La version lista para usar (con todo incluido, no necesitas instalar nada mas):

1. **Descarga el paquete:** [Descargar Subtitulador Text+ (Windows)](https://drive.usercontent.google.com/download?id=1_Jtj0ssiwSSWmr3o9ibgjafAQSa_IhUp&export=download&confirm=t)
2. Descomprime la carpeta en un lugar fijo de tu PC.
3. Doble clic en **`Instalar.bat`**.
4. Cierra y vuelve a abrir DaVinci Resolve.

Guia detallada paso a paso: ver **`LEEME.txt`**.

---

## Como usar

1. Abre tu proyecto con el video en la linea de tiempo (ya editado si quieres).
2. Menu **Area de trabajo -> Secuencias de comandos -> Subtitulador Text+**.
3. La primera vez descarga el modelo de IA (~500 MB), tarda unos minutos.
4. Se crea un Text+ por cada frase, ya en su tiempo. Editalos con el Inspector.

Recomendado: prueba primero en una **copia del timeline** (clic derecho sobre el
timeline -> Duplicar linea de tiempo).

---

## Instalacion desde el codigo (avanzado)

**Requisitos:** Windows 10/11, Python 3.13 (con *Add to PATH*), DaVinci Resolve.

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

Crea un entorno con `faster-whisper`, guarda la configuracion y copia el plugin
en la carpeta de scripts de DaVinci Resolve.

---

## Configuracion

Archivo: `%APPDATA%\SubtituladorIA\config.json`

| Opcion           | Valores                                       | Descripcion                     |
|------------------|-----------------------------------------------|---------------------------------|
| `idioma`         | `es`, `en`, `auto`                            | Idioma del audio                |
| `modelo`         | `tiny`, `base`, `small`, `medium`, `large-v3` | Precision vs. velocidad         |
| `max_caracteres` | numero (ej. `42`)                             | Maximo de caracteres por linea  |

Para audio con mucha musica o ruido, `medium` da resultados mas limpios (pesa mas
y va mas lento).

---

## Estructura del proyecto

| Archivo                 | Descripcion                                      |
|-------------------------|--------------------------------------------------|
| `Subtitulador Text+.py` | Plugin que corre dentro de DaVinci Resolve       |
| `transcribir_worker.py` | Motor de transcripcion (Whisper)                 |
| `Instalar.bat`          | Instalador de un clic (paquete con todo incluido)|
| `instalar.ps1`          | Instalador desde codigo fuente                   |
| `LEEME.txt`             | Guia de instalacion y uso                        |

---

## Licencia

MIT. Ver [LICENSE](LICENSE).
