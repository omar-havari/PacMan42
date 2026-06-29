import sys
from src.config import Config
from src.main_menu_UI import run_main_menu


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".json"):
        print("Usage: python pac-man.py config.json")
        sys.exit(1)
    
    config_file_path = sys.argv[1]
    config = Config(config_file_path)
    run_main_menu(config)
