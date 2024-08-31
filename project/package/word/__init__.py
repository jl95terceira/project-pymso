import dataclasses

from . import document

@dataclasses.dataclass
class Word:

    document:'document.Document' = dataclasses.field(default_factory=lambda: document.Document())
