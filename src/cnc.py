from typing import Generator

from programs import Programs
from parameters import Parameters
from positions import Positions
from coordinates import Coordinates
from tool_settings import ToolSettings
from variables import Variables
from parser import Parser


class CNC:
    def __init__(self):
        self.state = State()
        self.parser = Parser(self.state)

    def input_programs(self, programs: str):
        ...

    def remove_program(self, num: int):
        ...

    def input_parameter(self, num: int, parameter: tuple):
        ...

    def cycle_start(self, num: int) -> Generator:
        for changes in self.parser.cycle_start(num):
            yield changes


class State:
    def __init__(self):
        self.programs = Programs()
        self.parameters = Parameters()
        self.Positions = Positions()
        self.coordinates = Coordinates()
        self.tool_settings = ToolSettings()
        self.variables = Variables()