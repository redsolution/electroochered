try:
    from sadiki.local_settings import *
except ImportError:
    from sadiki.settings import *
    from sadiki.conf_settings import *