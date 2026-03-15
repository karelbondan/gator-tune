from time import strftime

import configs

CONFIG = configs.CONFIG


def _format_tab(log_type: str):
    # 9 is the total length from start to before
    # the log msg, e.g. INFO     something
    return " {}{}".format(log_type, " " * (9 - len(log_type)))


def log_info(log: str):
    print("{}{}{}".format(strftime("%Y-%m-%d %H:%M:%S"), _format_tab("INFO"), log))


def log_warn(log: str):
    print("{}{}{}".format(strftime("%Y-%m-%d %H:%M:%S"), _format_tab("WARN"), log))


def log_error(log: str):
    print("{}{}{}".format(strftime("%Y-%m-%d %H:%M:%S"), _format_tab("ERROR"), log))
