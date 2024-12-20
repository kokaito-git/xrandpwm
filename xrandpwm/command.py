import subprocess
from typing import Optional, Union, List

from xrandpwm import Vector2D, ROTATION_T, REFLECTION_T, MonitorTransformation, MonitorGamma, MonitorPanning, \
    SCALING_MODE_T, TEAR_FREE_T, MonitorBorders, Geometry


class XRandrCommandGenerator:

    @classmethod
    def monitor(
            cls,
            *,
            output: str,
            active: bool,
            mode: Optional[Vector2D],
            rate: Optional[float],
            pos: Optional[Vector2D],
            rotation: Optional[ROTATION_T],
            reflection: Optional[REFLECTION_T],
            transformation: Optional[MonitorTransformation],
            gamma: Optional[MonitorGamma],
            brightness: Optional[float],
            panning: Optional[MonitorPanning],
            scaling_mode: Optional[SCALING_MODE_T],
            tear_free: Optional[TEAR_FREE_T]
    ):
        """Utiliza la información indicada para construir un comando xrandr para aplicar esos cambios al monitor.

        - `output`: Nombre del monitor
        - `active`: Monitor apagado/encendido. Si es False entonces el resto de los parámetros serán ignorados.
        - `mode`: Resolución del monitor (Vector2D).z
        - `rate`: Frecuencia del monitor (float).
        - `pos`: Posición del monitor (Vector2D).
        - `rotation`: Rotación del monitor (normal, left, inverted, right).
        - `rotation`: Rotación del monitor (normal, left, inverted, right).
        - `reflection`: Reflexión del monitor (normal, x, y, xy).
        - `transformation`: Transformación aplicada al monitor como un objeto `MonitorTransformation`.
        - `gamma`: Configuración gamma como un objeto `MonitorGamma`.
        - `brightness`: Brillo del monitor (float).
        - `panning`: Configuración de panning (opcional).
        - `scaling_mode`: Modo de escalado (None, Full, Center, Full aspect).
        - `tear_free`: Configuración de tear-free (auto, off, on).

        La salida será una lista de cadenas, por cada parámetro dos (así que 0,2,4,... serían como las keys)
            ['--output', 'DVI-D-0' ... '--set "scaling mode"', "Full aspect' ...]

        Notas:
            No precedemos la salida con xrandr, recuerda hacer parts.insert(0, "xrandr").
            Si quieres el formato str puedes simplemente utilizar " ".join(parts).


        Ejemplo de salida:
        ['--output', 'DVI-D-0', '--mode', '1920x1080', '--rate', '60.00', '--pos', '1920x0', '--rotation', 'left',
        '--reflection', 'xy', '--transform', '1.0,0,0,0,1.0,0,0,0,1.0', '--gamma', '1.0:1.0:1.0', '--brightness',
        '1.1', '--panning', '1920x1080+0+0', '--set "scaling mode"', 'Full aspect',
        '--set "TearFree"', 'on']
        """
        parts = ["--output", output]
        if not active:
            parts.append("--off")
            return parts

        if mode:
            parts.extend(("--mode", str(mode)))
        if rate:
            parts.extend(("--rate", f"{rate:0.2f}"))
        if pos:
            parts.extend(("--pos", str(pos)))
        if rotation:
            parts.extend(("--rotation", str(rotation)))
        if reflection:
            parts.extend(("--reflection", str(reflection)))
        if transformation:
            parts.extend(("--transform", cls.parse_transformation(transformation)))
        if gamma:
            parts.extend(("--gamma", cls.parse_gamma(gamma)))
        if brightness:
            parts.extend(("--brightness", str(brightness)))
        if panning:
            parts.extend(("--panning", cls.parse_panning(panning)))
        if scaling_mode:
            parts.extend(("--set \"scaling mode\"", f"{scaling_mode}"))
        if tear_free:
            parts.extend(("--set \"TearFree\"", f"{tear_free}"))

        return parts

    @staticmethod
    def screen(dim: Optional[Vector2D], dpi: Optional[Vector2D]):
        """Devuelve argumentos para --fb y --dpi a partir de `dim` y `dpi`."""

        parts = []
        if dim:
            parts.extend(("--fb", str(dim)))
        if dpi:
            parts.extend(("--dpi", str(dpi)))

        return parts

    @staticmethod
    def parse_transformation(transformation: MonitorTransformation):
        """Devuelve la cadena para --transform a partir de una `MonitorTransformation`."""
        s, r, t, h = (transformation.scale, transformation.rotation, transformation.translation,
                      transformation.homogeneous)
        return (
            f"{s.x or 0},{r.y or 0},{t.x or 0},"
            f"{r.x or 0},{s.y or 0},{t.y or 0},"
            f"{h.x or 0},{h.y or 0},{h.z or 0}"
        )

    @staticmethod
    def parse_gamma(gamma: MonitorGamma):
        """Devuelve la cadena para --gamma a partir de un `MonitorGamma`."""
        return f"{gamma.r or 0}:{gamma.g or 0}:{gamma.b or 0}"

    @staticmethod
    def parse_borders(borders: MonitorBorders):
        """Devuelve la cadena de bordes (L/T/R/B) a partir de `MonitorBorders`."""
        return f"{borders.left}/{borders.top}/{borders.right}/{borders.bottom}"

    @staticmethod
    def parse_geometry(geometry: Geometry):
        """Devuelve la cadena WxH+X+Y a partir de `Geometry`."""
        return f"{geometry.w}x{geometry.h}{geometry.x:+}{geometry.y:+}"

    @classmethod
    def parse_panning(cls, panning: MonitorPanning):
        """Devuelve la cadena para --panning a partir de `MonitorPanning`."""

        # Geometría
        s = cls.parse_geometry(panning.geometry)

        # Tracking
        if panning.tracking is not None:
            s += f"/{cls.parse_geometry(panning.tracking)}"
        elif panning.tracking is None and panning.borders is not None:
            s += "/"

        # Bordes
        if panning.borders is not None:
            s += f"/{cls.parse_borders(panning.borders)}"

        return s


class XRandr:
    @staticmethod
    def xrandr(args: Optional[str] = None) -> subprocess.CompletedProcess:
        """Ejecuta el comando xrandr con los argumentos proporcionados y retorna el resultado.

        - `args`: str con los argumentos, ej.: '--output "DVI-D-0" --off'
        """

        if args is None:
            args = ""

        cmd = f"xrandr {args}"
        return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
