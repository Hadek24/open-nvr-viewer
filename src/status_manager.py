import json
import os
from copy import deepcopy
from src.config import get_config_dir

class StatusManager:

    def __init__(self):
        self.config_dir = get_config_dir()
        os.makedirs(self.config_dir, exist_ok=True)

        self.status_path = os.path.join(
            self.config_dir,
            "status.json"
        )

        self._initialize_file()

    def _initialize_file(self):
        """
        Crea status.json si todavía no existe.
        """

        if not os.path.exists(self.status_path):
            initial_data = {
                "version": 1,
                "users": {}
            }

            self._save_data(initial_data)

    def load_status(self):
        """
        Carga y valida la estructura general de status.json.
        """

        with open(self.status_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid status.json structure")

        if data.get("version") != 1:
            raise ValueError("Unsupported status.json version")

        users = data.get("users")

        if not isinstance(users, dict):
            raise ValueError("Invalid users structure in status.json")

        for user_id, user_data in users.items():

            if not isinstance(user_id, str) or not user_id.strip():
                raise ValueError("Invalid user ID in status.json")

            if not isinstance(user_data, dict):
                raise ValueError(
                    f"Invalid status data for user: {user_id}"
                )

            profiles = user_data.get("profiles")

            if not isinstance(profiles, dict):
                raise ValueError(
                    f"Invalid profiles structure for user: {user_id}"
                )

            for profile_id, profile_data in profiles.items():

                if not isinstance(profile_id, str) or not profile_id.strip():
                    raise ValueError("Invalid profile ID in status.json")

                self._validate_profile_status(profile_data)

        return data

    def _save_data(self, data):
        """
        Guarda status.json mediante escritura temporal.
        """

        temporary_path = self.status_path + ".tmp"

        try:
            with open(
                temporary_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.status_path)

        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def _default_profile_status(self):
        """
        Devuelve el estado visual inicial de un perfil.
        """

        return {
            "last_grid_size": 2,
            "grid_mappings": {
                "1": ["Vacío"],
                "2": ["Vacío"] * 4,
                "3": ["Vacío"] * 9,
                "4": ["Vacío"] * 16
            }
        }

    def _validate_profile_status(self, profile_data):
        """
        Valida el estado visual correspondiente a un perfil.
        """

        if not isinstance(profile_data, dict):
            raise ValueError("Invalid profile status structure")

        last_grid_size = profile_data.get("last_grid_size")

        if (
            not isinstance(last_grid_size, int)
            or isinstance(last_grid_size, bool)
            or last_grid_size not in (1, 2, 3, 4)
        ):
            raise ValueError("Invalid last_grid_size")

        grid_mappings = profile_data.get("grid_mappings")

        if not isinstance(grid_mappings, dict):
            raise ValueError("Invalid grid_mappings structure")

        for size in ("1", "2", "3", "4"):

            mapping = grid_mappings.get(size)

            if not isinstance(mapping, list):
                raise ValueError(
                    f"Invalid grid mapping for size {size}"
                )

            expected_slots = int(size) ** 2

            if len(mapping) != expected_slots:
                raise ValueError(
                    f"Invalid number of slots for grid size {size}"
                )

            if not all(isinstance(channel, str) for channel in mapping):
                raise ValueError(
                    f"Invalid channel mapping for grid size {size}"
                )

        return True

    def get_profile_status(self, user_id, profile_id):
        """
        Devuelve el estado visual de un usuario para un perfil.

        Si todavía no existe un estado guardado, devuelve valores
        predeterminados sin modificar el archivo.
        """

        self._validate_identifiers(user_id, profile_id)

        data = self.load_status()

        user_data = data["users"].get(user_id, {})
        profiles = user_data.get("profiles", {})

        profile_data = profiles.get(profile_id)

        if profile_data is None:
            return self._default_profile_status()

        self._validate_profile_status(profile_data)

        return deepcopy(profile_data)

    def get_grid_mapping(self, user_id, profile_id, grid_size):
        """
        Devuelve las cámaras asignadas a un tamaño de grilla.
        """

        self._validate_grid_size(grid_size)

        profile_status = self.get_profile_status(
            user_id,
            profile_id
        )

        return list(
            profile_status["grid_mappings"][str(grid_size)]
        )

    def save_grid_state(
        self,
        user_id,
        profile_id,
        grid_size,
        mapping
    ):
        """
        Guarda el tamaño de grilla seleccionado y su asignación
        de cámaras para un usuario y perfil determinados.
        """

        self._validate_identifiers(user_id, profile_id)
        self._validate_grid_size(grid_size)

        if not isinstance(mapping, list):
            raise ValueError("Grid mapping must be a list")

        expected_slots = grid_size ** 2

        if len(mapping) != expected_slots:
            raise ValueError(
                f"Grid size {grid_size} requires "
                f"{expected_slots} camera slots"
            )

        if not all(isinstance(channel, str) for channel in mapping):
            raise ValueError("Invalid camera mapping")

        data = self.load_status()

        users = data["users"]

        if user_id not in users:
            users[user_id] = {
                "profiles": {}
            }

        profiles = users[user_id]["profiles"]

        if profile_id not in profiles:
            profiles[profile_id] = self._default_profile_status()

        profile_data = profiles[profile_id]

        profile_data["last_grid_size"] = grid_size
        profile_data["grid_mappings"][str(grid_size)] = list(mapping)

        self._save_data(data)

    def _validate_identifiers(self, user_id, profile_id):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user ID")

        if not isinstance(profile_id, str) or not profile_id.strip():
            raise ValueError("Invalid profile ID")

    def _validate_grid_size(self, grid_size):
        if (
            not isinstance(grid_size, int)
            or isinstance(grid_size, bool)
            or grid_size not in (1, 2, 3, 4)
        ):
            raise ValueError("Invalid grid size")

