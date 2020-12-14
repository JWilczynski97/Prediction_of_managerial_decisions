/*
Created: 13.12.2020
Modified: 14.12.2020
Model: Physical Model
Database: SQLite 3.7
*/

-- Create tables section -------------------------------------------------

-- Table UCL_Matches

CREATE TABLE UCL_Matches
(
  UCL_Match_ID NUMERIC NOT NULL,
  Team_1_ID INTEGER NOT NULL,
  Team_2_ID INTEGER NOT NULL,
  Season TEXT NOT NULL,
  UCL_Match_WhoScored_ID INTEGER NOT NULL,
  Date TEXT NOT NULL,
  Centre_file TEXT NOT NULL,
  Preview_file TEXT NOT NULL,
  Link TEXT NOT NULL,
  CONSTRAINT Unique_Identifier2 PRIMARY KEY (UCL_Match_WhoScored_ID)
)
;

-- Table Matches

CREATE TABLE Matches
(
  Match_ID NUMERIC NOT NULL,
  Team_1_ID TEXT NOT NULL,
  Team_2_ID TEXT NOT NULL,
  Season TEXT NOT NULL,
  League TEXT NOT NULL,
  Match_WhoScored_ID INTEGER NOT NULL,
  Date TEXT NOT NULL,
  Centre_file TEXT NOT NULL,
  Preview_file TEXT NOT NULL,
  Link TEXT NOT NULL,
  CONSTRAINT Unique_Identifier3 PRIMARY KEY (Match_WhoScored_ID)
)
;

-- Table Teams

CREATE TABLE Teams
(
  Team_ID INTEGER NOT NULL,
  Team_name TEXT NOT NULL,
  League TEXT NOT NULL,
  Link TEXT NOT NULL,
  CONSTRAINT Unique_Identifier4 PRIMARY KEY (Team_ID)
)
;

-- Table UCL_Matches_Matches

CREATE TABLE UCL_Matches_Matches
(
  UCL_Match_WhoScored_ID INTEGER NOT NULL,
  Match_WhoScored_ID INTEGER NOT NULL
)
;

