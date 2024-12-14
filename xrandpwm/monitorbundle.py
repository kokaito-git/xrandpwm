from .monitorstate import (
    MonitorState, MonitorTransformation, MonitorGamma, MonitorPanning, MonitorResolutions, ActiveMonitorData,
    InactiveMonitorData, DisconnectedMonitorData, SingleResolution, MonitorBorders, BaseMonitorData
)
from .screenstate import ScreenResolutionState
from .utils import DevError, Geometry, Vector2D, Vector2DF, Vector3DF
from kcolors.refs import *  # pyright: ignore[]
import re, subprocess
from typing import Dict, List, Literal, Optional, Tuple, Iterator
from pydantic import BaseModel, Field


class MonitorStateBundle(BaseModel):
    """
    Representa un conjunto de estados de monitores y la configuración de pantalla.

    Contiene información de todos los monitores conectados o detectados, junto con
    los datos de resolución y dimensiones de la pantalla sobre la que están dispuestos.
    """

    monitors: Dict[str, MonitorState] = Field()
    screen: ScreenResolutionState = Field()

    def get_monitor_names(self) -> List[str]:
        """Retorna una lista con los nombres de los monitores en el bundle."""
        return list(self.monitors.keys())

    def get_monitor(self, name: str) -> MonitorState:
        """Obtiene un monitor específico por su nombre."""
        return self.monitors[name]

    def get_all_monitors(self) -> Dict[str, MonitorState]:
        """Retorna un diccionario con todos los monitores en el bundle."""
        return self.monitors

    def get_filtered_monitors(self, state: Literal["disconnected", "inactive", "active"]) -> Dict[str, MonitorState]:
        """Filtra y retorna los monitores según su estado (`disconnected`, `inactive`, `active`)."""
        filtered = self.monitors

        if state == "disconnected":
            filtered = {n: m for n, m in filtered.items() if not m.connected}
        elif state == "inactive":
            filtered = {n: m for n, m in filtered.items() if m.connected and not m.active}
        elif state == "active":
            filtered = {n: m for n, m in filtered.items() if m.active}
        else:
            raise ValueError(f"{RED}[!] Error{END}: {state} no es un estado válido.")

        return filtered

    def get_primary_monitor(self) -> Optional[MonitorState]:
        """Retorna el monitor principal si existe, de lo contrario, retorna `None`."""
        return next((m for m in self.monitors.values() if m.primary), None)

    def __str__(self, ind: str = "", header: bool = True) -> str:
        ind2 = ind + "  " if header else ind
        ind3 = ind2 + "  "
        parts = [f"{ind}{BLUE}{self.__class__.__name__}{END}:"] if header else []

        parts.append(self.screen.__str__(ind=ind2, header=True))
        parts.append(f"{ind2}{BLUE}MonitorStates{END}:")
        for monitor in self.monitors.values():
            parts.append(monitor.__str__(ind=ind3, header=False))

        return "\n".join(parts)


class MonitorStateBundleAssembler:
    """
    Ensamblador para crear un objeto `MonitorStateBundle`.

    Utiliza las herramientas `xrandr` y `xrandr --verbose` para obtener información
    sobre monitores y su estado, y genera un objeto que encapsula estos datos de
    manera estructurada.
    """

    @classmethod
    def assemble(cls) -> MonitorStateBundle:
        """
        Obtiene información acerca de los monitores y de la pantalla sobre la que se ubican todos estos
        y construye un objeto MonitorStateBundle.
        """

        xrandr_output = cls.__xrandr().stdout
        v_xrandr_output = cls.__xrandr("--verbose").stdout
        xrandr_output_lines = xrandr_output.splitlines()

        # Screen State
        screen_state = cls.__get_screen_state(xrandr_output_lines[0])

        # Diccionario de MonitorState
        monitor_states = cls.__get_all_monitor_states(
            xrandr_output_lines, v_xrandr_output
        )

        return MonitorStateBundle(monitors=monitor_states, screen=screen_state)

    @classmethod
    def __get_screen_state(cls, screen_line: str) -> ScreenResolutionState:
        result: List[Tuple[str, str]] = re.findall(r"(\d+) x (\d+)", screen_line)
        parsed_result: Iterator[Tuple[int, int]] = ((int(w), int(h)) for w, h in result)
        min_w, min_h = next(parsed_result)
        w, h = next(parsed_result)
        max_w, max_h = next(parsed_result)

        srs = ScreenResolutionState(
            min=Vector2D(x=min_w, y=min_h), dim=Vector2D(x=w, y=h), max=Vector2D(x=max_w, y=max_h)
        )

        return srs

    @classmethod
    def __get_all_monitor_states(
            cls, xrandr_output_lines: List[str], v_xrandr_output: str
    ) -> Dict[str, MonitorState]:
        """Retorna la información completa de un monitor -> Diccionario de MonitorState"""

        # Cabeceras y Resoluciones
        # (xrandr)
        all_raw_headers, all_raw_resolutions = cls.__get_raw_headers_resolutions(xrandr_output_lines)

        # Lista con los nombres de los monitores activos
        # (xrandr --listactivemonitors)
        active_monitor_names = cls.__get_active_monitor_names()

        # Información avanzada
        # (xrandr --verbose)
        active_raw_advanced_datas = cls.__get_active_raw_advanced_datas(
            v_xrandr_output, active_monitor_names
        )

        transformations: Dict[str, MonitorTransformation] = (
            cls.__get_monitors_transformation(active_raw_advanced_datas)
        )

        gammas: Dict[str, MonitorGamma] = cls.__get_monitors_gammas(active_raw_advanced_datas)
        brightnesses: Dict[str, float] = cls.__get_monitors_brightnesses(active_raw_advanced_datas)

        # Información avanzada y situacional
        # pannings no aparecerá en el output de xrandr si no se está utilizando,
        # por lo tanto, en esos casos panning será None
        pannings: Dict[str, Optional[MonitorPanning]] = cls.__get_monitors_pannings(active_raw_advanced_datas)

        # scaling_modes y tear_free son valores solo disponibles en ciertos sistemas
        # xrandr --output DVI-D-0 --set "scaling mode" "Full aspect"
        scaling_modes: Dict[str, Optional[Literal["Full", "Center", "Full aspect"]]] = (
            cls.__get_scaling_modes(active_raw_advanced_datas)
        )

        # xrandr --output DVI-D-0 --set "TearFree" "on"
        tear_frees: Dict[str, Optional[Literal["off", "on", "auto"]]] = (
            cls.__get_tear_frees(active_raw_advanced_datas)
        )

        # Creamos los objetos MonitorData
        all_monitor_datas: Dict[str, BaseMonitorData] = {}
        for monitor_name in all_raw_headers:
            all_monitor_datas[monitor_name] = cls.__get_monitor_data(
                monitor_name,
                all_raw_headers=all_raw_headers,
                active_monitor_names=active_monitor_names,
                all_raw_resolutions=all_raw_resolutions,
                transformations=transformations,
                gammas=gammas,
                brightnesses=brightnesses,
                pannings=pannings,
                scaling_modes=scaling_modes,
                tear_frees=tear_frees
            )

        # Creamos los MonitorStates con los MonitorData y los retornamos
        all_monitor_states: Dict[str, MonitorState] = {}
        for monitor_name, monitor_data in all_monitor_datas.items():
            monitor_state = MonitorState(md=monitor_data)
            all_monitor_states[monitor_name] = monitor_state

        return all_monitor_states

    @classmethod
    def __get_monitor_data(
            cls,
            monitor_name: str, all_raw_headers: Dict[str, str], active_monitor_names: List[str],
            all_raw_resolutions: Dict[str, List[str]],
            transformations: Dict[str, MonitorTransformation], gammas: Dict[str, MonitorGamma],
            brightnesses: Dict[str, float], pannings: Dict[str, Optional[MonitorPanning]],
            scaling_modes: Dict[str, Optional[Literal["Full", "Center", "Full aspect"]]],
            tear_frees: Dict[str, Optional[Literal["off", "on", "auto"]]],
    ) -> BaseMonitorData:
        raw_header = all_raw_headers[monitor_name]
        # Si el monitor no está conectado entonces geometry, rotation y reflection serán None
        connected, active, primary, geometry, rotation, reflection = (
            cls.__parse_raw_header(raw_header, active_monitor_names)
        )

        # Solo para monitores conectados
        resolutions: Optional[MonitorResolutions] = (
            cls.__parse_raw_monitor_resolutions(
                monitor_name, active, all_raw_resolutions[monitor_name]
            )
        )

        # Solo para monitores activos
        transformation = transformations.get(monitor_name)
        gamma = gammas.get(monitor_name)
        brightness = brightnesses.get(monitor_name)
        panning = pannings.get(monitor_name)
        scaling_mode = scaling_modes.get(monitor_name)
        tear_free = tear_frees.get(monitor_name)

        if active:
            assert rotation is not None, "monitor active and rotation is None"
            assert reflection is not None, "monitor active and reflection is None"
            monitor_data = ActiveMonitorData(
                name=monitor_name, primary=primary,
                resolutions=resolutions, geometry=geometry,
                rotation=rotation, reflection=reflection,
                transformation=transformation, gamma=gamma,
                brightness=brightness, panning=panning,
                scaling_mode=scaling_mode, tear_free=tear_free
            )
        elif connected:
            monitor_data = InactiveMonitorData(
                name=monitor_name, primary=primary, resolutions=resolutions
            )
        else:
            monitor_data = DisconnectedMonitorData(
                name=monitor_name, primary=primary,
            )
        return monitor_data

    @staticmethod
    def __get_raw_headers_resolutions(xrandr_output_lines: List[str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        all_raw_headers: Dict[str, str] = {}
        all_raw_resolutions: Dict[str, List[str]] = {}
        monitor_name = ""
        for line in xrandr_output_lines[1:]:
            if "connected" in line:
                monitor_name = line.split(" ")[0]
                all_raw_headers[monitor_name] = line.strip()
                all_raw_resolutions[monitor_name] = []
                continue
            all_raw_resolutions[monitor_name].append(line.strip())

        return all_raw_headers, all_raw_resolutions

    @classmethod
    def __get_active_monitor_names(cls) -> List[str]:
        """Obtiene los monitores que están actualmente encendidos usando xrandr."""
        output = cls.__xrandr("--listactivemonitors").stdout
        cmd = f"echo -e \"{output}\" | tail -n+2 | awk 'NF{{print $NF}}' | xargs"
        result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
        if result.returncode != 0 or result.stdout is None:
            e = f"[!] Error: No se ha podido leer la información con '{cmd}'. Código de salida {result.returncode}"
            raise RuntimeError(e)
        return result.stdout.strip().split(" ")

    @classmethod
    def __parse_raw_header(cls, raw_header: str, active_monitor_names: List[str]) -> Tuple[
        bool, bool, bool, Geometry, Optional[Literal["normal", "left", "inverted", "right"]],
        Optional[Literal["normal", "x", "y", "xy"]]
    ]:
        """Extrae las distintas partes de la cabecera de un monitor (salida de xrandr sin argumentos).
        Además de la cabecera también hay que pasarle los nombres de monitores activos."""

        parts = raw_header.split(" ")

        # Datos básicos del monitor
        monitor_name = parts[0]
        active = monitor_name in active_monitor_names
        connected = True if parts[1] == "connected" else False
        primary = True if parts[2] == "primary" else False

        # Geometria
        try:
            geometry = cls.__parse_geometry(raw_header)
        except ValueError:
            geometry = None

        # Rotation
        rotation: Optional[Literal["normal", "left", "inverted", "right"]] = None
        if active:
            rotation = cls.__parse_rotation(raw_header)

        # Reflection
        reflection: Optional[Literal["normal", "x", "y", "xy"]] = None
        if active:
            reflection = cls.__parse_reflection(raw_header)

        return connected, active, primary, geometry, rotation, reflection

    @staticmethod
    def __parse_rotation(
            raw_header: str,
    ) -> Literal["normal", "left", "inverted", "right"]:
        pattern = r"(normal|left|inverted|right) ((X axis|Y axis|X and Y axis)\s)?\("
        match = re.search(pattern, raw_header)
        rotation: Literal["normal", "left", "inverted", "right"] = "normal"
        if match is None:
            return rotation

        match match.group(1):
            case "normal":
                rotation = "normal"
            case "left":
                rotation = "left"
            case "inverted":
                rotation = "inverted"
            case "right":
                rotation = "right"
            case _:
                raise DevError(f"Match de rotación inválido: {match.group(1)}")
        return rotation

    @staticmethod
    def __parse_reflection(raw_header: str) -> Optional[Literal["normal", "x", "y", "xy"]]:
        pattern = r"(?:normal|left|inverted|right) (X axis|Y axis|X and Y axis)\s\("
        match = re.search(pattern, raw_header)
        reflection: Literal["normal", "x", "y", "xy"] = "normal"
        if match is None:
            return reflection

        match match.group(1):
            case "X and Y axis":
                reflection = "xy"
            case "X axis":
                reflection = "x"
            case "Y axis":
                reflection = "y"
            case _:
                raise DevError(f"Match de translación inválido: {match.group(1)}")

        return reflection

    @classmethod
    def __parse_raw_monitor_resolutions(
            cls, monitor_name: str, active: bool, raw_monitor_resolutions: List[str]
    ) -> Optional[MonitorResolutions]:
        """Parsea todas las resoluciones de un monitor (si las hay, si no retornará None)"""
        if not raw_monitor_resolutions:
            return None

        current_res_index = None
        current_freq_index = None
        preferred_res_index = None
        preferred_freq_index = None

        resolutions: List[SingleResolution] = []
        for ri, raw_resolution_line in enumerate(raw_monitor_resolutions):
            single_resolution, get_current_freq_index, get_preferred_freq_index = (
                cls.__parse_single_raw_resolution(monitor_name, raw_resolution_line)
            )

            if get_current_freq_index is not None:
                current_res_index = ri
                current_freq_index = get_current_freq_index

            if get_preferred_freq_index is not None:
                preferred_res_index = ri
                preferred_freq_index = get_preferred_freq_index

            # Agregamos la resolución a la lista de resoluciones del monitor
            resolutions.append(single_resolution)

        current = None
        if active:
            if current_res_index is None or current_freq_index is None:
                raise DevError(f"??? {monitor_name}")
            current = (current_res_index, current_freq_index)

        preferred = None
        if preferred_res_index is not None:
            if preferred_freq_index is None:
                raise ValueError(
                    "No es posible que haya una resolución preferida sin una frecuencia preferida"
                )
            preferred = (preferred_res_index, preferred_freq_index)

        return MonitorResolutions(
            resolutions=resolutions, current=current, preferred=preferred
        )

    @staticmethod
    def __parse_single_raw_resolution(
            monitor_name: str,
            raw_resolution_line: str,
    ) -> Tuple[SingleResolution, Optional[int], Optional[int]]:
        """"Parsea una línea de resolución de un monitor"""
        # Resolución
        raw_resolution = raw_resolution_line.split(" ")[0]
        match = re.match(r"(\d+)x(\d+)", raw_resolution)
        if match is None:
            e = f"No se ha podido extraer la resolución de la linea"
            e += f" '{raw_resolution_line}' del monitor {monitor_name}"
            raise DevError(e)
        x, y = (int(match.group(i)) for i in range(1, 3))
        resolution = Vector2D(x=x, y=y)

        # Obtenemos las frecuencias junto con sus flags (* utilizado, + recomendado)
        all_freqs_line = raw_resolution_line.split(f"{raw_resolution} ")[1].strip()
        match = re.findall(r"\d+\.\d+\D*", all_freqs_line)
        if match is None:
            e = f"No se han podido extraer las frecuencias de la linea"
            e += f" '{raw_resolution_line}'"
            raise DevError(e)

        current_res: bool = "*" in raw_resolution_line
        preferred_res: bool = "+" in raw_resolution_line
        current_freq_index: Optional[int] = None
        preferred_freq_index: Optional[int] = None

        freqs: List = []
        for fi, raw_freq in enumerate(match):
            # Frecuencia Actual
            if "*" in raw_freq:
                current_freq_index = fi

            # Frecuencia preferida
            if "+" in raw_freq:
                preferred_freq_index = fi

            # Frecuencia (el valor float sin sus flags *+)
            match = re.match(r"\d+\.\d+", raw_freq)
            if match is None:
                e = f"No se ha podido extraer la frecuencia de '{raw_freq}'"
                raise DevError(e)

            freqs.append(float(match.group(0)))

        single_resolution = SingleResolution(resolution=resolution, freqs=freqs)

        if current_res and current_freq_index is None or \
                preferred_res and preferred_freq_index is None:
            raise DevError("???")

        return single_resolution, current_freq_index, preferred_freq_index

    @staticmethod
    def __parse_geometry(string: str) -> Geometry:
        """
        Extrae la geometría en el formato 1920x1080+0+0 de una string.
            Nota: +/- preceden a la posición dependiendo de si es positiva o negativa.
            El 0 también tiene que estar representado como +0

        En caso de no hacer match lanzará ValueError.
        """
        match = re.search(r"(\d+)x(\d+)([+\-]\d+)([+\-]\d+)", string)
        if match:
            w, h, x, y = (int(match.group(i)) for i in range(1, 5))
            return Geometry(w=w, h=h, x=x, y=y)

        raise ValueError(f"No se ha podido extraer la geometría de '{string}'")

    @classmethod
    def __get_active_raw_advanced_datas(
            cls, v_xrandr_output: str, active_monitor_names: List[str]
    ) -> Dict[str, str]:
        all_raw_advanced_datas: Dict[str, str] = cls.__separate_raw_advanced_datas(
            v_xrandr_output
        )
        active_raw_advanced_datas: Dict[str, str] = {
            n: d
            for n, d in all_raw_advanced_datas.items()
            if n in active_monitor_names
        }

        return active_raw_advanced_datas

    @staticmethod
    def __separate_raw_advanced_datas(v_xrandr_output: str) -> Dict[str, str]:
        """
        Clasifica la información del output de xrandr --verbose de los monitores
        creando un diccionario cuyas keys son los nombres de los monitores
        """
        v_xrandr_output_lines = v_xrandr_output.splitlines()

        raw_advanced_datas: Dict[str, List[str]] = {}
        monitor_name = ""
        for line in v_xrandr_output_lines[1:]:
            if "connected" in line:
                monitor_name = line.split(" ")[0]
                raw_advanced_datas[monitor_name] = [line]
                continue
            raw_advanced_datas[monitor_name].append(line)

        unified_advanced_datas: Dict[str, str] = {}
        for monitor_name, monitor_data in raw_advanced_datas.items():
            unified_advanced_datas[monitor_name] = "\n".join(monitor_data)

        return unified_advanced_datas

    @staticmethod
    def __get_monitors_transformation(
            active_raw_advanced_datas: Dict[str, str],
    ) -> Dict[str, MonitorTransformation]:
        def sep_row(row: str) -> Tuple[float, float, float]:
            """Separa una row que contiene valores de transformación en tres float"""
            a, b, c = row.split(" ")

            return float(a), float(b), float(c)

        monitor_transformations: Dict[str, MonitorTransformation] = {}
        for monitor_name, raw_a_data in active_raw_advanced_datas.items():
            cmd = 'echo "{}"'.format(raw_a_data)
            cmd += " | grep -A2 'Transform:' | sed 's/Transform://' | awk '{$1=$1; print}'"

            result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

            all_rows = result.stdout.splitlines()
            row1, row2, row3 = (all_rows[0], all_rows[1], all_rows[2])

            scale_x, rotate_y, translate_x = sep_row(row1)
            rotate_x, scale_y, translate_y = sep_row(row2)
            homogeneous_x, homogeneous_y, homogeneous_w = sep_row(row3)

            transformation = MonitorTransformation(
                scale=Vector2DF(x=scale_x, y=scale_y),
                rotation=Vector2DF(x=rotate_x, y=rotate_y),
                translation=Vector2DF(x=translate_x, y=translate_y),
                homogeneous=Vector3DF(x=homogeneous_x, y=homogeneous_y, z=homogeneous_w),
            )
            monitor_transformations[monitor_name] = transformation
        return monitor_transformations

    @staticmethod
    def __get_monitors_gammas(
            active_raw_advanced_datas: Dict[str, str],
    ) -> Dict[str, MonitorGamma]:
        gammas: Dict[str, MonitorGamma] = {}
        for monitor_name, raw_a_data in active_raw_advanced_datas.items():
            cmd = 'echo "{}"'.format(raw_a_data)
            cmd += "| grep 'Gamma:' | sed 's/Gamma://'"
            result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

            raw_gammas = result.stdout.strip().split(":")
            float_gammas = (float(g) for g in raw_gammas)
            r, g, b = float_gammas
            gammas[monitor_name] = MonitorGamma(r=r, g=g, b=b)

        return gammas

    @staticmethod
    def __get_monitors_brightnesses(active_raw_advanced_datas: Dict[str, str]):
        brightnesses: Dict[str, float] = {}
        for monitor_name, raw_a_data in active_raw_advanced_datas.items():
            cmd = 'echo "{}"'.format(raw_a_data)
            cmd += "| grep 'Brightness:' | sed 's/Brightness://'"
            result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

            brightness = float(result.stdout.strip())
            brightnesses[monitor_name] = brightness

        return brightnesses

    @classmethod
    def __get_monitors_pannings(
            cls, active_raw_advanced_datas: Dict[str, str]
    ) -> Dict[str, Optional[MonitorPanning]]:
        pannings: Dict[str, Optional[MonitorPanning]] = {}

        for monitor_name, raw_a_data in active_raw_advanced_datas.items():
            cmd = 'echo "{}"'.format(raw_a_data)
            cmd += "| grep 'Panning:' -A2 | awk '{print $2}'"
            result = subprocess.run(
                ["bash", "-c", cmd], capture_output=True, text=True
            )

            stdout = result.stdout.strip()
            if not stdout:
                pannings[monitor_name] = None
                continue

            raw_panning, raw_tracking, raw_borders = stdout.splitlines()

            try:
                panning = cls.__parse_geometry(raw_panning)
            except ValueError:
                pannings[monitor_name] = None
                continue

            tracking = None
            try:
                tracking = cls.__parse_geometry(raw_tracking)
            except ValueError:
                ...

            l, t, r, b = map(int, raw_borders.split("/"))
            borders = MonitorBorders(left=l, top=t, right=r, bottom=b)
            if (
                    borders.left == 0
                    and borders.top == 0
                    and borders.right == 0
                    and borders.bottom == 0
            ):
                borders = None

            pannings[monitor_name] = MonitorPanning(
                panning=panning,
                tracking=tracking,
                borders=borders,
            )
        return pannings

    @staticmethod
    def __get_scaling_modes(active_raw_advanced_datas: Dict[str, str]):
        scaling_modes: Dict[str, Optional[Literal["Full", "Center", "Full aspect"]]] = {}

        for monitor_name, raw_a_data in active_raw_advanced_datas.items():
            cmd = 'echo "{}"'.format(raw_a_data)
            cmd += "| grep 'scaling mode:' | sed 's/scaling mode://'"
            result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

            mode = result.stdout.strip()
            if not mode:
                scaling_modes[monitor_name] = None
            elif mode == "None":
                scaling_modes[monitor_name] = None
            elif mode == "Full":
                scaling_modes[monitor_name] = "Full"
            elif mode == "Center":
                scaling_modes[monitor_name] = "Center"
            elif mode == "Full aspect":
                scaling_modes[monitor_name] = "Full aspect"
            else:
                raise DevError(
                    "Se ha obtenido un valor desconocido de lo que se supone que es"
                    f" el scaling mode: '{mode}'"
                )

        return scaling_modes

    @classmethod
    def __get_tear_frees(cls, active_raw_advanced_datas: Dict[str, str]) -> Dict[
        str, Optional[Literal["off", "on", "auto"]]
    ]:
        tear_frees: Dict[str, Optional[Literal["off", "on", "auto"]]] = {}

        for monitor_name, raw_a_data in active_raw_advanced_datas.items():
            cmd = 'echo "{}"'.format(raw_a_data)
            cmd += "| grep TearFree: | sed 's/TearFree://'"
            result = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

            tfree = result.stdout.strip()
            if not tfree:
                tear_frees[monitor_name] = None
            elif tfree == "off":
                tear_frees[monitor_name] = "off"
            elif tfree == "on":
                tear_frees[monitor_name] = "on"
            elif tfree == "auto":
                tear_frees[monitor_name] = "auto"
            else:
                raise DevError(
                    "Se ha obtenido un valor desconocido de lo que se supone que es "
                    f"el tear free: '{tfree}'"
                )

        return tear_frees

    @staticmethod
    def __xrandr(args: str = "") -> subprocess.CompletedProcess:
        """Ejecuta el comando xrandr con los argumentos proporcionados y retorna el resultado."""
        cmd = f"xrandr {args}"
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or result.stdout is None:
            raise RuntimeError(
                f"[!] Error: No se ha podido leer la información con '{cmd}'. "
                f"Código de salida {result.returncode}"
            )
        return result
