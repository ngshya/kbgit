import logging
import logging.config


DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - ' + \
                      '%(filename)s -  %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'WARNING', 
        },
    },
    'loggers': {
        'kbgit': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)

logger = logging.getLogger("kbgit")