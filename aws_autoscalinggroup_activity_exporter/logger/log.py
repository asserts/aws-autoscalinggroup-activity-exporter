import logging


def setup_custom_logger(path, level):
    """Custom logger

    Args:
        path (str): the path to write logs to (note, in addition to stdout/stderr)
        level (str): the log level
    """

    level_config = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING
    }

    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logging.basicConfig(level=level_config[level], handlers=[stream_handler])
