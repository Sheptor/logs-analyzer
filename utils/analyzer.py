import os
from multiprocessing import Pool, cpu_count
import typing as tp
from copy import copy

LOG_LEVELS: tp.Tuple = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def get_files_list(files: tp.Union[str, tp.Iterable[str]]) -> tp.Tuple[str, ...]:
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
        raise FileNotFoundError("files_list must be filename/directory or iterable of filenames/directories")

    return files_list


def start_analyze(files: tp.Union[str, tp.Iterable[str]]) -> tp.Dict[str, tp.Dict[str, int]]:
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


def analyze_log_file(filename: str) -> tp.Dict[str, tp.Dict[str, int]]:
    counter: tp.Dict[str, tp.Dict[str, int]] = dict()
    handler_counter: tp.Dict[str, int] = {
        i_level: 0 for i_level in LOG_LEVELS
    }

    with open(filename, "r") as log_file:
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
    handlers_list = sorted(counter.keys())
    return {
        i_level: sum([
            counter[i_handler][i_level] for i_handler in handlers_list
        ])
        for i_level in LOG_LEVELS
    }


def get_total_requests(total_counters: tp.Dict[str, int]) -> int:
    return sum(total_counters.values())

def handler_counter_to_text(handler_counter: tp.Dict, min_field_len: int) -> str:
    counter_text = ""
    for i_level in handler_counter:
        counter_text += f"{handler_counter[i_level]: <{min_field_len}}"
    return counter_text


def get_output(counter: tp.Dict, report_file_name: str) -> None:
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
