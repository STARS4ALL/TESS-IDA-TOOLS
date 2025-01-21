"""
This test module only test the Command Line Interface, with its various options.
The command output is written to a separate log file so that stdout is clean for unittest.

From the project base dir dir, run as:

    python -m unittest -v test.test_cli.TestDownload
    python -m unittest -v test.test_cli.TestECSV
    python -m unittest -v test.test_cli.TestPipeline
    <etc>

or the complete suite:

    python -m unittest -v test.test_cli

"""

import unittest
from shlex import split
from subprocess import run

import decouple

class TestDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        run(split(f"touch {cls.log}"))
        run(split(f"truncate --size 0 {cls.log}"))

    def test_1_single(self):
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} single -n stars289 -m 2023-06 -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_2_exact(self):
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} single -n stars201 -e stars201_2020-02_-1.dat -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} single -n stars201 -e stars201_2020-02_61.dat -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_3_range(self):
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} range -n stars289 -s 2023-06 -u 2023-09 -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_4_phot_list(self):
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} photometers --list 1 5 33 44 85 -s 2022-01 -u 2022-05 -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_5_phot_range(self):
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} photometers --range 300 305 -s 2022-01 -u 2022-05 -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_6_phot_near(self):
        result = run(
            split(
                f"tess-ida-get --log-file {self.log} near -lo -3.703790 -la 40.416775 -ra 50 -o IDA"
            )
        )
        self.assertEqual(result.returncode, 0)


class TestECSV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        run(split(f"touch {cls.log}"))
        run(split(f"truncate --size 0 {cls.log}"))
        run(split("rm -fr ECSV"))

    def test_1_single(self):
        result = run(
            split(
                f"tess-ida-ecsv --log-file {self.log} single -n stars289 -m 2023-06 -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_2_exact(self):
        result = run(
            split(
                f"tess-ida-ecsv --log-file {self.log} single -n stars201 -e stars201_2020-02_-1.dat -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-ecsv --log-file {self.log} single -n stars201 -e stars201_2020-02_61.dat -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_3_range(self):
        result = run(
            split(
                f"tess-ida-ecsv --log-file {self.log} range -n stars289 -s 2023-06 -u 2023-09 -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_4_combine(self):
        result = run(
            split(
                f"tess-ida-ecsv --log-file {self.log} combine -n stars289 -s 2023-06 -u 2023-09 -i IDA -on out.ecsv"
            )
        )
        self.assertEqual(result.returncode, 0)


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        run(split(f"touch {cls.log}"))
        run(split(f"truncate --size 0 {cls.log}"))
        run(split("rm -fr IDA ECSV"))

    def test_1_single(self):
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} single -n stars289 -m 2023-06 -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_2_exact(self):
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} single -n stars201 -e stars201_2020-02_-1.dat -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} single -n stars201 -e stars201_2020-02_61.dat -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_3_range(self):
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} range -n stars289 -s 2023-06 -u 2023-09 -i IDA -o ECSV -on output.ecsv"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_4_photometers_range(self):
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} photometers -r 1 5  2017-06 -u 2017-09 -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_5_photometers_list(self):
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} photometers -l 1 5 -s 2017-06 -u 2017-09 -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_6_photometers_near(self):
        result = run(
            split(
                f"tess-ida-pipe --log-file {self.log} near -lo -3.703790 -la 40.416775 -ra 50 -s 2017-06 -u 2017-09 -i IDA -o ECSV"
            )
        )
        self.assertEqual(result.returncode, 0)


class TestDBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        run(split(f"rm -fr {decouple.config('DATABASE_FILE')}"))

    def test_1_schema_create(self):
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose schema create"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_2_coords_add(self):
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords add -n stars200 -lo -3.5 -la 40.5 -he 650"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords add -n stars201 -lo -2 -la 41.2 -he 300"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_3_coords_list(self):
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords list -n stars200"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords list"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_4_coords_update(self):
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords update -n stars200 -lo 3.5 -la 40.8 -he 0"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords list"
            )
        )
        self.assertEqual(result.returncode, 0)

    def test_5_coords_delete(self):
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords delete -n stars200"
            )
        )
        self.assertEqual(result.returncode, 0)
        result = run(
            split(
                f"tess-ida-db --log-file {self.log} --verbose coords list"
            )
        )
        self.assertEqual(result.returncode, 0)



if __name__ == "__main__":
    unittest.main()
