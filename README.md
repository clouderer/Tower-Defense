# Tower-Defense
A motherboard-inspired tower defense game called CPU Overload: Tower Defense where players defend digital pathways from waves of cyber threats using specialized defensive towers.

## Run the game

Use Python 3.10 or newer (verified with Python 3.12 and Pygame 2.6.1).
Run these commands from the `Tower-Defense` folder, using the Python
interpreter from your virtual environment:

```powershell
python -m pip install -r requirements.txt
python -m program_files.app
```

The entry point is `program_files.app`; the package itself has no
`__main__.py`. Pygame is the only runtime dependency. The tests use
Python's built-in `unittest`, so pytest is not required.

Choose **Play**, then the first map, to start the campaign. The separate
**Tutorial** button on map selection opens the guided lessons. During
gameplay, use Space or the bottom banner to start a ready wave, S or the
skip banner to start the next wave while existing enemies continue,
1–4 to select towers, Q to cancel placement, and P to pause or resume.

## Check code style

Install the development tools and run the PEP 8 checker:

```powershell
python -m pip install -r requirements-dev.txt
python -m pycodestyle tests tools --exclude=balance_results
```

The style settings use 79 characters for code and 72 for comments and
docstrings. To apply automatic formatting:

```powershell
python -m autopep8 --in-place --recursive tests tools --exclude balance_results
```

Use `python -m pycodestyle program_files` to check the game source too.
The tools check excludes archived balance experiments.

## Run regression checks

The checks cover the current app entry point, tutorial, real assets,
combat and boss shields, tower purchases/upgrades/sales, wave presets,
overlapping wave spawns and rewards, pause timers, and the automation
tools. To run them without opening a game window in PowerShell:

```powershell
$env:SDL_VIDEODRIVER = "dummy"
$env:SDL_AUDIODRIVER = "dummy"
python -m unittest discover -s tests -v
```

These environment variables apply to the current terminal. Before
launching the game or a visible playtest from that terminal, clear them:

```powershell
Remove-Item Env:SDL_VIDEODRIVER, Env:SDL_AUDIODRIVER -ErrorAction SilentlyContinue
```

## Run balance simulations

Run a full campaign through the actual gameplay updates with a simulated
clock. The tool buys towers automatically and reports health, money, and
the final defense:

```powershell
python -m tools.simulate_balance --strategy efficient
python -m tools.simulate_balance --strategy firewall
python -m tools.simulate_balance --strategy no-upgrades
python -m tools.simulate_balance --strategy mixed-upgrades --buy-during-wave `
    --output tools/balance_results/current/simulation.json
```

Other strategies are `bitblaster`, `clock-heavy`, `upgrade-focused`, and
`mixed-upgrades`.
The `upgrade-focused` strategy upgrades its starting Firewalls fully,
then builds and upgrades Clocks. To start with two Firewalls and buy
during combat:

```powershell
python -m tools.simulate_balance --strategy upgrade-focused `
    --starter-firewalls 2 --buy-during-wave
```

To compare a mixed defense that establishes Firewalls before investing
in Clock upgrades:

```powershell
python -m tools.simulate_balance --strategy mixed-upgrades --buy-during-wave
```

Use `--step-ms 17` to compare update timing. The optional
`--enemy-health-scale`, `--enemy-speed-scale`, and `--spawn-interval-ms`
arguments temporarily change the simulated difficulty without editing
the game. These repeatable build strategies help compare balance; they
do not measure how difficult the game feels to a person.

Simulation stats, prices, tower positions, and wave compositions come
from the current game code. `--output` saves JSON with the outcome,
live balance configuration, and a SHA-256 fingerprint of the game source.
`--max-seconds` limits simulated time; an unfinished run reports
`timeout` and exits with status 1. Victory and defeat are both completed
playtests and exit with status 0.

## Audit campaigns and compare builds

The audit records kills, leaks, boss shields and outcomes, per-wave
rewards, spending, and whether the money totals reconcile:

```powershell
python -m tools.audit_campaign --strategy mixed-upgrades `
    --output tools/balance_results/current/audit.json
python -m tools.audit_campaign --strategy mixed-upgrades --skip-waves `
    --output tools/balance_results/current/skipped_waves.json
python -m tools.compare_builds --switch-wave 7 --clock-level 2
python -m tools.compare_hybrids --switch-wave 7 --proxy-after 3 --buy-during-wave
```

The audit buys during combat. With `--skip-waves`, it presses S as soon
as skipping is available; earlier enemies and their spawn queues stay
active. Rewarded waves and completed waves are reported separately.
`compare_builds` varies the transition to Clocks, while `compare_hybrids`
adds planned Proxy purchases. Their options affect the buying policy,
not combat rules. Run any tool with `--help` for its arguments.

## Watch full campaign playtests

The visible runner opens the actual Pygame app and uses its normal menu,
placement, upgrade, and wave-start controls. It advances the same fixed
game updates between rendered frames to speed up a full campaign:

```powershell
python -m tools.play_balance --strategy mixed-upgrades `
    --output tools/balance_results/visible_good
python -m tools.play_balance --strategy efficient `
    --output tools/balance_results/visible_bad
```

Each output folder contains a frame for every completed wave, purchase
records, wave results, and a final summary. The runner uses normal money,
health, enemy stats, and tower costs. Closing its window stops the test.

To exercise those same menu, placement, upgrade, and draw paths without
opening a window:

```powershell
python -m tools.play_balance --strategy mixed-upgrades --headless `
    --output tools/balance_results/current/ui
```

Headless mode saves the same screenshots and reports and skips the
render-rate limit and final linger. The summary includes the current
configuration and source fingerprint, including on timeout. Automated
runners restore SDL environment settings and release Pygame resources
when they finish or fail.

Folders under `tools/balance_results` contain results from particular
runs. Older results and the one-off scripts in dated folders are
historical experiments; regenerate results with the tools above to
evaluate the current game.
