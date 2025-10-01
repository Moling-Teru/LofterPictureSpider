from typing import Any, Optional

class Color:
    def __init__(self):
        self.colour = {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "RED": "\033[31m",
            "GREEN": "\033[32m",
            "YELLOW": "\033[33m",
            "BLUE": "\033[34m",
            "MAGENTA": "\033[35m",
            "CYAN": "\033[36m",
            "WHITE": "\033[37m",
            "BG_RED": "\033[41m",
            "BG_GREEN": "\033[42m",
            "BG_YELLOW": "\033[43m",
        }
    def get_colour(self, colour_name:str|list) -> Optional[str]:
        try:
            if isinstance(colour_name, list):
                return ''.join([self.colour[x] for x in colour_name])
            if isinstance(colour_name,str):
                return self.colour[colour_name]
        except KeyError as _:
            raise KeyError(f'Colour {colour_name} not found.')
    def reset(self) -> str:
        return self.colour["RESET"]