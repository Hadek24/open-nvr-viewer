import os
import json
import tempfile

from src.config import get_config_dir

def ensure_config_dir():
    """
    Garantiza que exista el directorio de configuración.
    Devuelve su ruta.
    """

    config_dir = get_config_dir()

    os.makedirs(config_dir, exist_ok=True)
    secure_path(config_dir, is_directory=True)

    return config_dir

def save_json(file_path, data):
    """
    Guarda datos JSON mediante un archivo temporal
    y reemplazo atómico del archivo original.
    """

    directory = os.path.dirname(file_path)

    os.makedirs(directory, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            suffix=".tmp",
            delete=False
        ) as file:

            temporary_path = file.name

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

            file.flush()
            os.fsync(file.fileno())

        secure_path(temporary_path)
        os.replace(temporary_path, file_path)

    finally:
        if (
            temporary_path is not None
            and os.path.exists(temporary_path)
        ):
            os.remove(temporary_path)

def load_json(file_path):
    """
    Carga un archivo JSON y devuelve su contenido.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def file_exists(file_path):
    """
    Comprueba si existe un archivo.
    """

    return os.path.isfile(file_path)

def secure_path(path, is_directory=False):
    """
    Aplica permisos restrictivos cuando el sistema
    operativo utiliza permisos POSIX.

    En Windows se mantienen las ACL heredadas
    del directorio privado del usuario.
    """

    if os.name == "posix":
        permissions = 0o700 if is_directory else 0o600
        os.chmod(path, permissions)

def create_json_if_missing(file_path, initial_data):
    """
    Crea un archivo JSON con datos iniciales
    solamente si todavía no existe.
    """

    if file_exists(file_path):
        return False

    save_json(file_path, initial_data)

    return True
