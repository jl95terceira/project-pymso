import dataclasses

from . import app as app

@dataclasses.dataclass
class DocProps:

    app:'app.Properties' = dataclasses.field(default_factory=lambda: app.Properties())
