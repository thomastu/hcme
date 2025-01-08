"""
Parse BEAM agent events.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Registry:

    root: str

    default_inum: int = None

    def __post_init__(self):
        self.root = Path(self.root)
        assert self.root.exists()

        self.iter_num = self.default_inum

    def _register(self):
        """Create the registry of relevant BEAM outputs."""

        # Directory of results for iteration
        self.it_dir = Path(self.root) / "ITERS" / f"it.{self.iter_num}"
        assert self.it_dir.exists()

        self.physsim = self.it_dir / f"{self.iter_num}.physSimEvents.csv"
        self.events = self.it_dir / f"{self.iter_num}.events.csv"

    @property
    def iter_num(self):
        return self._iter_num

    @iter_num.setter
    def iter_num(self, value):
        if value is None:
            # Calculate most recent iteration in the rooth path
            iters = sorted(
                int(fn.name.split(".")[-1]) for fn in (self.root / "ITERS").glob("it.[0-9]*")
            )
            # Take the second-to-last iteration to ensure a full run
            self._iter_num = iters[-2] if len(iters) >= 2 else iters[-1]
        else:
            self._iter_num = value
        self._register()
