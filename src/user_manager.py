import os
import uuid
import shutil
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError
)
from src.config import get_profiles
from src.storage import (
    ensure_config_dir,
    save_json,
    load_json,
    create_json_if_missing,
    secure_path
)

class UserManager:

    def __init__(self):
        self.config_dir = ensure_config_dir()

        self.users_path = os.path.join(
            self.config_dir,
            "users.json"
        )

        self._initialize_file()

    def _initialize_file(self):
        """
        Crea users.json si todavía no existe.
        """

        initial_data = {
            "version": 2,
            "users": {}
        }

        create_json_if_missing(
            self.users_path,
            initial_data
        )

    def _migrate_v1_to_v2(self, data):
        users = data.get("users")

        if not isinstance(users, dict):
            raise ValueError("Invalid users.json structure")

        backup_path = self.users_path + ".v1.bak"

        if os.path.exists(backup_path):
            raise ValueError(
                "Migration backup already exists. "
                "Manual verification is required."
            )

        migrated_data = {
            "version": 2,
            "users": {}
        }

        # Validate every existing user before migration
        for username, user_data in users.items():

            try:
                self._validate_username(username)
            except (AttributeError, ValueError):
                raise ValueError("Invalid username in users.json")

            if not isinstance(user_data, dict):
                raise ValueError(f"Invalid data for user: {username}")

            password_hash = user_data.get("password_hash")

            try:
                self._validate_password_hash(password_hash)
            except ValueError:
                raise ValueError(
                    f"Invalid password hash for user: {username}"
                )

            if user_data.get("role") not in (
                "Administrator",
                "Viewer"
            ):
                raise ValueError(f"Invalid role for user: {username}")

            assigned_profile = user_data.get("assigned_profile")

            if (
                not isinstance(assigned_profile, str)
                or not assigned_profile.strip()
            ):
                raise ValueError(
                    f"Invalid assigned profile for user: {username}"
                )

            if not isinstance(user_data.get("enabled"), bool):
                raise ValueError(
                    f"Invalid enabled status for user: {username}"
                )

            migrated_user = user_data.copy()
            migrated_user["id"] = str(uuid.uuid4())

            migrated_data["users"][username] = migrated_user

        # Preserve original file only after all users are validated
        shutil.copy2(self.users_path, backup_path)
        secure_path(backup_path)

        # Atomic replacement through _save_data()
        self._save_data(migrated_data)

        return migrated_data

    def load_users(self):
        """
        Carga users.json y valida su estructura e integridad.
        """

        data = load_json(self.users_path)

        if not isinstance(data, dict):
            raise ValueError("Invalid users.json structure")

        version = data.get("version")

        if version == 1:
            data = self._migrate_v1_to_v2(data)

        elif version != 2:
            raise ValueError("Unsupported users.json version")

        users = data.get("users")

        if not isinstance(users, dict):
            raise ValueError("Invalid users.json structure")

        validated_usernames = set()
        validated_ids = set()

        for username, user in users.items():

            # Validate username type and format
            if not isinstance(username, str):
                raise ValueError("Invalid username in users.json")

            try:
                validated_username = self._validate_username(username)
            except (AttributeError, ValueError):
                raise ValueError("Invalid username in users.json")

            if validated_username != username:
                raise ValueError(
                    f"Username is not normalized: {username}"
                )

            # Detect case-insensitive duplicate usernames
            normalized_username = username.casefold()

            if normalized_username in validated_usernames:
                raise ValueError(
                    f"Duplicate username detected: {username}"
                )

            validated_usernames.add(normalized_username)

            # Validate user structure
            if not isinstance(user, dict):
                raise ValueError(f"Invalid data for user: {username}")

            # Validate UUID
            user_id = user.get("id")

            try:
                parsed_id = uuid.UUID(user_id)
            except (ValueError, TypeError, AttributeError):
                raise ValueError(
                    f"Invalid user ID for user: {username}"
                )

            # Detect duplicate UUIDs
            if parsed_id in validated_ids:
                raise ValueError(
                    f"Duplicate user ID detected: {username}"
                )

            validated_ids.add(parsed_id)

            # Validate password hash
            password_hash = user.get("password_hash")

            try:
                self._validate_password_hash(password_hash)
            except ValueError:
                raise ValueError(
                    f"Invalid password hash for user: {username}"
                )

            # Validate role
            role = user.get("role")

            if role not in (
                "Superadmin",
                "Administrator",
                "Viewer"
            ):
                raise ValueError(
                    f"Invalid role for user: {username}"
                )

            # Validate assigned profile
            assigned_profile = user.get("assigned_profile")

            if role == "Superadmin":
                if assigned_profile is not None:
                    raise ValueError(
                        f"Superadmin cannot have an assigned profile: {username}"
                    )

            else:
                if (
                    not isinstance(assigned_profile, str)
                    or not assigned_profile.strip()
                ):
                    raise ValueError(
                        f"Invalid assigned profile for user: {username}"
                    )

            # Validate enabled status
            if not isinstance(user.get("enabled"), bool):
                raise ValueError(
                    f"Invalid enabled status for user: {username}"
                )

        return data

    def get_administration_state(self):
        """
        Comprueba el estado administrativo de la instalación.

        No modifica ni guarda datos.
        Los errores de lectura o estructura se propagan.
        """

        data = self.load_users()
        users = data["users"]

        # Instalación nueva: todavía no hay cuentas.
        if not users:
            return {
                "status": "first_run",
                "administration_fully_provisioned": False
            }

        superadmins = [
            user
            for user in users.values()
            if user["role"] == "Superadmin"
        ]

        # Si todavía no existe Superadmin, se debe completar el alta inicial.
        # Esto también cubre instalaciones anteriores que ya tenían
        # Administrators creados antes de incorporar este rol.
        if len(superadmins) == 0:
            return {
                "status": "bootstrap_required",
                "administration_fully_provisioned": False
            }

        # Más de un Superadmin indica una inconsistencia que no se corrige
        # automáticamente para evitar alterar cuentas privilegiadas.
        if len(superadmins) > 1:
            return {
                "status": "recovery_required",
                "administration_fully_provisioned": False
            }

        superadmin = superadmins[0]

        # El Superadmin debe estar habilitado.
        if not superadmin["enabled"]:
            return {
                "status": "recovery_required",
                "administration_fully_provisioned": False
            }

        # La ausencia de Administrators activos no impide arrancar.
        enabled_administrators = [
            user
            for user in users.values()
            if (
                user["role"] == "Administrator"
                and user["enabled"]
            )
        ]

        return {
            "status": "ready",
            "administration_fully_provisioned": bool(
                enabled_administrators
            )
        }

    def create_initial_superadmin(self, username, password):
        """Create the installation's first Superadmin without changing existing users."""
        data = self.load_users()
        users = data["users"]

        if any(user.get("role") == "Superadmin" for user in users.values()):
            raise ValueError("A Superadmin account already exists")

        username = self._validate_username(username)
        if not isinstance(password, str) or not password.strip():
            raise ValueError("Password is required")
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters")

        if any(name.casefold() == username.casefold() for name in users):
            raise ValueError("Username already exists")

        users[username] = {
            "id": str(uuid.uuid4()),
            "password_hash": self.hash_password(password),
            "role": "Superadmin",
            "assigned_profile": None,
            "enabled": True,
        }
        self._save_data(data)
        return {
            "id": users[username]["id"],
            "username": username,
            "role": "Superadmin",
            "assigned_profile": None,
            "enabled": True,
        }

    def authenticate(self, username, password):
        """Authenticate a local account and return a safe session record."""
        if not isinstance(username, str) or not isinstance(password, str):
            return None

        data = self.load_users()
        match = next(
            ((name, user) for name, user in data["users"].items()
             if name.casefold() == username.strip().casefold()),
            None,
        )
        if match is None:
            return None

        stored_username, user = match
        if not user.get("enabled", False):
            return None
        if not self.verify_password(password, user.get("password_hash", "")):
            return None

        return {
            "id": user["id"],
            "username": stored_username,
            "role": user["role"],
            "assigned_profile": user["assigned_profile"],
        }

    def list_users(self):
        data = self.load_users()
        users = []

        for username, user_data in data["users"].items():
            users.append({
                "id": user_data["id"],
                "username": username,
                "role": user_data["role"],
                "assigned_profile": user_data["assigned_profile"],
                "enabled": user_data["enabled"]
            })

        return users

    def _get_actor(self, actor_id):
        # Validate actor ID format
        if not isinstance(actor_id, str):
            raise PermissionError("Invalid actor identity")

        try:
            actor_uuid = uuid.UUID(actor_id)
        except (ValueError, TypeError, AttributeError):
            raise PermissionError("Invalid actor identity")

        # Load current users
        data = self.load_users()
        users = data["users"]

        # Find actor by UUID
        actor = None

        for username, user_data in users.items():
            if uuid.UUID(user_data["id"]) == actor_uuid:

                if actor is not None:
                    raise ValueError(
                        "Duplicate user ID detected in users.json"
                    )

                actor = {
                    "id": user_data["id"],
                    "username": username,
                    "role": user_data["role"],
                    "assigned_profile": user_data["assigned_profile"],
                    "enabled": user_data["enabled"]
                }

        # Reject unknown or disabled actors
        if actor is None or not actor["enabled"]:
            raise PermissionError(
                "Actor does not exist or is disabled"
            )

        return actor

    def _authorize_add_user(self, actor, role):
        # Validate requested role
        role = self._validate_role(role)

        if role == "Superadmin":
            raise PermissionError(
                "Superadmin cannot be created through normal user registration"
            )

        # Only Superadmin and Administrator can create users
        if actor["role"] not in (
            "Superadmin",
            "Administrator"
        ):
            raise PermissionError(
                "You do not have permission to create users"
            )

        return True

    def _authorize_edit_user(self, actor, target_user):
        # Protect Superadmin
        if target_user["role"] == "Superadmin":
            raise PermissionError(
                "Superadmin cannot be modified through user administration"
            )

        # Prevent users from modifying their own account
        if actor["id"] == target_user["id"]:
            raise PermissionError(
                "Users cannot modify their own account through user administration"
            )

        # Superadmin can modify Administrators and Viewers
        if actor["role"] == "Superadmin":
            return True

        # Administrator can only modify Viewers
        if actor["role"] == "Administrator":
            if target_user["role"] == "Viewer":
                return True

            raise PermissionError(
                "Administrators cannot modify other Administrators"
            )

        # Viewers cannot modify users
        raise PermissionError(
            "You do not have permission to modify users"
        )

    def _authorize_delete_user(self, actor, target_user):

        # Protect Superadmin
        if target_user["role"] == "Superadmin":
            raise PermissionError(
                "Superadmin cannot be deleted through user administration"
            )

        # Prevent users from deleting their own account
        if actor["id"] == target_user["id"]:
            raise PermissionError(
                "Users cannot delete their own account"
            )

        # Superadmin can delete Administrators and Viewers
        if actor["role"] == "Superadmin":
            return True

        # Administrator can only delete Viewers
        if actor["role"] == "Administrator":
            if target_user["role"] == "Viewer":
                return True

            raise PermissionError(
                "Administrators cannot delete other Administrators"
            )

        # Viewers cannot delete users
        raise PermissionError(
            "You do not have permission to delete users"
        )

    def _save_data(self, data):
        """
        Guarda users.json mediante el sistema centralizado
        de almacenamiento.
        """

        save_json(self.users_path, data)

    def hash_password(self, password):
        hasher = PasswordHasher()
        return hasher.hash(password)

    def verify_password(self, password, password_hash):
        hasher = PasswordHasher()

        try:
            return hasher.verify(password_hash, password)

        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def add_user(
        self,
        actor_id,
        username,
        password,
        role,
        assigned_profile,
        enabled=True
        ):

        # Identify and validate actor
        actor = self._get_actor(actor_id)

        # Check creation permissions
        self._authorize_add_user(actor, role)

        # Validate user data
        username = self._validate_username(username)
        role = self._validate_role(role)
        assigned_profile = self._validate_assigned_profile(assigned_profile)
        enabled = self._validate_enabled(enabled)

        # Basic password validation
        if not isinstance(password, str) or not password.strip():
            raise ValueError("Password is required")

        if len(password) < 8:
            raise ValueError(
                "Password must contain at least 8 characters"
            )

        # Load current users
        data = self.load_users()
        users = data["users"]

        # Prevent duplicate usernames (case-insensitive)
        for existing_username in users:
            if existing_username.casefold() == username.casefold():
                raise ValueError("Username already exists")

        # Create user record
        users[username] = {
            "id": str(uuid.uuid4()),
            "password_hash": self.hash_password(password),
            "role": role,
            "assigned_profile": assigned_profile,
            "enabled": enabled
        }

        # Persist changes
        self._save_data(data)

    def edit_user(
        self,
        actor_id,
        username,
        new_username,
        password,
        role,
        assigned_profile,
        enabled=True
        ):

        # Identify and validate actor
        actor = self._get_actor(actor_id)

        # Load current users
        data = self.load_users()
        users = data["users"]

        # Check that the target user exists
        if username not in users:
            raise ValueError("User does not exist")

        user_data = users[username]

        # Check modification permissions
        self._authorize_edit_user(actor, user_data)

        # Validate role
        role = self._validate_role(role)

        if role == "Superadmin":
            raise ValueError(
                "Users cannot be promoted to Superadmin through normal editing"
            )

        # Validate remaining fields
        new_username = self._validate_username(new_username)
        assigned_profile = self._validate_assigned_profile(assigned_profile)
        enabled = self._validate_enabled(enabled)

        # Validate password if provided
        if password is not None:
            if not isinstance(password, str):
                raise ValueError("Invalid password")

            if password.strip() and len(password) < 8:
                raise ValueError(
                    "Password must contain at least 8 characters"
                )

        # Prevent duplicate usernames
        for existing_username in users:
            if existing_username != username:
                if existing_username.casefold() == new_username.casefold():
                    raise ValueError("Username already exists")

        # Prevent removing the last active administrator
        was_enabled_admin = (
            user_data.get("role") == "Administrator"
            and user_data.get("enabled", False)
        )

        will_be_enabled_admin = (
            role == "Administrator"
            and enabled
        )

        if (
            was_enabled_admin
            and not will_be_enabled_admin
            and self._count_enabled_administrators(users) <= 1
        ):
            raise ValueError(
                "Cannot disable or downgrade the last active administrator"
            )

        # Update password if provided
        if password and password.strip():
            user_data["password_hash"] = self.hash_password(password)

        # Update user properties
        user_data["role"] = role
        user_data["assigned_profile"] = assigned_profile
        user_data["enabled"] = enabled

        # Handle username changes
        if new_username != username:
            del users[username]
            users[new_username] = user_data

        # Persist changes
        self._save_data(data)

    def change_own_credentials(
        self,
        actor_id,
        current_password,
        new_password
        ):

        # Identify and validate actor
        actor = self._get_actor(actor_id)

        # Only Superadmin and Administrator can change passwords
        if actor["role"] not in (
            "Superadmin",
            "Administrator"
        ):
            raise PermissionError(
                "You do not have permission to change credentials"
            )

        # Validate current password
        if (
            not isinstance(current_password, str)
            or not current_password
        ):
            raise ValueError("Current password is required")

        # Validate new password
        if (
            not isinstance(new_password, str)
            or not new_password.strip()
        ):
            raise ValueError("New password is required")

        if len(new_password) < 8:
            raise ValueError(
                "New password must contain at least 8 characters"
            )

        # Load current users
        data = self.load_users()
        users = data["users"]

        # Find authenticated user
        username = actor["username"]
        user_data = users[username]

        # Verify current password
        if not self.verify_password(
            current_password,
            user_data["password_hash"]
        ):
            raise PermissionError(
                "Current password is incorrect"
            )

        # Generate new password hash
        user_data["password_hash"] = self.hash_password(
            new_password
        )

        # Persist changes
        self._save_data(data)

    def _validate_username(self, username):

        if not isinstance(username, str):
            raise ValueError("Username must be a string")

        username = username.strip()

        if not username:
            raise ValueError("Username is required")

        if len(username) > 32:
            raise ValueError("Username cannot exceed 32 characters")

        if not username[0].isalnum():
            raise ValueError(
                "Username must start with a letter or number"
            )

        if not all(
            char.isalnum() or char in "._-"
            for char in username
        ):
            raise ValueError("Username contains invalid characters")

        return username

    def _count_enabled_administrators(self, users):
        return sum(
            1
            for user in users.values()
            if user.get("role") == "Administrator"
            and user.get("enabled", False)
        )

    def delete_user(self, actor_id, username):

        # Identify and validate actor
        actor = self._get_actor(actor_id)

        # Load current users
        data = self.load_users()
        users = data["users"]

        # Check that the target user exists
        if username not in users:
            raise ValueError("User does not exist")

        user_data = users[username]

        # Check deletion permissions
        self._authorize_delete_user(actor, user_data)

        # Prevent deleting the last active administrator
        if (
            user_data.get("role") == "Administrator"
            and user_data.get("enabled", False)
            and self._count_enabled_administrators(users) <= 1
        ):
            raise ValueError(
                "Cannot delete the last active administrator"
            )

        # Delete user
        del users[username]

        # Persist changes
        self._save_data(data)

    def _validate_assigned_profile(self, assigned_profile):
        if not isinstance(assigned_profile, str):
            raise ValueError("Assigned profile is required")

        assigned_profile = assigned_profile.strip()

        if not assigned_profile:
            raise ValueError("Assigned profile is required")

        profiles = get_profiles()

        if assigned_profile not in profiles:
            raise ValueError("Assigned profile does not exist")

        return assigned_profile

    def _validate_enabled(self, enabled):
        if not isinstance(enabled, bool):
            raise ValueError("Enabled status must be a boolean")

        return enabled

    def _validate_role(self, role):
        if role not in (
            "Superadmin",
            "Administrator",
            "Viewer"
        ):
            raise ValueError("Invalid user role")

        return role

    def _validate_password_hash(self, password_hash):
        if not isinstance(password_hash, str) or not password_hash.strip():
            raise ValueError("Invalid password hash")

        try:
            PasswordHasher().check_needs_rehash(password_hash)

        except InvalidHashError:
            raise ValueError("Invalid password hash")

        return password_hash
