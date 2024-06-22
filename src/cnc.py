from typing import Generator

from state import *
from parser import Parser


class CNC:
    def __init__(self):
        self.state = State()
        self.parser = Parser()

    def input_programs(self, programs: str):
        ...

    def remove_program(self, num: int):
        ...

    def input_parameter(self, num: int, parameter: tuple):
        ...

    def cycle_start(self, num: int) -> Generator:
        for changes in self.parser.cycle_start(num):
            yield changes




class NCError(Exception):
    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return f"{self.args}"
