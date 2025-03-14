import json

def load_config(config_file="config.json"):
    """Loads JSON configuration from a file."""
    with open(config_file, "r") as f:
        return json.load(f)

config = load_config()
