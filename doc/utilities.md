# Utilities

The TESS-IDA-TOOLS comprises the following scripts:
* `tess-ida-db`. Auxiliar database management,
* `tess-ida-get`. Download series of IDA monthly files.
* `tess-ida-ecsv`. Transform series of monthly files. Combine series of ECSV files into one.
* `tess-ida-pipe`. The complete download/transform/combine pipeline 

All script support the following ***generic options***:
* `--version`. Prints software version and quits.
* `--console`. Prints execution info on the terminal console (up to level INFO)
* `--log-file`. Appends the same execution info to a log file
* `--quiet`. Suppresses all messages except CRITICAL, ERROR and WARNING.
* `--verbose`. Includes DEBUG level messages.

All scripts include a help system (`-h` or `--help`) to describe the available commands and command options.

Examples:

```bash
tess-ida-get -h
```

shows that this script has three commands: `single`, `range` and `photometers`

Typing:

```bash
tess-ida-get single -h
tess-ida-get range -h
tess-ida-get photometers -h
```

will show available options for each command. The generic options always come *before* the command.

Example:

```bash
tess-ida-get --console --quiet photometers --list stars1 stars703 stars328 --since 2024-03 --until 2024-07
```

Many commands include `-s|--since` and `-u|--until` options. 
If not specified, the default values are the previos month and current month respectively.

Many commands include `-i|--input-dir` and `-o|output-dir` options.
If not specified, the default value is the current working directory.