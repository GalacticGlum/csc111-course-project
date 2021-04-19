"""A logger instance with a colourised format."""
import copy
import logging
import colorama


def colourise_string(string: str, colour: str) -> str:
    """Return a string with a stdout colour format."""
    reset_style = colorama.Style.RESET_ALL
    return f'{colour}{string}{reset_style}'


# Colours for the different logging level.
LOG_COLORS = {
    logging.FATAL: colorama.Fore.LIGHTRED_EX,
    logging.ERROR: colorama.Fore.RED,
    logging.WARNING: colorama.Fore.YELLOW,
    logging.DEBUG: colorama.Fore.LIGHTWHITE_EX
}

# Format the different logging levels.
LOG_LEVEL_FORMATS = {}

# Generic logger format.
LOGGER_FORMAT = '%(asctime)s - %(levelname)s: %(message)s'


class ColourisedLoggerFormatter(logging.Formatter):
    """A logging.Formatter that adds colours."""
    def format(self, record, *args, **kwargs):
        """Format the log message."""
        # To avoid mutating the original record ('action-at-a-distance'),
        # we make a deepcopy of the record.
        record_copy = copy.copy(record)
        if record_copy.levelno in LOG_COLORS:
            # we want levelname to be in different color, so let's modify it
            colour = LOG_COLORS[record_copy.levelno]
            record_copy.levelname = f'{colour}{record_copy.levelname}{colorama.Style.RESET_ALL}'

        original_format = self._style._fmt
        self._style._fmt = LOG_LEVEL_FORMATS.get(record.levelno, original_format)

        # now we can let standart formatting take care of the rest
        result = super().format(record_copy, *args, **kwargs)

        self._style._fmt = original_format
        return result


logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(ColourisedLoggerFormatter(LOGGER_FORMAT))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

