import sys
import json
import os
import keyring

def get_config_path():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "config.json")
    
def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        print("Error: No se encontró config.json")
        sys.exit(1)
    with open(config_path, "r") as f:
        config = json.load(f)
    password = get_nvr_password()
    if password is None:
        print("Error: No se encontró la contraseña del NVR en el keyring")
        sys.exit(1)
    config["NVR_PASS"] = password
    return config

def save_config(config):
    config_path = get_config_path()
    config_to_save = config.copy()
    config_to_save.pop("NVR_PASS", None)
    with open(config_path, "w") as f:
        json.dump(config_to_save, f, indent=4)

def get_nvr_password():
    return keyring.get_password("open-nvr-viewer", "nvr")

def set_nvr_password(password):
    keyring.set_password("open-nvr-viewer", "nvr", password)
