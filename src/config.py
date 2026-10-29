import sys
import json
import os
import keyring

APP_NAME = "open-nvr-viewer"
KEYRING_SERVICE = "open-nvr-viewer"

CONFIG_DESCRIPTION = (
    "NINGUN PARAMETRO DEL ARCHIVO DEBERA SER MODIFICADO MANUALMENTE. "
    "CUALQUIER CAMBIO REALIZADO AQUI PODRIA CONLLEVAR QUE EL PROGRAMA "
    "DEJE DE FUNCIONAR. CUALQUIER ERROR INTRODUCIDO POR CAMBIOS MANUALES "
    "NO SERA CUBIERTO NI REPARADO, YA QUE EL PROGRAMA FUE HECHO PARA "
    "UTILIZARSE DESDE LA APLICACION. SI DESPUES DE UN CAMBIO MANUAL EL "
    "PROGRAMA FALLA, RECOMENDAMOS ELIMINAR EL CONFIG.JSON, ABRIR EL "
    "PROGRAMA Y CREAR UNA CONFIGURACION NUEVA."
)

# Built-in RTSP templates use neutral names and are managed by the application.
# Template variables are expanded by CameraWidget when each stream is opened.
BUILTIN_RTSP_TEMPLATES = [
    {
        "id": "builtin-rtsp-channel-code",
        "name": "RTSP Channel Code",
        "url_template": (
            "rtsp://{username}:{password}@{ip}:{port}/"
            "Streaming/channels/{channel_code}"
        ),
        "type": "builtin",
    },
    {
        "id": "builtin-rtsp-path-stream",
        "name": "RTSP Path Stream",
        "url_template": (
            "rtsp://{username}:{password}@{ip}:{port}/"
            "live/{channel}/{stream_index}"
        ),
        "type": "builtin",
    },
    {
        "id": "builtin-rtsp-query-stream",
        "name": "RTSP Query Stream",
        "url_template": (
            "rtsp://{username}:{password}@{ip}:{port}/stream"
            "?channel={channel}&subtype={stream_index}"
        ),
        "type": "builtin",
    },
    {
        "id": "builtin-rtsp-channel-suffix",
        "name": "RTSP Channel Suffix",
        "url_template": (
            "rtsp://{username}:{password}@{ip}:{port}/"
            "channels/{channel}{stream_padded}"
        ),
        "type": "builtin",
    },
]

def get_config_dir():
    """
    Devuelve el directorio donde se almacenará la configuración
    según el sistema operativo.
    """
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA")

        if not base_dir:
            base_dir = os.path.expanduser("~")

        return os.path.join(base_dir, APP_NAME)

    return os.path.join(
        os.path.expanduser("~"),
        ".config",
        APP_NAME
    )

def get_config_path():
    """
    Devuelve la ruta completa del archivo config.json.
    """
    return os.path.join(
        get_config_dir(),
        "config.json"
    )

def create_config():
    """
    Crea un config.json vacío con la estructura inicial.
    """
    config_dir = get_config_dir()
    config_path = get_config_path()

    os.makedirs(config_dir, exist_ok=True)

    config = {
        "description": CONFIG_DESCRIPTION,
        "active_profile": None,
        "profiles": {},
        "rtsp_templates": [template.copy() for template in BUILTIN_RTSP_TEMPLATES],
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def migrate_old_config(old_config):
    """
    Convierte el formato antiguo de config.json al nuevo formato
    basado en perfiles.
    """
    profile_id = "nvr-principal"

    new_config = {
        "description": CONFIG_DESCRIPTION,
        "active_profile": profile_id,
        "profiles": {
            profile_id: {
                "name": "NVR principal",
                **old_config
            }
        },
        "rtsp_templates": [template.copy() for template in BUILTIN_RTSP_TEMPLATES],
    }
    return new_config

def load_raw_config():
    """
    Carga el contenido completo de config.json sin resolver
    el perfil activo ni la contraseña.
    """
    config_path = get_config_path()

    if not os.path.exists(config_path):
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_rtsp_templates(config):
    """Add missing built-in RTSP templates and default profile references.

    User-defined templates remain in the same config.json file as profiles.
    Existing template definitions are not rewritten, including manual edits.
    """
    changed = False
    templates = config.get("rtsp_templates")

    if not isinstance(templates, list):
        templates = []
        config["rtsp_templates"] = templates
        changed = True

    existing_ids = {
        item.get("id")
        for item in templates
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    for builtin in BUILTIN_RTSP_TEMPLATES:
        if builtin["id"] not in existing_ids:
            templates.append(builtin.copy())
            changed = True

    profiles = config.get("profiles", {})
    if isinstance(profiles, dict):
        default_template_id = BUILTIN_RTSP_TEMPLATES[0]["id"]
        for profile in profiles.values():
            if isinstance(profile, dict) and not profile.get("RTSP_TEMPLATE_ID"):
                profile["RTSP_TEMPLATE_ID"] = default_template_id
                changed = True

    if not config.get("description"):
        config["description"] = CONFIG_DESCRIPTION
        changed = True

    return changed

def get_rtsp_templates():
    """Return the RTSP templates stored in config.json, or built-ins if absent."""
    config = load_raw_config()
    if not isinstance(config, dict):
        return [template.copy() for template in BUILTIN_RTSP_TEMPLATES]

    if ensure_rtsp_templates(config):
        save_raw_config(config)

    templates = config.get("rtsp_templates", [])
    return [item.copy() for item in templates if isinstance(item, dict)]

def load_config():
    """
    Carga la configuración del perfil activo y agrega la contraseña
    obtenida desde el keyring.
    """
    config = load_raw_config()

    if config is None:
        print("Error: No se encontró config.json")
        return None

    # Detectar formato antiguo y migrarlo.
    if "profiles" not in config:
        config = migrate_old_config(config)

        save_raw_config(config)

    if ensure_rtsp_templates(config):
        save_raw_config(config)

    active_profile = config.get("active_profile")
    profiles = config.get("profiles", {})

    if not active_profile or active_profile not in profiles:
        print("Error: No hay un perfil activo configurado")
        return None

    profile = profiles[active_profile].copy()

    # Resolve the selected template for the video player without persisting
    # the expanded value back into the profile.
    template_id = profile.get("RTSP_TEMPLATE_ID")
    templates = config.get("rtsp_templates", [])
    template = next(
        (item for item in templates
         if isinstance(item, dict) and item.get("id") == template_id),
        None,
    )
    if template:
        profile["RTSP_URL_TEMPLATE"] = template.get("url_template", "")

    password = get_nvr_password(active_profile)

    if password is not None:
        profile["NVR_PASS"] = password

    return profile

def save_raw_config(config):
    """
    Guarda directamente la estructura completa de configuración.
    """
    config_dir = get_config_dir()
    config_path = get_config_path()

    os.makedirs(config_dir, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(
            config,
            f,
            indent=4,
            ensure_ascii=False
        )

def save_config(config):
    """
    Guarda los cambios del perfil activo.

    La contraseña nunca se escribe en config.json.
    """
    raw_config = load_raw_config()

    if raw_config is None:
        print("Error: No se encontró config.json")
        return False

    # Si todavía existe el formato antiguo, migrarlo primero.
    if "profiles" not in raw_config:
        raw_config = migrate_old_config(raw_config)

    active_profile = raw_config.get("active_profile")

    if not active_profile:
        print("Error: No hay un perfil activo configurado")
        return False

    config_to_save = config.copy()

    # Runtime-only values are resolved from the selected template and keyring.
    config_to_save.pop("RTSP_URL_TEMPLATE", None)

    # Nunca guardar la contraseña en config.json.
    password = config_to_save.pop("NVR_PASS", None)

    raw_config["profiles"][active_profile] = config_to_save

    save_raw_config(raw_config)

    # Si recibimos una contraseña, actualizar el keyring.
    if password:
        set_nvr_password(active_profile, password)

    return True

def delete_config():
    """
    Elimina el archivo de configuracion.

    Las contraseñas tambien se eliman del sistema.
    """
    config = load_raw_config()

    if config is None:
        return False

    profiles = config.get("profiles", {})

    # Eliminar las contraseñas asociadas a los perfiles
    for profile_id in profiles:
        try:
            keyring.delete_password(KEYRING_SERVICE, profile_id)
        except Exception:
            pass

    # Eliminar la credencial antigua, si todavía existiera
    try:
        keyring.delete_password(KEYRING_SERVICE, "nvr")
    except Exception:
        pass

    config_path = get_config_path()

    try:
        os.remove(config_path)
    except OSError:
        return False

    return True

def get_nvr_password(profile_name):
    """
    Obtiene la contraseña del perfil desde el keyring.
    """
    try:
        password = keyring.get_password(
            KEYRING_SERVICE,
            profile_name
        )

        if password is not None:
            return password

        # Compatibilidad con la configuración anterior.
        if profile_name == "nvr-principal":
            old_password = keyring.get_password(
                KEYRING_SERVICE,
                "nvr"
            )

            if old_password is not None:
                # Migrar la contraseña al nuevo identificador.
                keyring.set_password(
                    KEYRING_SERVICE,
                    profile_name,
                    old_password
                )

                return old_password

        return None

    except Exception:
        return None

def get_nvr_password_for_backup(profile_name):
    """Read a profile password for backup, allowing errors to propagate."""

    password = keyring.get_password(KEYRING_SERVICE, profile_name)

    if password is not None:
        return password

    # Preserve the legacy credential migration for the main profile.
    if profile_name == "nvr-principal":
        old_password = keyring.get_password(KEYRING_SERVICE, "nvr")

        if old_password is not None:
            keyring.set_password(
                KEYRING_SERVICE,
                profile_name,
                old_password,
            )
            return old_password

    return None

def set_nvr_password(profile_name, password):
    """
    Guarda la contraseña del perfil en el keyring.
    """
    try:
        keyring.set_password(
            KEYRING_SERVICE,
            profile_name,
            password
        )
        return True
    except Exception:
        return False

def get_default_profile():
    """
    Devuelve una configuración base para crear un nuevo perfil.
    """
    return {
        "name": "Nuevo NVR",
        "NVR_USER": "admin",
        "NVR_IP": "",
        "NVR_PORT": "554",
        "TOTAL_CHANNELS": 16,
        "LAST_GRID_SIZE": 2,
        "RTSP_TEMPLATE_ID": BUILTIN_RTSP_TEMPLATES[0]["id"],
        "GRID_MAPPINGS": {
            "1": ["Vacío"],
            "2": ["Vacío", "Vacío", "Vacío", "Vacío"],
            "3": ["Vacío"] * 9,
            "4": ["Vacío"] * 16
        }
    }

def generate_profile_id(profile_name):
    """
    Genera un ID interno a partir del nombre del perfil.
    """
    profile_id = profile_name.strip().lower()
    profile_id = profile_id.replace(" ", "-")

    return profile_id

def validate_profile(profile_name, nvr_user, nvr_ip, nvr_port, nvr_channels):
    """
    Valida los datos básicos de un perfil.
    Devuelve:
        (True, None) si todo es correcto
        (False, mensaje) si hay un error
    """

    if not profile_name.strip():
        return False, "El nombre del perfil es obligatorio"

    if not nvr_user.strip():
        return False, "El usuario del NVR es obligatorio"

    # Validar IP
    ip_parts = nvr_ip.strip().split(".")

    if len(ip_parts) != 4:
        return False, "La IP debe tener 4 octetos"

    try:
        ip_parts = [int(part) for part in ip_parts]
    except ValueError:
        return False, "La IP solo puede contener números"

    if any(part < 1 or part > 255 for part in ip_parts):
        return False, "Cada octeto debe estar entre 1 y 255"

    # Validar puerto
    try:
        port = int(nvr_port)
    except ValueError:
        return False, "El puerto debe ser un número"

    if port < 1 or port > 65535:
        return False, "El puerto debe estar entre 1 y 65535"

    # Validar cantidad de canales
    try:
        channels = int(nvr_channels)
    except ValueError:
        return False, "Los canales deben ser un número"

    if channels < 1 or channels > 48:
        return False, "Los canales deben estar entre 1 y 48"

    return True, None

def get_profiles():
    """
    Devuelve los perfiles configurados.
    """
    config = load_raw_config()

    if config is None:
        return {}

    return config.get("profiles", {})

def get_active_profile():
    """
    Devuelve el identificador del perfil activo.
    """
    config = load_raw_config()

    if config is None:
        return None

    return config.get("active_profile")

def set_active_profile(profile_name):
    """
    Establece un perfil como activo.
    """
    config = load_raw_config()

    if config is None:
        return False

    profiles = config.get("profiles", {})

    if profile_name not in profiles:
        return False

    config["active_profile"] = profile_name

    save_raw_config(config)

    return True

def create_profile(profile_id, profile_data):
    """
    Crea un nuevo perfil.

    El perfil no pasa a ser activo automáticamente.
    """
    config = load_raw_config()

    if config is None:
        return False

    profiles = config.setdefault("profiles", {})

    # No permitir sobrescribir un perfil existente.
    if profile_id in profiles:
        return False

    profiles[profile_id] = profile_data

    save_raw_config(config)

    return True

def update_profile(profile_id, profile_data):
    """
    Actualiza los datos de un perfil existente sin cambiar su ID
    ni eliminar los parámetros que no se están modificando.
    """
    config = load_raw_config()

    if config is None:
        return False

    profiles = config.get("profiles", {})

    if profile_id not in profiles:
        return False

    # Actualizar los campos recibidos y conservar los demás.
    profiles[profile_id].update(profile_data)

    save_raw_config(config)

    return True

def delete_profile(profile_id):
    """
    Elimina un perfil existente.
    No permite eliminar el perfil actualmente activo.
    """
    config = load_raw_config()

    if config is None:
        return False

    profiles = config.get("profiles", {})
    active_profile = config.get("active_profile")

    if profile_id not in profiles:
        return False

    if profile_id == active_profile:
        return False

    del profiles[profile_id]

    save_raw_config(config)

    try:
        keyring.delete_password(KEYRING_SERVICE, profile_id)
    except Exception:
        pass

    return True
