import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent

SCRIPTS = [
    "run_analysis.py",
    "parameter_sweep.py",
    "equal_budget.py",
    "figure_2_reference_profile.py",
    "figure_3_transmission_instants.py",
    "figure_4_periodic_reconstruction.py",
    "figure_5_event_reconstruction.py",
    "figure_6_reconstruction_errors.py",
    "figure_7_tradeoff.py",
]


def run_script(script_name: str) -> None:
    script_path = SCRIPT_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Script not found: {script_path}"
        )

    print()
    print("=" * 70)
    print(f"Running {script_name}")
    print("=" * 70)

    # Use a non-interactive Matplotlib backend so figure scripts
    # can run automatically without opening plot windows.
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"

    subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=SCRIPT_DIR,
        env=environment,
        check=True,
    )


def main() -> None:
    print("Starting complete reproducibility workflow.")

    for script_name in SCRIPTS:
        run_script(script_name)

    print()
    print("=" * 70)
    print("Workflow completed successfully.")
    print("=" * 70)
    print()
    print("Generated outputs:")
    print("  results/ - analysis CSV files")
    print("  figures/ - manuscript Figures 2-7")


if __name__ == "__main__":
    main()