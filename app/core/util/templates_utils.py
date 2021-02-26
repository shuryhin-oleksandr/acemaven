import jinja2
from delorean import Delorean
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

from app.core.util import consts


def build_jinja2_environment(**options) -> Environment:
    undefined_cls = (jinja2.ChainableUndefined, jinja2.DebugUndefined)[settings.DEBUG]

    opts = options.copy()
    opts.update(
        {
            "auto_reload": True,
            "undefined": undefined_cls,
        }
    )

    env = Environment(**opts)

    global_names = {
        "debug": settings.DEBUG,
        "Delorean": Delorean,
        "enumerate": enumerate,
        "project_name": consts.PROJECT_NAME.lower(),
        "repr": repr,
        "static": static,
        "url": reverse,
        "len": len,
    }

    env.globals.update(**global_names)

    return env
