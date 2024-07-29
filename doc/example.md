# Example of usage

***Note:*** Make sure that you have already completed the installation and configuration procedure before following this example.

## Getting the files
In your jupyter working directory, with the activated virtual environment, type:

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars289 -s 2019-05 -u 2023-06 -i IDA -o ECSV
```

The above utility `tess-ida-pipe` is the complete pipeline that:
1. Downloads IDA monthly files for stars289 since 2019-05 until 2023-06, placing them under `IDA/stars289` subdirectory.
2. Transforms them to ECSV files under `ECSV/stars289`.
3. Merges them into a combined time series file named `ECSV/stars289/since_2019-05_until_2023-06.ecsv`

Note that the transformation process will take a while (1-2 min per file), since every monthly file is added Solar Altitude, Moon Altitude and Moon Phase.

However, if you re-run the script again, it will download all the files but will skip the transform part because the software detects no changes
in IDA files.

As the final product for this step, we have the `ECSV/stars289/since_2019-05_until_2023-06.ecsv` ready to be analyzed in a Jupyter notebook.

## Launching Jupyter

The second step to perform in the command line is launching Jupyter Notebook. From then all, all processing will be done in an notebook.

```bash
jupyer notebook
```

A snapshot of the notebook can be seen [here](TESS-IDA-TOOLS-Example.md)