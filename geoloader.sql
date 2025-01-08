\set csv_file :csv_file

BEGIN;

-- Assuming the table Location already exists and has the appropriate structure

-- Use the \copy command to load data from the CSV file into a temporary table
CREATE TEMP TABLE temp_location (
    "criteria_id" INTEGER,
    "name" TEXT,
    "canonical_name" TEXT,
    "parent_id" TEXT,
    "country_code" TEXT,
    "target_type" TEXT,
    "status" TEXT
);

COPY temp_location("criteria_id", "name", "canonical_name", "parent_id", "country_code", "target_type", "status") FROM :'csv_file' DELIMITER ',' CSV HEADER;

-- Perform the UPSERT operation
-- Update the existing records if there's a conflict on the criteria_id (primary key)
-- If no conflict, insert the new record
INSERT INTO "location" ("criteria_id", "name", "canonical_name", "parent_id", "country_code", "target_type", "status")
SELECT
    "criteria_id",
    "name",
    "canonical_name",
    CASE
        WHEN "parent_id" = '' THEN NULL
        ELSE "parent_id"::INTEGER
    END AS "parent_id",
    "country_code",
    "target_type",
    "status"
FROM temp_location
ON CONFLICT ("criteria_id") DO UPDATE SET
  "name"          = EXCLUDED."name",
  "canonical_name" = EXCLUDED."canonical_name",
  "parent_id"      = EXCLUDED."parent_id",
  "country_code"   = EXCLUDED."country_code",
  "target_type"    = EXCLUDED."target_type",
  "status"         = EXCLUDED."status";

-- Drop the temporary table
DROP TABLE temp_location;

COMMIT;
