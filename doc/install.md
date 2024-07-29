# Installation and configuration

## Installation

We strongly recommend making a Python virtual environment where you install this package and other packages related to your data analysis.
A very popular way is to use [Jupyter Notebooks](https://jupyter.org/), so lets do this as an example

The following lines create a jupyter folder from our home directory, a new Python virtual environment named `.venv` and activate it.
```bash
~$ mkdir jupyter
cd jupyter 
jupyter$ python3 -m venv .venv
jupyter$ source .venv/bin/activate
(.venv)  jupyter$ 
```

Now we install jupyter:

```bash
pip install -U pip
pip install notebook
```

And then our TESS-IDA-TOOLS, directly from our [GitHub repository](https://github.com/STARS4ALL/TESS-IDA-TOOLS):

```bash
pip install git+https://github.com/STARS4ALL/TESS-IDA-TOOLS#main
```

## Configuration

With the help of a text editor, create a new auxiliar environment file called `.env`
Inside this file, you must add two environment variables:

```text
IDA_URL=<NextCloud Server IDA base URL>
DATABASE_FILE=adm/tessida.db
```

The first one contains the base URL of our NextCloud Server where we publish the IDA files (and you should already have)
The second one is the path of an auxiliar SQLite database file that help us in the process of download and convert IDA files to ECSV

The example above shows that we will create an `adm` subdirectory inside our working directory `~/jupyter` and a database file named `tessida.db`.

As the final step, we must initialize the database:

```bash
tess-ida-db --console schema create
```
All the configuration is done now.
