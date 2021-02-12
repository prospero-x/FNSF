### hPIC simulations on SOLPS

This project is to use hPIC simulations on the output of SOLPS data. The
overall project is the Fusion Nuclear Science Facility (FNSF).

Data will be send from Jeremy Lori who is modelling the Scrape Off Layer
(SOL). He will send us his output, which includes B field strength,
densities of deuterium and neon, and heat flux on the divertor surface.

We will use his data as input to hPIC in order to get a theta-E distribution
of particles

### Commands

To clean the data (convert it from Jeremy Lori's sent raw data to usable CSV):
```bash
./clean_data <PATH_TO_RAW_DATAFILE>
```

To configure simulations for a specific data set (inner SP or outer SP):
```bash
python configure_simulations solps_data/cleaned/solpsTargInner.csv
```

This creates an executable `solpsTargInner.sh` as well as a directory tree
in `hpic_results`. One subdirectory is created for every row in the SOLPS
data file, i.e. one subdir for every position relative to the SP.

To run the simulations for a specific data set (inner SP or outer SP), run:
```bash
./solpsTargInner.sh
```
