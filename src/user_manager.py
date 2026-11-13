import json
import os
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError
)
from src.config import get_config_dir, get_profiles

class UserManager:

    def __init__(self):
        self.config_dir = get_config_dir()
        os.makedirs(self.config_dir, exist_ok=True)

        self.users_path = os.path.join(
            self.config_dir,
            "users.json"
        )

        self._initialize_file()

    def _initialize_file(self):
        if not os.path.exists(self.users_path):
            initial_data = {
                "version": 1,
                "users": {}
            }

            self._save_data(initial_data)

    def load_users(self):
        with open(self.users_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid users.json structure")

        if data.get("version") != 1:
            raise ValueError("Unsupported users.json version")

        users = data.get("users")

        if not isinstance(users, dict):
            raise ValueError("Invalid users.json structure")

        for username, user in users.items():

            try:
                self._validate_username(username)
            except (AttributeError, ValueError):
                raise ValueError("Invalid username in users.json")

            if not isinstance(user, dict):
                raise ValueError(f"Invalid data for user: {username}")

            password_hash = user.get("password_hash")

            try:
                self._validate_password_hash(password_hash)
            except ValueError:
                raise ValueError(f"Invalid password hash for user: {username}")

            if user.get("role") not in ("Administrator", "Viewer"):
                raise ValueError(f"Invalid role for user: {username}")

            assigned_profile = user.get("assigned_profile")

            if not isinstance(assigned_profile, str) or not assigned_profile.strip():
                raise ValueError(f"Invalid assigned profile for user: {username}")

            if not isinstance(user.get("enabled"), bool):
                raise ValueError(f"Invalid enabled status for user: {username}")

        return data

    def list_users(self):
        data = self.load_users()
        users = []

        for username, user_data in data["users"].items():
            users.append({
                "username": username,
                "role": user_data["role"],
                "assigned_profile": user_data["assigned_profile"],
                "enabled": user_data["enabled"]
            })

        return users

    def _save_data(self, data):
        temporary_path = self.users_path + ".tmp"

        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        os.replace(temporary_path, self.users_path)

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
        username,
        password,
        role,
        assigned_profile,
        enabled=True
        ):

        username = self._validate_username(username)
        assigned_profile = self._validate_assigned_profile(assigned_profile)
        enabled = self._validate_enabled(enabled)

        # Basic validation
        if not password.strip():
            raise ValueError("Password is required")

        if len(password) < 8:
            raise ValueError(
                "Password must contain at least 8 characters"
            )

        role = self._validate_role(role)

        if not assigned_profile:
            raise ValueError("Assigned profile is required")

        # Load current users
        data = self.load_users()
        users = data["users"]

        # Prevent duplicate usernames (case-insensitive)
        for existing_username in users:
            if existing_username.casefold() == username.casefold():
                raise ValueError("Username already exists")

        # Create user record
        users[username] = {
            "password_hash": self.hash_password(password),
            "role": role,
            "assigned_profile": assigned_profile,
            "enabled": enabled
        }

        # Persist changes
        self._save_data(data)

    def edit_user(
        self,
        username,
        new_username,
        password,
        role,
        assigned_profile,
        enabled=True
        ):

        new_username = self._validate_username(new_username)
        assigned_profile = self._validate_assigned_profile(assigned_profile)
        enabled = self._validate_enabled(enabled)

        data = self.load_users()
        users = data["users"]

        # Check that the original user exists
        if username not in users:
            raise ValueError("User does not exist")

        # Validate role
        role = self._validate_role(role)

        # Validate assigned profile
        if not assigned_profile:
            raise ValueError("Assigned profile is required")

        # Prevent duplicate usernames
        for existing_username in users:
            if existing_username != username:
                if existing_username.casefold() == new_username.casefold():
                    raise ValueError("Username already exists")

        # Update user data
        user_data = users[username]

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
            if len(password) < 8:
                raise ValueError(
                    "Password must contain at least 8 characters"
                )

            user_data["password_hash"] = self.hash_password(password)

        # Update user properties
        user_data["role"] = role
        user_data["assigned_profile"] = assigned_profile
        user_data["enabled"] = enabled

        # Handle username changes
        if new_username != username:
            del users[username]
            users[new_username] = user_data

        self._save_data(data)

    def _validate_username(self, username):
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

    def delete_user(self, username):
        data = self.load_users()
        users = data["users"]

        if username not in users:
            raise ValueError("User does not exist")

        user = users[username]

        if (
            user.get("role") == "Administrator"
            and user.get("enabled", False)
            and self._count_enabled_administrators(users) <= 1
        ):
            raise ValueError(
                "Cannot delete the last active administrator"
            )

        del users[username]

        self._save_data(data)

    def _validate_assigned_profile(self, assigned_profile):
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
        if role not in ("Administrator", "Viewer"):
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
