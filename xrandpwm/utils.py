from kcolors.refs import *  # pyright: ignore[]
from typing import Union
from pydantic import BaseModel, Field, model_validator


class DevError(Exception):
    def __init__(self, message, prefix=f"{RED}[!] DevError:{END} "):
        """
        Clase para manejar errores de desarrollo causados por escenarios no considerados.

        Si encuentras un error de este tipo, por favor repórtalo. Agrega un prefijo estándar
        a los mensajes de error para diferenciarlos.

        Attributes:
            message (str): Mensaje del error.
            prefix (str): Prefijo personalizado para el mensaje de error.
        """
        self.prefix = prefix
        self.message = message
        self.message = self.prefix + self.message
        super().__init__(self.message)


class Geometry(BaseModel):
    """
    Representa una geometría rectangular con dimensiones y posición.

    Attributes:
        w (int): Ancho del rectángulo, debe ser mayor que 0.
        h (int): Alto del rectángulo, debe ser mayor que 0.
        x (int): Posición horizontal relativa (por defecto 0).
        y (int): Posición vertical relativa (por defecto 0).
    """

    w: int = Field()
    h: int = Field()
    x: int = Field(default=0)
    y: int = Field(default=0)

    @model_validator(mode="after")
    def __post_validation(self) -> "Geometry":
        if self.w <= 0 or self.h <= 0:
            raise ValueError(f"w y h tienen que ser mayores que 0: {self!r}")
        return self

    def __str__(self, ind: str = "", header: bool = True) -> str:
        ind2 = ind + "  " if header else ind
        parts = [f"{ind}{BLUE}{self.__class__.__name__}{END}"] if header else []
        parts.append(f"{ind2}{self.w}x{self.h}{self.x:+}{self.y:+}")
        return "\n".join(parts)


class Vector2D(BaseModel):
    """
    Representa un vector 2D con coordenadas enteras.

    Attributes:
        x (int): Coordenada x (por defecto 0).
        y (int): Coordenada y (por defecto 0).
    """
    x: int = Field(default=0)
    y: int = Field(default=0)

    def __str__(self) -> str:
        return f"{self.x}x{self.y}"


class Vector2DF(BaseModel):
    """
    Representa un vector 2D con coordenadas flotantes.

    Attributes:
        x (int): Coordenada x (por defecto 0.0).
        y (int): Coordenada y (por defecto 0.0).
    """
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)

    def __str__(self) -> str:
        return f"{self.x:.2f}x{self.y:.2f}"


class Vector3D:
    """
    Representa un vector 3D con coordenadas enteras.

    Attributes:
        x (int): Coordenada x (por defecto 0).
        y (int): Coordenada y (por defecto 0).
        z (int): Coordenada z (por defecto 0).
    """
    x: int = Field(default=0)
    y: int = Field(default=0)
    z: int = Field(default=0)

    def __str__(self) -> str:
        return f"{self.x}x{self.y}x{self.z}"


class Vector3DF(BaseModel):
    """
    Representa un vector 3D con coordenadas flotantes.

    Attributes:
        x (Union[int, float]): Coordenada x (por defecto 0.0).
        y (Union[int, float]): Coordenada y (por defecto 0.0).
        z (Union[int, float]): Coordenada z (por defecto 0.0).
    """
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    z: float = Field(default=0.0)

    def __str__(self) -> str:
        return f"{self.x:.2f}x{self.y:.2f}x{self.z:.2f}"
