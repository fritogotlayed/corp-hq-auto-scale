"""Configures the application logging"""
import logging


def setup(logger: logging.Logger):
    """Configures the provided logger

    :param logger: The logger to configure
    """

    # create console handler with a debug log level
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    # create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)

    # add the handler to the logger
    logger.addHandler(stream_handler)
