from .utils import Geometry, Vector2D, Vector2DF, Vector3DF
from kcolors.refs import *  # pyright: ignore[]
from typing import List, Literal, Optional, Tuple, Union, Any
from pydantic import BaseModel, Field, model_validator


class SingleResolution(BaseModel, frozen=True):
    """
    Representa una única resolución soportada por un monitor y las frecuencias disponibles para dicha resolución.

    - `resolution`: Resolución en píxeles (ancho x alto) representada por un `Vector2D`.
    - `freqs`: Lista de frecuencias (en Hz) soportadas por la resolución.
    """
    resolution: Vector2D
    freqs: List[float]


class MonitorResolutions(BaseModel):
    """
    Contiene las resoluciones disponibles en un monitor conectado, incluyendo la resolución y frecuencia
    actual y preferida.

    - `resolutions`: Lista de objetos `SingleResolution`, cada uno representando una resolución soportada.
    - `preferred`: Tupla opcional `(res_index, freq_index)` que indica la resolución y frecuencia preferida.
    - `current`: Tupla opcional `(res_index, freq_index)` que indica la resolución y frecuencia actuales.

    Métodos principales:
    - `get_preferred_res()`: Retorna el objeto `SingleResolution` correspondiente a la resolución preferida.
    - `get_current_res()`: Retorna el objeto `SingleResolution` correspondiente a la resolución actual.
    - `get_preferred_freq()`: Retorna la frecuencia preferida como un `float`.
    - `get_current_freq()`: Retorna la frecuencia actual como un `float`.
    """

    resolutions: List[SingleResolution]
    preferred: Optional[Tuple[int, int]]
    current: Optional[Tuple[int, int]]

    @model_validator(mode="after")
    def __post_validation(self) -> "MonitorResolutions":
        self.__validate_resolutions()
        self.__validate_current()
        self.__validate_preferred()
        return self

    def get_preferred_res(self) -> Optional[SingleResolution]:
        """Retorna la resolución preferida, determinada por la tupla preferred."""
        if self.preferred is None:
            return None
        res_index = self.preferred[0]
        return self.resolutions[res_index]

    def get_current_res(self) -> Optional[SingleResolution]:
        """Retorna la resolución actual, determinada por la tupla current."""
        if self.current is None:
            return None
        res_index = self.current[0]
        return self.resolutions[res_index]

    def get_preferred_freq(self) -> Optional[float]:
        """Retorna la frecuencia preferida."""
        if self.preferred is None:
            return None

        res_index, freq_index = self.preferred
        preferred_res = self.resolutions[res_index]
        return preferred_res.freqs[freq_index]

    def get_current_freq(self) -> Optional[float]:
        """Retorna la frecuencia actual."""
        if self.current is None:
            return None
        res_index, freq_index = self.current
        current_res = self.resolutions[res_index]
        return current_res.freqs[freq_index]

    def __get_freq_symbols(self, ri: int, fi: int) -> Tuple[str, str]:
        """
        Retorna una tupla (str, str) con la frecuencia formateada a 2 decimales y sus símbolos
        correspondientes (* para actual, + para preferida).
        """
        # Averiguamos si es la frecuencia preferida/actual
        res, preferred, current = (self.resolutions[ri], self.preferred, self.current)
        is_preferred = False if preferred is None else (ri == preferred[0]) and (fi == preferred[1])
        is_current = False if current is None else (ri == current[0]) and (fi == current[1])

        # Agregamos los símbolos que le corresponden
        freq_symbols = f"{'*' if is_current else ''}{'+' if is_preferred else ''}"

        # Frecuencia formateada y sus símbolos, ej. [60.00, '*']
        return f"{res.freqs[fi]:0.2f}", freq_symbols

    def __make_res_str_line(self, ri: int) -> List[str]:
        """
        Función auxiliar de str que retorna una lista donde cada campo representa un row de la línea
        """
        res = self.resolutions[ri]

        # Resolución y 4 espacios ej. ['1920x1080', '    ']
        parts = [res.resolution.__str__(), "    "]

        # Agregamos frecuencia y sus símbolos, ej. de freq_symbols: [60.00, '*'] (frecuencia current)
        #   Nota: Fijate que 60.00 está formateado para mostrar '.00' dos decimales
        for fi in range(len(res.freqs)):
            freq_symbols = self.__get_freq_symbols(ri, fi)
            parts.extend(freq_symbols)

        return parts

    @staticmethod
    def __calculate_row_widths(res_str_rows: List[List[str]]) -> List[int]:
        """
        Función auxiliar de str que calcula el ancho mínimo requerido por cada row indiscriminadamente
        """
        max_cols = max((len(row) for row in res_str_rows), default=0)
        row_widths = [0] * max_cols

        for row in res_str_rows:
            for i, part in enumerate(row):
                length = len(part)
                if length > row_widths[i]:
                    row_widths[i] = length
        return row_widths

    def __str__(self, ind: str = "", header: bool = True) -> str:
        ind2 = ind + "  " if header else ind
        parts = [f"{ind}{BLUE}{self.__class__.__name__}{END}:"] if header else []

        res_str_rows = []
        # Creamos las líneas separadas por rows (lista de listas de str)
        for ri in range(len(self.resolutions)):
            res_str_rows.append(self.__make_res_str_line(ri))

        # Calculamos los tamaños de las row
        row_widths = self.__calculate_row_widths(res_str_rows)

        # Tamaño custom para la row de los simbólos de las frecuencias (4 de ancho)
        for i in range(3, len(row_widths), 2):
            row_widths[i] = max(row_widths[i], 4)

        # Creamos las líneas aplicando los sizes a las row
        res_parts = []
        for row in res_str_rows:
            line_parts = []
            for i, part in enumerate(row):
                width = row_widths[i]
                line_parts.append(f"{part:<{width}}")
            line = ind2 + "".join(line_parts)
            res_parts.append(line)
        res_str = "\n".join(res_parts)

        # Aplicamos colores a los símbolos '*', '+' antes de unir res_str a parts
        res_str = res_str.replace("*", f"{GREEN}*{END}")
        res_str = res_str.replace("+", f"{GREEN}+{END}")
        parts.append(res_str)

        return "\n".join(parts)

    def __validate_resolutions(self):
        if not self.resolutions:
            raise ValueError("Debes indicar al menos una resolución.")

    def __validate_preferred(self):
        if self.preferred is not None:
            if len(self.preferred) != 2:
                raise ValueError("Preferred debe ser una tupla de dos elementos.")
            self.__validate_indexes("preferred", self.preferred)

    def __validate_current(self):
        if self.current is not None:
            if len(self.current) != 2:
                raise ValueError("Current debe ser una tupla de dos elementos.")
            self.__validate_indexes("current", self.current)

    def __validate_indexes(self, kind: Literal["preferred", "current"], indexes: Tuple[int, int]):
        rmax = len(self.resolutions) - 1
        ri, fi = indexes

        if not (0 <= ri <= rmax):
            raise ValueError(f"El índice de resolución '{kind}' '{ri}' está fuera del límite permitido 0-{rmax}")

        freqs = self.resolutions[ri].freqs
        fmax = len(freqs) - 1
        if not (0 <= fi <= fmax):
            raise ValueError(
                f"Índice de frecuencia '{kind}' (resolución {ri}) fuera de rango: {fi} (permitido: 0-{fmax})"
            )


class MonitorTransformation(BaseModel):
    """
    Representa la matriz de transformación aplicada a un monitor.

    - `scale`: Factor de escala en los ejes `x` y `y` como `Vector2DF`.
    - `rotation`: Rotación aplicada en los ejes `x` y `y` como `Vector2DF`.
    - `translation`: Valores de traslación en los ejes `x` y `y` como `Vector2DF`.
    - `homogeneous`: Coordenadas homogéneas como `Vector3DF`.
    """

    scale: Vector2DF
    rotation: Vector2DF
    translation: Vector2DF
    homogeneous: Vector3DF

    def __str__(self, ind: str = "", header: bool = False) -> str:
        ind2 = ind + "  " if header else ind
        parts = [f"{ind}{BLUE}{self.__class__.__name__}{END}:"] if header else []

        parts.extend((
            f"{ind2}{self.scale.x:.6f} {self.rotation.y:.6f} {self.translation.x:.6f}",
            f"{ind2}{self.rotation.x:.6f} {self.scale.y:.6f} {self.translation.y:.6f}",
            f"{ind2}{self.homogeneous.x:.6f} {self.homogeneous.y:.6f} {self.homogeneous.z:.6f}"
        ))
        return "\n".join(parts)


class MonitorGamma(BaseModel):
    """
    Representa los valores de corrección gamma para un monitor en los canales RGB.

    - `r`: Valor gamma para el canal rojo.
    - `g`: Valor gamma para el canal verde.
    - `b`: Valor gamma para el canal azul.
    """

    r: float
    g: float
    b: float

    def __str__(self, ind: str = "", header: bool = True) -> str:
        s = f"{ind}{BLUE}{self.__class__.__name__}{END}: " if header else f"{ind} "
        s += f"rgb({self.r}, {self.g}, {self.b})"
        return s


class MonitorBorders(BaseModel):
    """
    Representa los bordes configurados para el monitor.

    - `left`: Borde izquierdo en píxeles.
    - `top`: Borde superior en píxeles.
    - `right`: Borde derecho en píxeles.
    - `bottom`: Borde inferior en píxeles.
    """

    left: int
    top: int
    right: int
    bottom: int

    def __str__(self) -> str:
        cname = self.__class__.__name__
        return f"{BLUE}{cname}{END}: {self.left}/{self.top}/{self.right}/{self.bottom}"


class MonitorPanning(BaseModel):
    """
    Representa los bordes configurados para el monitor.

    - `left`: Borde izquierdo en píxeles.
    - `top`: Borde superior en píxeles.
    - `right`: Borde derecho en píxeles.
    - `bottom`: Borde inferior en píxeles.
    """

    panning: Geometry
    tracking: Optional[Geometry]
    borders: Optional[MonitorBorders]

    def __str__(self, ind: str = "", header: bool = True) -> str:
        s = f"{ind}{BLUE}{self.__class__.__name__}{END}: " if header else f"{ind} "
        s += self.panning.__str__(ind="", header=False)
        if self.tracking is not None:
            s += f"/{self.tracking}"
        elif self.tracking is None and self.borders is not None:
            s += "/0x0+0+0"
        if self.borders is not None:
            s += f"/{self.borders}"
        return s


class BaseMonitorData(BaseModel):
    """
    Clase base para representar datos generales de un monitor.

    - `name`: Nombre del monitor.
    - `primary`: Indica si es el monitor principal.
    - `connected`: Estado de conexión del monitor (siempre `False` en esta clase base).
    - `active`: Estado activo del monitor (siempre `False` en esta clase base).
    """

    name: str
    primary: bool
    class_name: Literal["BaseMonitorData"] = Field(default="BaseMonitorData", init=False)
    connected: bool = Field(default=False, init=False, exclude=True)
    active: bool = Field(default=False, init=False, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def __pre_validation(cls, data: Any) -> Any:
        assert cls != BaseMonitorData, f"{cls.__name__} no puede ser instanciado directamente."
        if isinstance(data, dict):
            assert "connected" not in data, "No está permitido asignar valores a 'connected'."
            assert "active" not in data, "No está permitido asignar valores a 'active'."
        return data

    def header_str(self, ind: str = "") -> str:
        return f"{ind}{BLUE}{self.class_name}{END}"

    def status_str(self, ind: str = "") -> str:
        primary_str = f"{GREEN}*{END}" if self.primary else ""
        status = f"{GREEN}active{END}" if self.active \
            else f"{YELLOW}inactive{END}" if self.connected \
            else f"{BLACK}disconnected{END}"
        return f"{ind}{self.name}{primary_str} ({status})"

    def __str__(self, ind: str = "", header: bool = True) -> str:
        ind2 = ind + "  " if header else ind
        parts = [self.header_str(ind=ind)] if header else []
        parts.append(self.status_str(ind=ind2))
        return "\n".join(parts)


class DisconnectedMonitorData(BaseMonitorData):
    """
    Representa un monitor desconectado.
    - `name`: Nombre del monitor.
    - `primary`: Indica si es el monitor principal.
    """
    class_name: Literal["DisconnectedMonitorData"] = Field(default="DisconnectedMonitorData", init=False)


class ConnectedMonitorData(BaseMonitorData):
    """
    Representa un monitor conectado (pero no necesariamente activo).
    - `name`: Nombre del monitor.
    - `primary`: Indica si es el monitor principal.
    - `resolutions`: Objeto `MonitorResolutions` que contiene las resoluciones soportadas.
    """
    class_name: Literal["ConnectedMonitorData"] = Field(default="ConnectedMonitorData", init=False)
    connected: bool = Field(default=True, init=False, exclude=True)
    resolutions: MonitorResolutions

    @model_validator(mode="before")
    @classmethod
    def __pre_validation(cls, data: Any) -> Any:
        assert cls != ConnectedMonitorData, f"{cls.__name__} no puede ser instanciado directamente."
        return data

class InactiveMonitorData(ConnectedMonitorData):
    """
    Representa un monitor conectado pero no activo.
    - `name`: Nombre del monitor.
    - `primary`: Indica si es el monitor principal.
    - `resolutions`: Objeto `MonitorResolutions` que contiene las resoluciones soportadas.
    """
    class_name: Literal["InactiveMonitorData"] = Field(default="InactiveMonitorData", init=False)
    active: bool = Field(default=False, init=False, exclude=True)

    def __str__(self, ind: str = "", header: bool = True) -> str:
        ind2 = ind + "  " if header else ind
        ind3 = ind2 + "  "
        parts = [self.header_str(ind=ind)] if header else []
        parts.append(self.status_str(ind=ind2))
        parts.append(self.resolutions.__str__(ind=ind3, header=True))
        return "\n".join(parts)


class ActiveMonitorData(ConnectedMonitorData):
    """
    Representa un monitor activo.
    - `name`: Nombre del monitor.
    - `primary`: Indica si es el monitor principal.
    - `resolutions`: Objeto `MonitorResolutions` que contiene las resoluciones soportadas.
    - `geometry`: Geometría del monitor como un objeto `Geometry`.
    - `rotation`: Rotación del monitor (normal, left, inverted, right).
    - `reflection`: Reflexión del monitor (normal, x, y, xy).
    - `transformation`: Transformación aplicada al monitor como un objeto `MonitorTransformation`.
    - `gamma`: Configuración gamma como un objeto `MonitorGamma`.
    - `brightness`: Brillo del monitor como un valor flotante.
    - `panning`: Configuración de panning (opcional).
    - `scaling_mode`: Modo de escalado (Full, Center, Full aspect).
    - `tear_free`: Configuración de tear-free (off, on, auto).
    """
    class_name: Literal["ActiveMonitorData"] = Field(default="ActiveMonitorData", init=False)
    active: bool = Field(default=True, init=False, exclude=True)

    # Only active:
    geometry: Geometry
    rotation: Literal["normal", "left", "inverted", "right"]
    reflection: Literal["normal", "x", "y", "xy"]
    transformation: MonitorTransformation
    gamma: MonitorGamma
    brightness: float

    # Si no se ha aplicado será None
    panning: Optional[MonitorPanning]

    # Solo disponible en ciertos entornos (ej. en mi host aparecen pero en mi vm no)
    scaling_mode: Optional[Literal["Full", "Center", "Full aspect"]]
    tear_free: Optional[Literal["off", "on", "auto"]]

    def __str__(self, ind: str = "", header: bool = True) -> str:
        ind2 = ind + "  " if header else ind
        ind3 = ind2 + "  "
        parts = [self.header_str(ind=ind)] if header else []

        dim_str = self.geometry.__str__(ind="", header=False)
        status_str = self.status_str(ind=ind2)
        status_str += f" {dim_str} {self.rotation} {self.reflection}"
        parts.append(status_str)

        parts.append(self.resolutions.__str__(ind=ind3, header=True))
        parts.append(self.gamma.__str__(ind=ind3, header=True))
        parts.append(f"{ind3}{BLUE}MonitorBrightness{END}: {self.brightness}")
        parts.append(self.transformation.__str__(ind=ind3, header=True))
        if self.panning is not None:
            parts.append(self.panning.__str__(ind=ind3))

        if self.scaling_mode is not None:
            parts.append(f"{ind3}{BLUE}Scaling Mode{END}: {self.scaling_mode}")

        if self.tear_free is not None:
            parts.append(f"{ind3}{BLUE}Tear Free{END}: {self.tear_free}")

        return "\n".join(parts)


class MonitorState(BaseModel):
    """
    Representa el estado actual de un monitor (desconectado, inactivo o activo).

    - `md`: Unión de `DisconnectedMonitorData`, `InactiveMonitorData` y `ActiveMonitorData`.

    Propiedades principales:
    - `name`: Nombre del monitor.
    - `primary`: Indica si es el monitor principal.
    - `connected`: Indica si el monitor está conectado.
    - `active`: Indica si el monitor está activo.

    - `resolutions`: Resoluciones soportadas (disponibles solo si el monitor está conectado).

    - `geometry`, `rotation`, `reflection`, `transformation`, `gamma`, `brightness`, `panning`, `scaling_mode`, `tear_free`:
      Propiedades disponibles solo si el monitor está activo.
    """

    md: Union[DisconnectedMonitorData, InactiveMonitorData, ActiveMonitorData]

    @property
    def name(self) -> str:
        return self.md.name

    @property
    def primary(self) -> bool:
        return self.md.primary

    @property
    def connected(self) -> bool:
        if isinstance(self.md, (InactiveMonitorData, ActiveMonitorData)):
            return True
        return False

    @property
    def active(self) -> bool:
        return isinstance(self.md, ActiveMonitorData)

    @property
    def resolutions(self) -> MonitorResolutions:
        if self.connected:
            return self.md.resolutions
        raise AttributeError("Resolutions are only available for connected or active monitors.")

    @property
    def geometry(self) -> Geometry:
        if self.active:
            return self.md.geometry
        raise AttributeError("Geometry is only available for active monitors.")

    @property
    def rotation(self) -> Literal["normal", "left", "inverted", "right"]:
        if self.active:
            return self.md.rotation
        raise AttributeError("Rotation is only available for active monitors.")

    @property
    def reflection(self) -> Literal["normal", "x", "y", "xy"]:
        if self.active:
            return self.md.reflection
        raise AttributeError("Reflection is only available for active monitors.")

    @property
    def transformation(self) -> MonitorTransformation:
        if self.active:
            return self.md.transformation
        raise AttributeError("Transformation is only available for active monitors")

    @property
    def gamma(self) -> MonitorGamma:
        if self.active:
            return self.md.gamma
        raise AttributeError("Gamma is only available for active monitors")

    @property
    def brightness(self) -> float:
        if self.active:
            return self.md.brightness
        raise AttributeError("Brightness is only available for active monitors")

    @property
    def panning(self) -> Optional[MonitorPanning]:
        if self.active:
            return self.md.panning
        raise AttributeError("Panning is only available for active monitors")

    @property
    def scaling_mode(self) -> Optional[Literal["Full", "Center", "Full aspect"]]:
        if self.active:
            return self.md.scaling_mode
        raise AttributeError("Scaling Mode is only available for active monitors")

    @property
    def tear_free(self) -> Optional[Literal["off", "on", "auto"]]:
        if self.active:
            return self.md.tear_free
        raise AttributeError("Scaling Mode is only available for active monitors")

    def __str__(self, ind: str = "", header: bool = True) -> str:
        return self.md.__str__(ind=ind, header=header)
