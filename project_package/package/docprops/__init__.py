import dataclasses

from . import app, core

@dataclasses.dataclass
class DocProps:

    app :'app.Properties'      = dataclasses.field(default_factory=lambda: app.Properties     ())
    core:'core.CoreProperties' = dataclasses.field(default_factory=lambda: core.CoreProperties())
