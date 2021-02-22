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


## Step 1: Format SOLPS Data

Assuming raw data is from Jeremy already exists, format the data first (convert it from Jeremy Lori's sent raw data to usable CSV):
```bash
scripts/format_data_files.sh solps_data/raw/solpsTargInner.txt
```
A new formatted pure CSV at the location `solps_data/formatted/solpsTargInner.csv`

## Step 2: Choose a number for ngyro
Explore the deybe lengths and ion gyroradii of deuterium by running:

```bash
scripts/debye_length.py
scripts/gyroradius.py
```

Investigate these values for deuterium to determine how many deuterium gyroradii
we want in the simulation domain. Put that value in `config.yaml` under `ngyro`.

## Step 3: Estimate the amount of work for each simulation
We need to figure out how much work each hPIC simulation represents.
The total number of particle pushes in a simulation approximates the overall
work involved. To see this, modify the `hpic` executable:

Place the following code in `hPIC/hpic_1d3v/main.c`, **after** `hpic_initialize`
has been called, but **before** the loop over time steps:
```c
u_int64_t Npart = hpic->param.Npart;
u_int64_t Nt = hpic -> param.time_steps;
printf("%ld\n", Nt * Npart);
exit(0);
```

Next, recompile `hpic`.

, run the following commands:
```bash
$ python scripts/configure_simulations.py configure_total_pushes
$ scripts/get_total_pushes.sh > total_pushes.csv
```

**Important** go back and revert `hPIC/hpic_1d3v/main.c` to its original state and
recompile.

## Step 4: Assign workloads to all machines involved in hpic simulations
Modify `MACHINE_BANDWIDTHS` in `scripts/assign_workloads.py`. To do this, first
ollect a list of all machines which will be used to run the hPIC sims
in parallel. Then, determine the fraction of the total workload which
should be assigned to each machine. One heuristic to determine these values
is the following:

```bash
If Box Bi can run a single hPIC simulation at speed vi (particles/second),
then it should be assigned vi/sum_i^n(vi) fraction of the work.

But what if Bi has M cores? then it can process M*vi particles/second.
Therefore it should be assigned M*vi/sum_i^n(M*vi) fraction of the work.
```

After modifying `MACHINE_ASSIGNMENTS`, run:

```bash
$ python scripts/assign_workloads.py total_pushes.csv
```

## Step 5: Configure hPIC simulations
```bash
$ python scripts/configure_simulations.py
```

## Step 6: Send the hPIC scripts to each machine
This assumes that your ssh key is on LCPP machines so that you can
ssh without a password.

Make sure each LCPP host signifier is in `remote_scripts/lcpp_hosts.txt`.
Each line  should contain a value such that ssh onto that LCPP box is
possible by running `$ ssh <VALUE>`.

```bash
cd remote_scripts
./run_cmd_on_all_hosts.sh mkdir my-hpic-sims
./send_files_to_all_hosts.sh my-hpic-sims
```

# Step 7: Start the simulations
ssh onto each box and run:

```bash
nohup my-hpic-sims/run_hpic_fnsf_solps_<HOSTNAME>.sh &
```

verify that they're running with `htop` and `ps`

# Step 8: Check status of running simulations

On your own box, run:

```bash
cd remote_scripts
./run_cmd_on_all_hosts.sh cd my-sim-dir \;./check_status.sh
```

# Step 9: Once hPIC simulations are complete, send files back to yourself:
```bash
cd remote_scripts
./run_cmd_on_all_hosts.sh cd my-sim-dir\; ./send_results_to_mikhail.sh
```
