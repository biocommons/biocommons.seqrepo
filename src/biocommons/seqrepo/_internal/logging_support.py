import logging


class DuplicateFilter:
    """
    Filters away duplicate log messages.
    Modified from https://stackoverflow.com/a/60462619/342839
    """

    def __init__(self, logger=None):
        self.log_keys = set()
        self.logger = logger

    def filter(self, record):
        log_key = (record.name, record.lineno, str(record.msg))
        is_duplicate = log_key in self.log_keys
        if not is_duplicate:
            self.log_keys.add(log_key)
        return not is_duplicate

    def __enter__(self):
        if not self.logger:
            raise RuntimeError(
                "DuplicateFilter used as context manager without specifying logger=... argument"
            )
        self.logger.addFilter(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.removeFilter(self)
