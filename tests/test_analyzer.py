import os.path
import pytest

import utils.analyzer


@pytest.fixture
def get_logs_dir():
    logs_dir = os.path.join(os.path.dirname(__file__), "test_logs")
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    yield logs_dir
    for i_file in os.listdir(logs_dir):
        os.remove(os.path.join(logs_dir, i_file))

def make_log_file(logs_dir, file_number):
    with open(os.path.join(logs_dir, f"log_file_{file_number}.log"), "w") as log_file:
        for i_index in range(5):
            log_file.write("2025-01-01 00:00:00,000 DEBUG django.request: GET handler_name 204 OK [127.0.0.1]\n")
        for i_index in range(10):
            log_file.write("2025-01-01 00:00:00,000 INFO django.request: GET handler_name 201 OK [127.0.0.1]\n")
        for i_index in range(15):
            log_file.write("2025-01-01 00:00:00,000 WARNING django.security: IntegrityError: duplicate key value violates unique constraint\n")
        for i_index in range(20):
            log_file.write("2025-01-01 00:00:00,000 ERROR django.request: Internal Server Error: handler_name [127.0.0.1] - DatabaseError: Deadlock detected\n")
        for i_index in range(25):
            log_file.write("2025-01-01 00:00:00,000 CRITICAL django.core.management: ConnectionError: Failed to connect to payment gateway\n")

def test_get_files_list_from_non_existent_directory(get_logs_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(os.path.join("tests", "non_existent_directory/"))

def test_get_files_list_from_empty_directory(get_logs_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(get_logs_dir)

def test_get_files_list_by_non_existent_path(get_logs_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(os.path.join(get_logs_dir, "non_existent_log_file"))

def test_get_files_list_from_directory_with_logs(get_logs_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(os.path.join(get_logs_dir, "non_existent_log_file"))

def test_get_files_list_from_directory_with_non_log_files(get_logs_dir):
    with open(os.path.join(get_logs_dir, "non_log_file.png"), "w") as non_log_file:
        pass
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(os.path.join("tests", "test_logs"))

def test_get_files_list_from_directory_with_log_files_and_one_non_log_files(get_logs_dir):
    for i_index in range(3):
        make_log_file(logs_dir=get_logs_dir, file_number=i_index)
    with open(os.path.join(get_logs_dir, "non_log_file.png"), "w") as non_log_file:
        pass
    files_list = utils.analyzer.get_files_list(os.path.join("tests", "test_logs"))
    assert sorted(files_list) == sorted(tuple(os.path.join(get_logs_dir, f"log_file_{i_index}.log") for i_index in range(3)))

def test_get_files_list_by_non_log_file_path(get_logs_dir):
    with open(os.path.join(get_logs_dir, "non_log_file.png"), "w") as non_log_file:
        pass
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(os.path.join(get_logs_dir, "non_log_file.png"))

def test_get_files_list_by_paths_list_with_one_non_log_file(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    with open(os.path.join(get_logs_dir, "non_log_file.png"), "w") as non_log_file:
        pass
    file_names_list = [os.path.join(get_logs_dir, "non_log_file.png"), os.path.join(get_logs_dir, "log_file_0.log")]
    with pytest.raises(FileNotFoundError) as exc_info:
        files_list = utils.analyzer.get_files_list(file_names_list)

def test_get_files_list_by_paths_list_of_two_log_files(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    make_log_file(logs_dir=get_logs_dir, file_number=1)
    file_names_list = [os.path.join(get_logs_dir, "log_file_0.log"), os.path.join(get_logs_dir, "log_file_1.log")]
    obtained_files_list = utils.analyzer.get_files_list(file_names_list)
    assert sorted(obtained_files_list) == sorted(file_names_list)

def test_get_files_from_directory_with_log_files(get_logs_dir):
    for i_index in range(3):
        make_log_file(logs_dir=get_logs_dir, file_number=i_index)
    obtained_files_list = utils.analyzer.get_files_list(os.path.join("tests", "test_logs"))
    assert sorted(obtained_files_list) == sorted(tuple(os.path.join(get_logs_dir, f"log_file_{i_index}.log") for i_index in range(3)))

def test_get_files_by_path(get_logs_dir):
    original_file_name = os.path.join(get_logs_dir, f"test_log_1.log")
    with open(original_file_name, "w") as log_file:
        pass
    obtained_files_list = utils.analyzer.get_files_list(os.path.join("tests", "test_logs"))
    assert obtained_files_list == (original_file_name, )

def test_analyze_empty_log_file(get_logs_dir):
    with open(os.path.join(get_logs_dir, "log_file.log"), "w") as log_file:
        pass
    result = utils.analyzer.analyze_log_file(os.path.join(get_logs_dir, "log_file.log"))
    assert result == dict()

def test_analyze_log_file_by_path(get_logs_dir,):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    result = utils.analyzer.analyze_log_file(os.path.join(get_logs_dir, "log_file_0.log"))
    assert result == {
        "handler_name": {
            "DEBUG": 5,
            "INFO": 10,
            "WARNING": 0,
            "ERROR": 20,
            "CRITICAL": 0
        }
    }

def test_start_analyze_with_non_existent_file(get_logs_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        result = utils.analyzer.start_analyze(os.path.join(get_logs_dir, "non_existent.log"))

def test_start_analyze_with_non_existent_directory(get_logs_dir):
    with pytest.raises(FileNotFoundError) as exc_info:
        result = utils.analyzer.start_analyze(os.path.join(get_logs_dir, "non_existent_dir"))

def test_start_analyze_log_file_from_dir_with_one_file(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    files_list = utils.analyzer.get_files_list(get_logs_dir)
    result = utils.analyzer.start_analyze(files_list)
    assert result == {
        "handler_name": {
            "DEBUG": 5,
            "INFO": 10,
            "WARNING": 0,
            "ERROR": 20,
            "CRITICAL": 0
        }
    }

def test_start_analyze_log_file_from_dir_with_three_files(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    make_log_file(logs_dir=get_logs_dir, file_number=1)
    make_log_file(logs_dir=get_logs_dir, file_number=2)
    files_list = utils.analyzer.get_files_list(get_logs_dir)
    result = utils.analyzer.start_analyze(files_list)
    assert result == {
        "handler_name": {
            "DEBUG": 5*3,
            "INFO": 10*3,
            "WARNING": 0,
            "ERROR": 20*3,
            "CRITICAL": 0
        }
    }

def test_start_analyze_log_file_by_path(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    make_log_file(logs_dir=get_logs_dir, file_number=1)
    make_log_file(logs_dir=get_logs_dir, file_number=2)
    files_list = [os.path.join(get_logs_dir, f"log_file_{i_index}.log") for i_index in range(3)]
    result = utils.analyzer.start_analyze(files_list)
    assert result == {
        "handler_name": {
            "DEBUG": 5*3,
            "INFO": 10*3,
            "WARNING": 0,
            "ERROR": 20*3,
            "CRITICAL": 0
        }
    }

def test_start_analyze_log_file_by_path_with_one_non_existent_file(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    make_log_file(logs_dir=get_logs_dir, file_number=1)
    make_log_file(logs_dir=get_logs_dir, file_number=2)
    files_list = [os.path.join(get_logs_dir, f"log_file_{i_index}.log") for i_index in range(3)]
    files_list.append(os.path.join(get_logs_dir, "non_existent_file"))
    with pytest.raises(FileNotFoundError) as exc_info:
        result = utils.analyzer.start_analyze(files_list)

def test_start_analyze_log_file_by_path_with_one_non_log_file(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    make_log_file(logs_dir=get_logs_dir, file_number=1)
    make_log_file(logs_dir=get_logs_dir, file_number=2)
    files_list = [os.path.join(get_logs_dir, f"log_file_{i_index}.log") for i_index in range(3)]
    with open(os.path.join(get_logs_dir, "non_log_file.png"), "w") as non_log_file:
        pass
    files_list.append(os.path.join(get_logs_dir, "non_log_file.png"))
    with pytest.raises(FileNotFoundError) as exc_info:
        result = utils.analyzer.start_analyze(files_list)

def test_get_total_counter(get_logs_dir):
    make_log_file(logs_dir=get_logs_dir, file_number=0)
    result = utils.analyzer.analyze_log_file(os.path.join(get_logs_dir, "log_file_0.log"))
    assert utils.analyzer.get_total_counter(result) == {
            "DEBUG": 5,
            "INFO": 10,
            "WARNING": 0,
            "ERROR": 20,
            "CRITICAL": 0
        }

def test_get_total_requests(get_logs_dir):
    total_counters = {
            "DEBUG": 5,
            "INFO": 10,
            "WARNING": 0,
            "ERROR": 20,
            "CRITICAL": 0
        }
    result = utils.analyzer.get_total_requests(total_counters=total_counters)
    assert result == 5 + 10 + 20

def test_handler_counter_to_text(get_logs_dir):
    total_counters = {
            "DEBUG": 5,
            "INFO": 10,
            "WARNING": 0,
            "ERROR": 20,
            "CRITICAL": 0
        }
    result = utils.analyzer.handler_counter_to_text(handler_counter=total_counters, min_field_len=12)
    assert "5 " in result
    assert " 10 " in result
    assert " 0 " in result
    assert " 20 " in result

def test_get_output(get_logs_dir):
    counter = {
        "handler_1": {
            "DEBUG": 5,
            "INFO": 10,
            "WARNING": 0,
            "ERROR": 20,
            "CRITICAL": 0
        }
    }
    result = utils.analyzer.get_output(counter=counter, report_file_name=None)
    assert f"Total requests: {5 + 10 + 20}" in result
    assert " 5 " in result
    assert " 10 " in result
    assert " 0 " in result
    assert " 20 " in result
