# logs-analyzer
This project is designed to analyze django log files with extensions: `.log`, `.txt`, `.logs`. Records are counted for the DEBUG, INFO, WARNING, ERROR, and CRITICAL levels for each handler.counts the number of requests to handles, these are django.requests records in all files:
* for each handle, 
* for each logging level, 
* it groups requests by handles.

Logs example:
```text
# logs/log_file.log:

2025-01-01 00:00:00,000 INFO django.request: GET /api/v1/some_name/ 204 OK [127.0.0.1]
2025-01-01 00:00:00,000 ERROR django.request: Internal Server Error: /admin/dashboard/ [127.0.0.1] - DatabaseError: Deadlock detected
2025-01-01 00:00:00,000 DEBUG django.db.backends: (0.41) SELECT * FROM 'products' WHERE id = 4;
2025-01-01 00:00:00,000 WARNING django.security: IntegrityError: duplicate key value violates unique constraint
2025-01-01 00:00:00,000 CRITICAL django.core.management: ConnectionError: Failed to connect to payment gateway
```

To generate the report, run main.py and enter the log files separated by a space.
Analyze all log files in directory:
```commandline
$ python main.py logs/
```
Analyze specified files:
```commandline
$ python main.py logs/log_file_1.log logs/log_file_2.log
```
Analyze files with save result to file:
```commandline
$ python main.py logs/log_file.log --report report_file_name
```

```text
# result/report_file_name.txt:

Total requests: 2

HANDLER               DEBUG       INFO        WARNING     ERROR       CRITICAL
/admin/dashboard/     0           0           0           1           0           
/api/v1/some_name/    0           1           0           0           0           
                      0           1           0           1           0           
```
