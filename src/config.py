import sys
import json
import os

def load_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    if not os.path.exists(config_path):
        print("Error: No se encontró config.json")
        sys.exit(1)
    with open(config_path, "r") as f:
        return json.load(f)

def save_config(config):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
