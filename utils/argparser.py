
def add_parser_args(arg_parser):
    arg_parser.add_argument(
        "-i",
        "--input_file",
        help="File where your JSON logs are stored.",
    )
    arg_parser.add_argument(
        "-o",
        "--output_file",
        help="File where you would like your output stored.",
    )
    arg_parser.add_argument(
        "-k",
        "--seek_key",
        help=(
            "The key you want to seek. Will output all logs with this key."
        ),
    )
    arg_parser.add_argument(
        "-m",
        "--models",
        action="store_true",
        help="Writes JSON models to file instead of raw logs.",
    )
    arg_parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help=(
            "Writes raw JSON to file instead of raw logs. This will be "
            "written by default if no other output format option is "
            "selected."
        ),
    )
    arg_parser.add_argument(
        "-a",
        "--analyze",
        action="store_true",
        help=(
            "Analyze the logs, output logs with duplicate keys as well "
            "as any logs with nested data."
        ),
    )
    arg_parser.add_argument(
        "-n",
        "--nested",
        action="store_true",
        help="Output logs with nested data."
    )
    arg_parser.add_argument(
        "-d",
        "--duplicates",
        action="store_true",
        help="Output logs with duplicate keys",
    )
