from dataclasses import dataclass


@dataclass(frozen=True)
class KimiSource:
    index: int
    source: str
    title: str
    description: str
    url: str
    domain: str = ""