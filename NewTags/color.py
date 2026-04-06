# -*- coding: utf-8 -*-
"""Terminal color helper."""


class Color:
    COLORS = {
        "RESET": "\033[0m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "CYAN": "\033[36m",
    }

    def get_colour(self, color_name):
        return self.COLORS.get(color_name, "")

    def reset(self):
        return self.COLORS["RESET"]

    def red(self, text):
        return f"{self.COLORS['RED']}{text}{self.COLORS['RESET']}"

    def green(self, text):
        return f"{self.COLORS['GREEN']}{text}{self.COLORS['RESET']}"

    def yellow(self, text):
        return f"{self.COLORS['YELLOW']}{text}{self.COLORS['RESET']}"

    def blue(self, text):
        return f"{self.COLORS['BLUE']}{text}{self.COLORS['RESET']}"

    def cyan(self, text):
        return f"{self.COLORS['CYAN']}{text}{self.COLORS['RESET']}"


color = Color()
