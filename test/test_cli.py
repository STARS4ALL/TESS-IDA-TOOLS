"""
This test module only test the Command Line Interface, with its various options.
The command output is written to a separate log file so that stdout is clean for unittest.
"""
import unittest
from shlex import split
from subprocess import run


class TestDownload(unittest.TestCase):

    @classmethod 
    def setUpClass(cls):
        cls.log = f"{cls.__name__}.log"
        run(split(f"touch {cls.log}"))
        run(split(f"truncate --size 0 {cls.log}"))

    def test_single(self):
        result = run(split(f"tess-ida-get --log-file {self.log} single -n stars289 -m 2023-06 -o IDA"))
        self.assertEqual(result.returncode, 0)

    def test_specific(self):
        result = run(split(f"tess-ida-get --log-file {self.log} single -n stars201 -e stars201_2020-02_-1.dat -o IDA"))
        self.assertEqual(result.returncode, 0)
        result = run(split(f"tess-ida-get --log-file {self.log} single -n stars201 -e stars201_2020-02_61.dat -o IDA"))
        self.assertEqual(result.returncode, 0)

    def test_range(self):
        result = run(split(f"tess-ida-get --log-file {self.log} range -n stars201 -s 2022-01 -u 2022-05 -o IDA"))
        self.assertEqual(result.returncode, 0)

    def test_phot_list(self):
        result = run(split(f"tess-ida-get --log-file {self.log} photometers --list 1 5 33 44 85 -s 2022-01 -u 2022-05 -o IDA"))
        self.assertEqual(result.returncode, 0)

    def test_phot_range(self):
        result = run(split(f"tess-ida-get --log-file {self.log} photometers --range 300 305 -s 2022-01 -u 2022-05 -o IDA"))
        self.assertEqual(result.returncode, 0)

    def test_phot_near(self):
        result = run(split(f"tess-ida-get --log-file {self.log} near -lo -3.703790 -la 40.416775 -ra 50 -o IDA"))
        self.assertEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()