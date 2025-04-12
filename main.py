import argparse
from utils.analyzer import start_analyze, get_output
import sys
import traceback


parser = argparse.ArgumentParser()
parser.add_argument(dest="FILES", metavar="FILES", nargs="*", help="Log files list to analyze", default="logs/")
parser.add_argument("--report", help="Report file name")
namespace = parser.parse_args()
report_file_name = namespace.report
FILES = namespace.FILES

# examples:
# FILES = "logs/"  # analyze all files in directory
# FILES = ("logs/app1.log", "logs/app2.log")  # select files to analyze
# FILES = "logs/app1.log"  # select one file to analyze

if __name__ == '__main__':
    try:
        counter = start_analyze(files=FILES)
        get_output(counter=counter, report_file_name=report_file_name)

    except FileNotFoundError as exc:
        print(traceback.format_exc())
        sys.exit(1)

