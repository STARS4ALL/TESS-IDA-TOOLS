# The Auxiliar database

The TESS-IDA-TOOLS work with an auxiliary database with the purpose of being efficient in transformimg monthly IDA files to monthly ECSV files.
There are two issues to solve:
* Detect change of monthly IDA files (most likely metadata)
* Supply '`Position` coordinates when needed if the IDA monthly file doesn't provide them.

## IDA Monthly Files change

Computing Sun & Moon data for a monthly file takes about 1-2 minutes, depending on the file size and computer. This must be multiplied
for the number of downloaded files. This must be done the first time the files are downloaded. 
However, unnecesary recalculations should be avoided when re-runing the pipeline. The problem is that IDA monthly files may change 
in our NextCloud Server, most likely by updating observer, location or position metadata.

To avoid the lengthy computations, the pipeline always download the files (unless instructed not to do so) 
and compare an MD5 sum of these files against stored MD5 sums of previous downloads. 
For each file, if they match, there is no change and we skip the lengthy computation.

## Managing Position.

The pipeline will stop if it detects that there is not known Position during the Sun & Moon data computation.
If you happen to know an approximated Position for the photometer with enough accuracy for your purpose, you may enter it
in the database.

### Entering new position

1. Enter new cordinates in the database

```bash
tess-ida-db --console coords add --name stars4 --latitude 40.5 --longitude -3.1 --height 650
```

2. Then, re-run the pipeline with the `--fix` flag

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars4 -s 2024-03 -u 2024-06 -i IDA -o ECSV --fix
```

### Modifing position

1. Modify cordinates in the database

```bash
tess-ida-db --console coords update --name stars4 --latitude 40.8 --longitude -3.15 --height 690
```

2. ***Delete al related ECSV files !***

```bash
rm -fr ECSV/stars4/*.ecsv
```

3. Then, re-run the pipeline with the `--fix` flag

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars4 -s 2024-03 -u 2024-06 -i IDA -o ECSV --fix
```


### Deleting position

You probably want this once you know that the IDA monthly files incorporate Position metadata in the header


1. Delete coordinates from the database

```bash
tess-ida-db --console coords delete --name stars4
```

2. ***Delete al related ECSV files !***

```bash
rm -fr ECSV/stars4/*.ecsv
```

3. Then, re-run the pipeline ***without*** the  `--fix` flag

```bash
(.venv)  jupyter$  tess-ida-pipe --console range -n stars4 -s 2024-03 -u 2024-06 -i IDA -o ECSV
```
