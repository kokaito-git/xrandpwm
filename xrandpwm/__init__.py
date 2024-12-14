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
    SingleResolution, MonitorResolutions, MonitorTransformation, MonitorGamma, MonitorBorders, MonitorPanning,
    BaseMonitorData, DisconnectedMonitorData, ConnectedMonitorData, InactiveMonitorData, ActiveMonitorData,
    MonitorState
)
from .monitorbundle import MonitorStateBundle, MonitorStateBundleAssembler

__all__ = [
    "Geometry", "Vector2D", "Vector2DF", "Vector3D", "Vector3DF",
    ####################################################
    "SingleResolution", "MonitorResolutions", "MonitorTransformation", "MonitorGamma", "MonitorBorders",
    "MonitorPanning", "BaseMonitorData", "DisconnectedMonitorData", "ConnectedMonitorData", "InactiveMonitorData",
    "ActiveMonitorData", "MonitorState",
    ####################################################
    "MonitorStateBundle", "MonitorStateBundleAssembler"
]

if __name__ == "__main__":
    msb = MonitorStateBundleAssembler.assemble()
    print(msb)