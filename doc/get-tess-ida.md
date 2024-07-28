# get-tess-ida.py
Script to download TESS-W IDA monthly files from NextCloud server.

# Instalation and dependencies

It is ***highly recommended*** to create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Simple Script installation

1. Download the [get-tess-ida.py script](https://raw.githubusercontent.com/STARS4ALL/TESS-IDA-TOOLS/main/get-tess-ida.py) from the GitHub repository:

2. Install the following packages in the virtual environment previously created:

```bash
pip install python-decouple python-dateutil requests
```

## Additional configuartion 

1. Make an enviroment file called `.env` (Mac/Linux) or settings.ini (Windows) containing enviromental variables.

The contents of this `.env` file should be:

```bash
IDA_URL=<NextCloud Server URL>
```

settings.ini file:

```ini
[settings]
IDA_URL=<NextCloud Server URL>
```

# Usage and examples

The utility is self-explanatory

`python get-tess-ida.py -h` shows general help and avaliable commands:

```bash
usage: ida.main [-h] [--version] [--console] [--log-file <FILE>] [--verbose | --quiet] {month,year,range,selected} ...

Get TESS-W IDA monthly files from NextCloud server

positional arguments:
  {single,range,photometers}
    single              Download single monthly file from a photometer
    range               Download a month range from a photometer
    photometers         Download a month range from selected photometers

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --console             Log to vanilla console.
  --log-file <FILE>     Log to file.
  --verbose             Verbose output.
  --quiet               Quiet output.

```

Each command has its own help:

`python get-tess-ida.py range -h` shows additional arguments

```bash
usage: ida.main range [-h] -n NAME -s <YYYY-MM> [-u <YYYY-MM>]

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Photometer name
  -s <YYYY-MM>, --since <YYYY-MM>
                        Year and Month (defaults to previous month)
  -u <YYYY-MM>, --until <YYYY-MM>
                        Year and Month (defaults to current month)
```
## Examples

### Download single month for a given photometer
```bash
python get-tess-ida.py --console single --month 2023-4 --name stars1 
```

### Download an specific file for a given photometer
```bash
python get-tess-ida.py --console single --exact stars4_2016-09_2.dat --name stars4 
```

### Download monthly files since a given month until another

If no `--since` parameter is given, defaults to last month.

If no `--until` parameter is given, defaults to current month.

```bash
python get-tess-ida.py --console range --since 2023-3 --until 2023-6 --name stars1 
```

### Download a range of monthly files for a selected set of photometers

If no `--since` parameter is given, defaults to last month.

If no `--until` parameter is given, defaults to current month.

***Photometers range***

Instead of names, we pass just photometer numbers. 


The script below will download data from photometers `stars1` up to `stars5` since month `2023-06` until current month:

```bash
python get-tess-ida.py --console photometers --range 1 5 --since 2023-06
```

***Selected photometers***

The script below will download data from selected photometers `stars1` , `stars243`, `stars703` 
since last month until current month:

```bash
python get-tess-ida.py --console photometers --list 1 245 703
```
