------------------------------------------------------------
--          TESS IDA TOOLS ADMINISTRATIVE DATA MODEL
------------------------------------------------------------

BEGIN TRANSACTION;

-- --------------------------------------------------------
-- Optimizing ECSV computation when including Sun/Moon data
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS ecsv_t
(
    filename       TEXT NOT NULL,  -- without path (i.e stars1-2024-01.dat)
    hash           TEXT NOT NULL,  -- printable version of MD5 hash
    UNIQUE(hash),                  -- No two files should have the same hash
    PRIMARY KEY(filename)
);

-- -----------------
-- Coordinates table
-- -----------------

CREATE TABLE IF NOT EXISTS coords_t
(
    phot_name       TEXT NOT NULL, 
    longitude       REAL NOT NULL,          --  [degrees]
    latitude        REAL NOT NULL,          --  [degrees]
    height          REAL NOT NULL,          -- meters above sea level [meters]
    PRIMARY KEY(phot_name)
);

COMMIT;
