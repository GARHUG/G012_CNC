from programs import Programs
from parameters import Parameters
from positions import Positions
from coordinates import Coordinates
from tool_settings import ToolSettings
from variables import Variables

class State:
    def __init__(self):
        self.programs = Programs()
        self.parameters = Parameters()
        self.Positions = Positions()
        self.coordinates = Coordinates()
        self.tool_settings = ToolSettings()
        self.variables = Variables()