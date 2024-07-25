# get-tess-ida
Get TESS-W IDA monthly files from NextCloud server

# Instalation and dependencies

There are two versions of this tool, the simples one is a self contained script called ***get-tess-ida.py***) which just downloads the data files.
The other one is a full package, bundled other analysis tools (*being developed at the moment*).
For both versions, it is ***highly recommended*** to create a virtual environment and activate is:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Simple Script installation

1. Download the [get-tess-ida.py script](https://raw.githubusercontent.com/STARS4ALL/TESS-IDA-TOOLS/main/get-tess-ida.py) from the GitHub repository:

3. Install the following packages in the virtual environment previously created:

```bash
pip install python-decouple python-dateutil requests
```

## Package installation

1. Download the full package from GitHub.
There are several ways to do it, either cloning the github repo for the latest development evrsions or use a previous packaged version


```bash
git clone https://github.com/STARS4ALL/TESS-IDA-TOOLS.git
```

2. Install the package in the virtual envirnment previously created:


```bash
pip install .
```

## Additional configuartion for both versions 

1. Make an env file caled `.env` (Mac/Linux) or settings.ini (Windows) containing an enviromental variable

.env file:

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
  {month,year,range,selected}
    month               Download single monthly file
    year                Download a year of monthly files
    range               Download from a month range
    selected            Download selected photometers in a month range

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
                        Year and Month
  -u <YYYY-MM>, --until <YYYY-MM>
                        Year and Month (defaults to current month)
```
## Examples

1. Download single month for a given photometer
```bash
python get-tess-ida.py --console month --name stars1 --month 2023-4
```

2. Download an ***specific file*** for a given photometer
```bash
python get-tess-ida.py --console month --name stars4 --exact stars4_2016-09_2.dat
```

3. Download a whole year for a given photometer
```bash
python get-tess-ida.py --console year --name stars1 --year 2023
```

4. Download monthly files since a given month until another

If no `--since` parameter is given, defaults to last month.
If no `--until` parameter is given, defaults to current month.

```bash
python get-tess-ida.py --console since --name stars1 --since 2023-3 --until 2023-6
```


5. Download a range of monthly files for a selected set of photometers

If no `--since` parameter is given, defaults to last month.
If no `--until` parameter is given, defaults to current month.

Instead of names, we pass just photometer numbers. 

The script below will download data from photometers `stars1` up to `stars5` since month `2023-06` until current month

```bash
python get-tess-ida.py --console selected --range 1 5 --since 2023-06
```

The script below will download data from selected photometers `stars1` , `stars243`, `stars703` 
since last month until current month

```bash
python get-tess-ida.py --console selected --list 1 245 703
```
