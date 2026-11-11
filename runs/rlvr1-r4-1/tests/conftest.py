"""Keep hypothesis's storage directory under audit/out instead of the working directory."""
import pathlib

from hypothesis import configuration

configuration.set_hypothesis_home_dir(str(pathlib.Path(__file__).resolve().parents[1] / "out" / ".hypothesis"))
