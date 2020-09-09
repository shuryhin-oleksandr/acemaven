try:
    from config.settings.local import *
except ImportError:
    from config.settings.common import *
