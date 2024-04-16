from __future__ import generators

from parser import Parser
from programs import Programs
from parameters import Parameters
from positions import Positions
from coordinates import Coordinates
from tool_settings import ToolSettings
from variables import Variables


class CNC:
    def __init__(self):
        self.parser = Parser()
        self.programs = Programs()
        self.parameters = Parameters()
        self.Positions = Positions()
        self.coordinates = Coordinates()
        self.tool_settings = ToolSettings()
        self.variables = Variables()

    def input_programs(self, programs: str):
        ...

    def remove_program(self, num: int):
        ...

    def input_parameter(self, num: int, parameter: tuple):
        ...

    def cycle_stert(self, num: int) -> :