### hPIC simulations on SOLPS

This project is to use hPIC simulations on the output of SOLPS data. The
overall project is the Fusion Nuclear Science Facility (FNSF).

Data will be send from Jeremy Lori who is modelling the Scrape Off Layer
(SOL). He will send us his output, which includes B field strength,
densities of deuterium and neon, and heat flux on the divertor surface.

We will use his data as input to hPIC in order to get a theta-E distribution
of particles

### Requirements
- Python 3.8


### Setup

SHOULD run the following inside a virtualenv or pew environment
```bash
pip install -r requirements.txt
```

### Config
`config.yaml` can supply parameters to each hpic simulation. If specified,
these values will overrride hardcoded defaults.


### Commands

Assuming raw data is from Jeremy already exists, format the data first (convert it from Jeremy Lori's sent raw data to usable CSV):
```bash
scripts/format_data_files.sh solps_data/raw/solpsTargInner.txt
```
A new formatted pure CSV at the location `solps_data/formatted/solpsTargInner.csv`

To configure simulations for a specific data set (inner SP or outer SP):
```bash
scripts/configure_simulations.py
```

This creates an executable `scripts/run-hpic-olpsTargInner.sh` as well as a directory tree
in `hpic_results`. One subdirectory is created for every row in the SOLPS
data file, i.e. one subdir for every position relative to the SP.

To run the simulations for a specific data set (inner SP or outer SP), run:
```bash
scripts/run-hpic-solpsTargInner.sh
```

procedure:
1. choose ngyro
2. make 3-step mesh (pummi)
3. read nt and npart from hpic, use that to estimate total running time
4. do split_work
5. configure_simulations
5. scp scripts onto boxes and run


