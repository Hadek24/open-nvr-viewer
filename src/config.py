import sys
import json
import os

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
        return json.load(f)

def save_config(config):
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
