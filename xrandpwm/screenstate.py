from kcolors.refs import *  # pyright: ignore[]
from pydantic import BaseModel, Field
from .utils import Vector2D


class ScreenResolutionState(BaseModel):
    """
    Representa el estado de la resolución de la pantalla principal.

    Este modelo incluye:
    - `min`: Resolución mínima soportada (e.g., 1x1).
    - `dim`: Resolución actual o configurada. (e.g, 3840x1080)
    - `max`: Resolución máxima soportada (e.g., 16384x16384).

    Se utiliza para almacenar y mostrar las características de la pantalla en términos
    de resoluciones soportadas.
    """

    min: Vector2D = Field()
    dim: Vector2D = Field()
    max: Vector2D = Field()

    def __str__(self, ind: str = "", header: bool = True):
        # ind2 = ind + "  " if header else ind
        parts = [f"{ind}{BLUE}{self.__class__.__name__}{END}:"] if header else []
        parts.append(f"min: {self.min}, dim: {self.dim}, max: {self.max}")
        return " ".join(parts)
