import os
from multiprocessing import Pool, cpu_count
import typing as tp
from copy import copy

LOG_LEVELS: tp.Tuple = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def get_files_list(files: tp.Union[str, tp.Iterable[str]]) -> tp.Tuple[str, ...]:
    """
    The function retrieves log file names by directory or path. If one of the specified files or directories
    does not exist or the specified file is not a log file, the FileNotFoundError occurs.
    If the directory contains log files and non-log files, FileNotFoundError will not be started.
    :param files: list of file names or directories with log files
    :return: list of log files
    """
    if isinstance(files, str):
        files = (files,)
    try:
        if not all([os.path.exists(i_file) for i_file in files]):
            raise TypeError

        files_list = []
        for i_file in files:
            if os.path.isdir(i_file):
                files_list.extend([
                    os.path.abspath(os.path.join(i_file, j_file))
                    for j_file in os.listdir(i_file)
                    if j_file.endswith((".log", ".txt", ".logs"))
                ])
            elif i_file.endswith((".log", ".txt", ".logs")):
                files_list.append(os.path.abspath(i_file))
            else:
                raise FileNotFoundError("Only .log, .txt, .logs supported")
        files_list = tuple(set(files_list))
        if len(files_list) == 0:
            raise FileNotFoundError("Directory is empty")
    except TypeError:
        raise FileNotFoundError("files_list must be file_name/directory or iterable of file_names/directories")

    return files_list


def start_analyze(files: tp.Union[str, tp.Iterable[str]]) -> tp.Dict[str, tp.Dict[str, int]]:
    """
    The function counts the number of requests to handles, these are django.requests records in all files:
    for each handle, 
    for each logging level, 
    it groups requests by handles.
    :param files: list of file names or directories with log files to analyze
    :return: counter: {
        "handler_name_1": {
            "DEBUG": number of debug logs in all files,
            "INFO": number of info logs in all files,
            "WARNING": number of warning logs in all files,
            "ERROR": number of errors logs in all files,
            "CRITICAL": number of critical errors logs in all files,
        },
        "handler_name_2": {...},
        ...
    }
    """
    files_list = get_files_list(files)

    counter = None
    with Pool(min(cpu_count(), len(files_list))) as pool:
        result = pool.map(analyze_log_file, files_list)


    for i_result in result:
        if counter is None:
            counter = i_result
        else:
            counter = add_log_file_results(counter, i_result)

    return counter


def analyze_log_file(file_name: str) -> tp.Dict[str, tp.Dict[str, int]]:
    """
    The function counts the number of requests to handles, these are django.requests records in one file:
    for each handle, 
    for each logging level, 
    it groups requests by handles.
    :param file_name: log file to analyze
    :return: counter: {
        "handler_name_1": {
            "DEBUG": number of debug logs in file,
            "INFO": number of info logs in file,
            "WARNING": number of warning logs in file,
            "ERROR": number of errors logs in file,
            "CRITICAL": number of critical errors logs in file,
        },
        "handler_name_2": {...},
        ...
    }
    """
    counter: tp.Dict[str, tp.Dict[str, int]] = dict()
    handler_counter: tp.Dict[str, int] = {
        i_level: 0 for i_level in LOG_LEVELS
    }

    with open(file_name, "r") as log_file:
        for i, i_row in enumerate(log_file):
            if "django.request:" in i_row:
                log_elements = i_row.split()
                log_level = log_elements[2]  # If template is DATE TIME LOG_LEVEL
                if log_level not in {"WARNING", "ERROR", "CRITICAL"}:
                    handler = log_elements[5]  # If template is DATE TIME LOG_LEVEL LOGGER: METHOD: HANDLER
                else:
                    handler = i_row.split(": ")[2].split()[0]  # If template is DATE TIME LOG_LEVEL LOGGER: METHOD: ERROR_MESSAGE: HANDLER
                if counter.get(handler) is None:
                    counter[handler] = copy(handler_counter)
                counter[handler][log_level] += 1

    return counter


def add_log_file_results(base_counter: tp.Dict, other_counter: tp.Dict):
    """
    The function adds the results of the counter to the total counter.
    :param base_counter: total counter
    :param other_counter: counter of one file
    :return: total counter
    """
    for i_handler, i_counts in other_counter.items():
        if i_handler not in base_counter:
            base_counter[i_handler] = copy(i_counts)
        else:
            base_counter[i_handler] = {
                j_level: base_counter[i_handler][j_level] + i_counts[j_level]
                for j_level in LOG_LEVELS
            }

    return base_counter


def get_total_counter(counter: tp.Dict[str, tp.Dict[str, int]]) -> tp.Dict[str, int]:
    """
    The function counts the total number of requests for each logging level.
    :param counter: a counter for each handler for all files
    :return: total_counter: {
        "DEBUG": number of debug logs in all files,
        "INFO": number of info logs in all files,
        "WARNING": number of warning logs in all files,
        "ERROR": number of errors logs in all files,
        "CRITICAL": number of critical errors logs in all files,
    }
    """
    handlers_list = sorted(counter.keys())
    return {
        i_level: sum([
            counter[i_handler][i_level] for i_handler in handlers_list
        ])
        for i_level in LOG_LEVELS
    }


def get_total_requests(total_counters: tp.Dict[str, int]) -> int:
    """
    The function retrieves total django.request count from all files.
    :param total_counters:
    :return: number of django.request
    """
    return sum(total_counters.values())

def handler_counter_to_text(handler_counter: tp.Dict, min_field_len: int) -> str:
    """
    The function converts the counter to a string for convenient output.
    :param handler_counter: counter for convert
    :param min_field_len: minimal length of field
    :return: handler counter as text
    """
    counter_text = ""
    for i_level in handler_counter:
        counter_text += f"{handler_counter[i_level]: <{min_field_len}}"
    return counter_text


def get_output(counter: tp.Dict, report_file_name: tp.Optional[str]) -> str:
    """
    The function outputs the result of log analysis.
    if the report_file_name parameter is specified, it writes the result to the specified file.
    :param counter:
    :param report_file_name:
    :return: report text
    """
    output_text = ""

    max_handler_name_len = max(map(len, counter.keys())) + 4
    handlers_list = sorted(counter.keys())
    total_counters = get_total_counter(counter=counter)
    min_field_len = max(8, len(str(max(total_counters.values())))) + 4

    output_text += f"Total requests: {get_total_requests(total_counters)}\n\n"

    output_text += (
        f"{"HANDLER": <{max_handler_name_len}}"
        f"{"DEBUG": <{min_field_len}}"
        f"{"INFO": <{min_field_len}}"
        f"{"WARNING": <{min_field_len}}"
        f"{"ERROR": <{min_field_len}}"
        f"{"CRITICAL"}\n"
    )
    for i_handler in handlers_list:
        output_text += (
            f"{i_handler: <{max_handler_name_len}}"
            f"{handler_counter_to_text(counter[i_handler], min_field_len)}\n"
        )
    output_text += (
        f"{'': <{max_handler_name_len}}"
        f"{handler_counter_to_text(total_counters, min_field_len)}"
    )

    print(output_text)

    if report_file_name is not None:
        if not os.path.exists("results"):
            os.mkdir("results")
        with open(os.path.join("results", f"{report_file_name}.txt"), "w", encoding="UTF-8") as output_file:
            output_file.write(output_text)
        print(f"saved to {os.path.join('results', f'{report_file_name}.txt')}")

    return output_text
