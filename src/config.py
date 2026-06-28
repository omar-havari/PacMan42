import json
from typing import Any, List

class Config:
    def __init__(self, config_file: str):
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
            cleaned = "\n".join(line for line in lines if not line.strip().startswith("#"))
            config_data = json.loads(cleaned)
        except FileNotFoundError:
            print(f"Error: Configuration file '{config_file}' not found. Using default settings.")
            config_data = {}
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse configuration file '{config_file}': {e}. Using default settings.")
            config_data = {}
        
        self.highscore_file: str = config_data.get("highscore_file", "highscores.json")
        self.level: List[Any] = config_data.get("level", [])
        self.width: int = config_data.get("width", 800)
        self.height: int = config_data.get("height", 600)
        self.lives: int = config_data.get("lives", 3)
        self.pacgum: int = config_data.get("pacgum", 0)
        self.points_per_pacgum: int = config_data.get("points_per_pacgum", 10)
        self.points_per_super_pacgum: int = config_data.get("points_per_super_pacgum", 50)
        self.points_per_ghost: int = config_data.get("points_per_ghost", 200)
        self.seed: int = config_data.get("seed", 42)
        self.level_max_time: int = config_data.get("level_max_time", 90)

        self._validate()


    def _validate(self):
        if self.lives<=0:
            print("Warning: 'lives' must be greater than 0. Using default value of 3.")
            self.lives = 3
        if self.width <=0 or self.height <=0:
            print("Warning: 'width' and 'height' must be greater than 0. Using default values of 800x600.")
            self.width = 800
            self.height = 600   
        if self.level_max_time <= 0:
            print("Warning: 'level_max_time' must be greater than 0. Using default value of 90.")
            self.level_max_time = 90
        if self.points_per_pacgum < 0 or self.points_per_super_pacgum <0 or self.points_per_ghost <0:
            print ("Warning: Points values must be non-negative. Using default values of 10, 50, and 200 respectively.")
            self.points_per_pacgum = 10
            self.points_per_super_pacgum = 50
            self.points_per_ghost = 200
        if not isinstance(self.seed, int):
            print("Warning: 'seed' must be an integer. Using default value of 42.")
            self.seed = 42
        if  not isinstance(self.level, list):
            print("Warning: 'level' must be a list. Using default empty list.")
            self.level = []

    