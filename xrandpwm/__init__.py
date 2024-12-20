"""
`xrandpwm` es un paquete diseñado para gestionar y obtener información detallada sobre monitores conectados
a través de `xrandr`, con un enfoque especial en entornos que utilizan `bspwm`. El nombre combina `xrandr`
(la herramienta para la gestión de monitores) y `pwm` (por su integración optimizada para `bspwm`), aunque es
compatible con configuraciones más amplias de `xrandr`.

### Componentes principales:
- `MonitorState`: Representa el estado de un monitor (activo, inactivo, desconectado).
- `MonitorStateBundle`: Agrega información sobre todos los monitores y la pantalla en un objeto único.
- `MonitorStateBundleAssembler`: Ensambla automáticamente un `MonitorStateBundle` a partir del comando `xrandr`.
- Clases auxiliares (`Geometry`, `Vector2D`, `Vector3DF`, etc.) para trabajar con datos geométricos y de resolución.

### Características destacadas:
- Proporciona compatibilidad completa con `bspwm`, haciendo que la gestión de monitores en este entorno sea
  más eficiente.
- Aprovecha las capacidades extensas de `xrandr` para obtener datos avanzados como transformaciones, gamma,
  modos de escalado (`scaling modes`), y configuraciones de `TearFree`.

### Ejemplo de uso:
```python
from xrandpwm import MonitorStateBundleAssembler

# Ensamblar el estado actual de los monitores
msb = MonitorStateBundleAssembler.assemble()
print(msb)

# Convertir el estado a JSON
msb_json = msb.model_dump_json()
print(msb_json)

# Reconstruir desde JSON
msb2 = MonitorStateBundle.model_validate_json(msb_json)
print(msb2)
"""

from .utils import Geometry, Vector2D, Vector2DF, Vector3D, Vector3DF
from .monitorstate import (
    ROTATION_T, ROTATION, REFLECTION_T, REFLECTION, SCALING_MODE_T, SCALING_MODE, TEAR_FREE_T, TEAR_FREE,
    SingleResolution, MonitorResolutions, MonitorTransformation, MonitorGamma, MonitorBorders, MonitorPanning,
    BaseMonitorData, DisconnectedMonitorData, ConnectedMonitorData, InactiveMonitorData, ActiveMonitorData,
    MonitorState
)
from .monitorbundle import MonitorStateBundle, MonitorStateBundleAssembler
from .command import XRandrCommandGenerator, XRandr

__all__ = [
    "Geometry", "Vector2D", "Vector2DF", "Vector3D", "Vector3DF",
    ####################################################
    "ROTATION_T", "ROTATION", "REFLECTION_T", "REFLECTION", "SCALING_MODE_T", "SCALING_MODE",
    "TEAR_FREE_T", "TEAR_FREE",
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    "SingleResolution", "MonitorResolutions", "MonitorTransformation", "MonitorGamma", "MonitorBorders",
    "MonitorPanning", "BaseMonitorData", "DisconnectedMonitorData", "ConnectedMonitorData", "InactiveMonitorData",
    "ActiveMonitorData", "MonitorState",

    ####################################################
    "MonitorStateBundle", "MonitorStateBundleAssembler",

    ####################################################
    "XRandrCommandGenerator", "XRandr"
]

if __name__ == "__main__":
    msb = MonitorStateBundleAssembler.assemble()
    print(msb)

    m = msb.monitors["DVI-D-0"]
    print(m)

    sm_output = XRandrCommandGenerator.monitor(
        output="DVI-D-0",
        active=True,
        mode=Vector2D(x=1920, y=1080),
        rate=60.0,
        pos=Vector2D(x=1920, y=0),
        rotation="left",
        reflection="xy",
        transformation=MonitorTransformation(
            scale=Vector2DF(x=1.0, y=1.0),
            rotation=Vector2DF(x=0., y=0.),
            translation=Vector2DF(x=0., y=0.),
            homogeneous=Vector3DF(x=0., y=0., z=1.)
        ),
        gamma=MonitorGamma(r=1., g=1., b=1.),
        brightness=1.1,
        panning=MonitorPanning(geometry=Geometry(w=1920, h=1080, x=0, y=0), tracking=None, borders=None),
        scaling_mode="Full aspect",
        tear_free="on"
    )
    print(sm_output)

    dim = Vector2D(x=1920, y=1080)
    dpi = Vector2D(x=96, y=96)
    r = XRandrCommandGenerator.screen(dim=dim, dpi=dpi)
    print(r)
