"""
src/reactor.py - Unified interface exposing 1D and 2D reactor simulation solvers.
"""

from src.reactor_1d import Reactor1D, SimulationResults1D
from src.reactor_2d import Reactor2D, SimulationResults2D

__all__ = ["Reactor1D", "SimulationResults1D", "Reactor2D", "SimulationResults2D"]
