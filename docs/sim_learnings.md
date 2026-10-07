# xschem + ngspice (sky130) simulation learnings

Collected from asic-radio (ttsky26d) and mini-mosbius-configurator. These were
found the hard way; each one cost time at least once. Tool versions:
IIC-OSIC-TOOLS `hpretl/iic-osic-tools:2026.05` (ngspice 46, xschem 3.4.x),
sky130A, run headless in Docker.

## Speed

- **`.spiceinit` is read only from ngspice's current directory.** Keep one
  tracked file and copy it to wherever ngspice runs (for example `build/`). A
  wrapper script that does the copy on every run stops it drifting.
  ```
  set skywaterpdk
  set ng_nomodcheck
  set num_threads=8
  option noinit
  ```
- **`option klu` breaks `.noise`** in ngspice 46 ("Noise simulation is not
  (yet) supported with 'option KLU'"). Keep it out of the shared `.spiceinit`;
  put `.options klu` only in decks that are big transients with no noise
  analysis.
- **Never `set ngbehavior=hsa`.** It changes the default element scale
  factor. Bin selection then fails for the binned HV FET models
  (`sky130_fd_pr__nfet_g5v0d10v5` / `pfet_g5v0d10v5`, which the TT pad model
  uses), with "could not find a valid modelname".
- **Loading the model library is a fixed cost for every ngspice process.**
  The sky130 combined lib parse is ~15–25 s here and ~2 min reported elsewhere
  ([IIC-OSIC-TOOLS#262](https://github.com/iic-jku/IIC-OSIC-TOOLS/issues/262)).
  So sweep inside one process:
  ```
  foreach w 10 20 40
    alterparam w_dp = $w
    reset
    ac lin 1 433.92e6 433.92e6
    ...
    destroy all
  end
  ```
  `alterparam` needs `reset` to take effect. `destroy all` stops plots piling
  up in memory.
- **Don't run several ngspice processes in parallel blindly.** Each one starts
  `num_threads` OpenMP threads. Six processes on 8 cores gave a load average
  of 48, and nothing finished in 48 min. Run in sequence, or cut
  `num_threads`. Check with `uptime`.
- **`.save` only the vectors you measure in long transients.** For example,
  3 µs at 50 ps is 60k points × every node. With `.save v(det) v(out_p)
  v(out_n)` and one process at a time, it ran in ~47 s per case.
- **Floating nodes make it slow.** A node with no DC path made the operating
  point re-solve at every sweep point: 123 s against 25 s. Check that every
  node has a DC path to a source. Gates and capacitors don't count; MOSFET
  D-S-B and inductors do.
- **Avoid extreme resistor ratios.** 1e-12 Ω / 1e12 Ω ties hung ngspice for
  50+ min; 1 Ω / 1e9 Ω ran in seconds. ngspice also silently swaps a 0 Ω
  resistor for 1e-12.
- **Small probe first:** time a short run (e.g. 0.2 µs instead of 3 µs) and
  extrapolate before committing to a long one.

## Watching a running ngspice

- **Batch mode reports progress.** ngspice writes `Reference value : <x>`
  (sim time, or frequency for AC) with carriage returns. Log to a file, don't
  pipe to grep, then:
  ```
  tr '\r' '\n' < run.log | grep Reference | tail -1
  ```
  No Reference line yet means it's still loading models.
- `ps -o etime,time,pcpu,rss -C ngspice` shows CPU time and memory. Flat RSS
  says nothing about progress when you aren't saving many vectors.
- **Killing jobs:**
  - `pkill -f "<pattern>"` also matches the shell running the pkill if the
    pattern is in its command line. Kill by PID.
  - A Docker container outlives a killed wrapper shell: `docker ps`, then
    `docker kill <id>`.
- **Don't edit a shell script while it's running.** Bash reads scripts from
  disk as it goes. A killed child returns control, and bash carries on at the
  old byte offset in the *new* file. Here that re-launched the whole Docker
  job.

## xschem

- Netlist headless: `xschem -n -s -q -o build tb.sch`. **Check the netlist
  for `IS MISSING`**; the exit code doesn't tell you.
- **Property values can't contain `{}`.** Use ngspice `'expr'` quoting:
  `value='rl_dp'`, `W='w*(1+mm/2)'`.
- **A double quote inside a code block (`value="..."`) truncates the block**
  in the netlist. The usual sign is ngspice's "Missing .endc". Write `echo`
  without quotes: `echo $p $&avg`.
- **Subcircuit parameters:**
  - In the symbol, set `format="@name @pinlist @symname w=@w rl=@rl"` and
    `template="name=x1 w=20 rl=4k"`.
  - xschem puts the template defaults on the `.subckt` line. Instances
    override them (`w='w1'` can refer to a testbench `.param`).
  - Inside the subcircuit, use `'w'`.
- Ports and labels connect by name (`lab=`). A port symbol needs no wire.
- **No dots in top-level net names:** they clash with ngspice's `x1.node`
  hierarchy syntax.
- sky130 MOS symbols:
  - `W` is the *total* width (split over `nf` fingers); `mult` multiplies the
    device.
  - Narrow fingers carry noticeably less current per µm.
  - Instance names get the `X` spiceprefix: `M1` becomes `XM1`, and internal
    nodes are `x1.node`.
- Corners: put `corner.sym` in the schematic and rewrite the `.lib ... tt`
  line in the generated netlist to sweep `ss/ff/sf/fs`. That leaves the
  committed schematics at tt.

## ngspice control language traps

- **`print -i(v1) v(a)` merges into one expression** (`-i(v1) - v(a)`). Use
  `let x = -i(v1)` and print plain names.
- **Vectors belong to a plot.** After a new analysis, the old plot's vectors
  are no longer visible. Echo or compute what you need before running the
  next analysis.
- **Noise plot names count up** across analyses (`noise1` … `noise4`), so
  `setplot noise1` breaks. After `noise ... dec ...`, the current plot is the
  integrated one, so use `setplot previous` for the spectrum. A single-point
  `noise ... lin 1 f f` makes no integrated plot: the spectrum is already
  current.
- **`if $var = string` doesn't work** for string compares. Structure the loop
  so you don't need it (`alterparam $what = $&val` works).
- **Join echo output onto one line:** `echo "$a" NOEOL`, then
  `sed -z "s/ NOEOL\n/ /g"` on the output.
- **Temperature in a control loop:** `option temp = 60` *after* `reset`.
  `set temp = 60` is silently ignored, and an `option temp` before `reset`
  gets reset.
- **`meas ... rise=N` counts from the first saved point** (`tstart` of
  `tran`). Make sure edge N falls inside the run.
- **`destroy all` deletes vectors, including `meas` results.** Keep values
  you need later in control variables: `let x = vth` then `set xs = $&x`,
  then use `$xs` (even inside `alter @v[pulse] = [ $lo $hi ... ]`).
- `$&vec` puts a vector's value into a string; `{$t}` puts a loop variable
  into a node name: `v({$t}p)`.
- **Switch AC sources in one run instead of separate decks:**
  ```
  alter @vant_p[acmag]=0
  alter @vcmi[acmag]=1      * then: common-mode run, PSRR run, ...
  ```
- **Measures:** `meas tran x pp v(a) from= to=`; also `avg`, `rms`,
  `find v(a) at=`. An AC measure needs `let g = db(...)` first.
- **`trnoise` + clocked sources = "timestep too small"** when a source edge
  lands on trnoise's sample grid (a breakpoint every NT, e.g. 50 ps): two
  breakpoints a rounding error apart. Offset every pulse/PWL edge by NT/2
  (e.g. `pulse(0 1.8 25p ...)`). Also: a hard ternary in a B-source (`a ? 1
  : -1`) is better written as `tanh(k*x)` at ps timesteps.
- **`.options interp`** + `tran <tstep> ... <tmax>` saves output only on the
  tstep grid while the solver still steps at tmax. That's how 400 µs at 50 ps
  steps gives a 2 MB raw file.
- **`trnoise` isn't repeatable:** `.options seed`, `set rndseed` in .control
  and rndseed in .spiceinit were all ignored. For repeatable transient noise
  (so a signal can be found by difference), generate PWL sources in Python
  from a fixed seed. Per-sample σ = d / √(2T) for one-sided density d at
  sample period T.
- **ngspice-44.2** (`iic-osic-tools:2025.07`) has a bogus fatal error,
  `Pclm ... is not positive`; ngspice 46 (`2026.05`) is fine. Pin the image
  tag; `:latest` can resolve to an old cached image.
- The OSDI load errors from the image's global spiceinit are harmless.

## Noise analysis recipes

- **Comparator/amp decision noise = `onoise_total` / DC gain**, not
  `inoise_total`. `inoise_total` integrates the input-referred density over
  the whole sweep. Above the amp's pole the gain is tiny, so that density
  explodes, and band-limiting looks like it *adds* noise (0.31 mV → 1.85 mV
  here, where the real figure went 83 µV → 28 µV).
- After `noise ... dec ...`, the *current* plot holds the totals
  (`onoise_total`, `inoise_total`); `setplot previous` is the spectrum.

- **NF from the noise analysis:**
  `NF = 10·log10(onoise² / (|G|² · 4kT·Rs))`. G is the AC gain from source
  EMF to the output; T = 300.15 K (ngspice's default 27 °C). The source
  resistor's own noise is included in onoise.
- **For a symmetric differential circuit fed by two antiphase sources**,
  `inoise_spectrum` referred to *one* of them equals the noise per volt of
  differential EMF. That gives a one-line NF inside a sweep.
- **Per-device noise contributions:** a summary on a single point,
  `noise v(out) vsrc lin 1 f f 1`, then `print all`.
  - The entries are `onoise_<dev>` in V/√Hz (square them to add).
  - MOSFETs give a total `onoise.m.x1.xm1.msky130...` plus sub-terms (`.id`
    thermal, `.1overf` flicker, `.rbpb`, ...). Don't sum the total and the
    sub-terms.
- **sky130 `nfet_01v8` flicker noise is still significant at hundreds of
  MHz** in the models (~40 % of a min-L input pair's noise at 434 MHz);
  `pfet_01v8` shows almost none. Even so, a wider or higher-current NMOS pair
  beat a PMOS pair on NF at RF.

## Python side

- Read raws with a small binary/ASCII raw reader (asic-radio
  `tools/rawread.py`). Keep plotting in the host venv (numpy, matplotlib),
  not the container.
- NumPy 2: `np.trapz` is gone, use `np.trapezoid`.
- Generate schematics from Python (asic-radio `tools/xsch.py`): place
  symbols, then put `lab_pin`s exactly on pin coordinates. It's repeatable,
  diffable, and parameter sweeps don't need GUI edits.

## Silicon vs sim (ring oscillators)

- **tt08/ttsky25b ring** (18 × inv_2 + nand2_2, extracted): 598 MHz at tt
  extracted, measured 518 MHz, so ×0.866. That's between tt (598) and ss
  (495). It isn't temperature (+0.5 % from 27 to 60 °C at 1.8 V) and it isn't
  VDD (good on the demoboards). Use it as the empirical sim → silicon factor
  for new rings.

## Silicon vs sim (mini-mosbius)

- The chip measured was an **ss** part: ring 11 % slow, inverter gain 17 %
  high, both explained by the corner. Fitting the corner took **both**
  circuits:
  - an inverter's trip point pins the N/P strength ratio (fs/sf);
  - a ring's frequency pins speed (barely separates fs from tt).
- Routed parasitics matter: real bus-wire capacitance took a ring from
  ~93 MHz down to ~38 MHz (measured ~30 MHz).
