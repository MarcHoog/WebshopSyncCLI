#!/usr/bin/env python3
"""
Systemd Job Generator for Syncly CLI

This script creates systemd service and timer files for scheduling Syncly sync operations
on Ubuntu/Debian servers. It supports all available sync commands and provides flexible
scheduling options.

Usage:
    python create_systemd_jobs.py --help

Example:
    # Create a daily Hydrowear sync at 2 AM
    python create_systemd_jobs.py \
        --name hydrowear-daily \
        --command "ccv sync-hydrowear" \
        --schedule "daily" \
        --time "02:00" \
        --env-file /etc/syncly/env

    # Create a Mascot sync every 6 hours
    python create_systemd_jobs.py \
        --name mascot-sync \
        --command "ccv sync-mascot" \
        --schedule "every-6-hours"
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional


SCHEDULE_PRESETS = {
    "hourly": "OnCalendar=hourly",
    "daily": "OnCalendar=daily",
    "weekly": "OnCalendar=weekly",
    "monthly": "OnCalendar=monthly",
    "every-6-hours": "OnCalendar=*-*-* 00,06,12,18:00:00",
    "every-4-hours": "OnCalendar=*-*-* 00,04,08,12,16,20:00:00",
    "every-2-hours": "OnCalendar=*-*-* 00/2:00:00",
    "every-30-minutes": "OnCalendar=*:0/30",
}


def generate_service_file(
    name: str,
    command: str,
    description: str,
    working_dir: str,
    user: str,
    env_file: Optional[str] = None,
    python_path: Optional[str] = None,
    extra_args: Optional[str] = None,
) -> str:
    """Generate a systemd service file content."""

    # Determine the syncly command path
    if python_path:
        syncly_cmd = f"{python_path} -m syncly.cli"
    else:
        syncly_cmd = "syncly"

    # Build the full command
    full_command = f"{syncly_cmd} {command}"
    if extra_args:
        full_command += f" {extra_args}"

    # Build environment section
    env_section = ""
    if env_file:
        env_section = f"EnvironmentFile={env_file}\n"

    service_content = f"""[Unit]
Description={description}
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User={user}
WorkingDirectory={working_dir}
{env_section}ExecStart={full_command}

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=syncly-{name}

# Security hardening
PrivateTmp=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={working_dir}

# Restart policy
Restart=on-failure
RestartSec=30s

[Install]
WantedBy=multi-user.target
"""
    return service_content


def generate_timer_file(
    name: str,
    description: str,
    schedule: str,
    time: Optional[str] = None,
    persistent: bool = True,
) -> str:
    """Generate a systemd timer file content."""

    # Determine the schedule string
    if schedule in SCHEDULE_PRESETS:
        schedule_line = SCHEDULE_PRESETS[schedule]
        # Override time if specified for preset schedules
        if time and schedule in ["daily", "weekly", "monthly"]:
            schedule_line = f"OnCalendar={schedule.capitalize()} {time}"
    else:
        # Custom schedule
        schedule_line = f"OnCalendar={schedule}"

    # Add time if specified and not already in schedule
    if time and "OnCalendar=" in schedule_line and time not in schedule_line:
        # Parse and modify the OnCalendar line
        if schedule_line == "OnCalendar=daily":
            schedule_line = f"OnCalendar=daily {time}"

    persistent_line = "Persistent=true" if persistent else "Persistent=false"

    timer_content = f"""[Unit]
Description={description} Timer
Requires={name}.service

[Timer]
{schedule_line}
{persistent_line}
AccuracySec=1m

[Install]
WantedBy=timers.target
"""
    return timer_content


def write_systemd_files(
    name: str,
    service_content: str,
    timer_content: str,
    output_dir: Optional[Path] = None,
    install: bool = False,
) -> tuple[Path, Path]:
    """Write service and timer files to disk."""

    if output_dir is None:
        if install and os.geteuid() == 0:
            # Root user - install to system directory
            output_dir = Path("/etc/systemd/system")
        elif install:
            # Non-root user - install to user directory
            output_dir = Path.home() / ".config" / "systemd" / "user"
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Just output to current directory
            output_dir = Path.cwd()

    service_file = output_dir / f"syncly-{name}.service"
    timer_file = output_dir / f"syncly-{name}.timer"

    # Write files
    service_file.write_text(service_content)
    timer_file.write_text(timer_content)

    print(f"✓ Created service file: {service_file}")
    print(f"✓ Created timer file: {timer_file}")

    return service_file, timer_file


def install_systemd_jobs(service_file: Path, timer_file: Path, user_mode: bool = False):
    """Install and enable systemd service and timer."""
    import subprocess

    systemctl_cmd = ["systemctl"]
    if user_mode:
        systemctl_cmd.append("--user")

    try:
        # Reload systemd
        subprocess.run(systemctl_cmd + ["daemon-reload"], check=True)
        print("✓ Reloaded systemd daemon")

        # Enable the timer
        timer_name = timer_file.name
        subprocess.run(systemctl_cmd + ["enable", timer_name], check=True)
        print(f"✓ Enabled timer: {timer_name}")

        # Start the timer
        subprocess.run(systemctl_cmd + ["start", timer_name], check=True)
        print(f"✓ Started timer: {timer_name}")

        # Show status
        print("\nTimer status:")
        subprocess.run(systemctl_cmd + ["status", timer_name, "--no-pager"], check=False)

    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing systemd jobs: {e}", file=sys.stderr)
        print("\nYou may need to manually run:")
        if user_mode:
            print(f"  systemctl --user daemon-reload")
            print(f"  systemctl --user enable {timer_file.name}")
            print(f"  systemctl --user start {timer_file.name}")
        else:
            print(f"  sudo systemctl daemon-reload")
            print(f"  sudo systemctl enable {timer_file.name}")
            print(f"  sudo systemctl start {timer_file.name}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate systemd service and timer files for Syncly sync operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Schedule Presets:
  hourly            - Run every hour
  daily             - Run once per day (default: midnight)
  weekly            - Run once per week
  monthly           - Run once per month
  every-6-hours     - Run every 6 hours
  every-4-hours     - Run every 4 hours
  every-2-hours     - Run every 2 hours
  every-30-minutes  - Run every 30 minutes

Available Sync Commands:
  ccv sync-hydrowear     - Sync HydroWear CSV to CCV Shop
  ccv sync-mascot        - Sync Mascot data
  ccv create-attribute-set-from-txt - Create attribute set from TXT

Examples:
  # Daily Hydrowear sync at 2 AM
  python create_systemd_jobs.py \\
      --name hydrowear-daily \\
      --command "ccv sync-hydrowear" \\
      --schedule daily \\
      --time "02:00"

  # Mascot sync every 6 hours with custom arguments
  python create_systemd_jobs.py \\
      --name mascot-sync \\
      --command "ccv sync-mascot" \\
      --schedule every-6-hours \\
      --extra-args "--dry-run"

  # Custom schedule using systemd calendar syntax
  python create_systemd_jobs.py \\
      --name custom-sync \\
      --command "ccv sync-hydrowear" \\
      --schedule "*-*-* 06,18:00:00"
        """
    )

    # Required arguments
    parser.add_argument(
        "--name",
        required=True,
        help="Name for the systemd job (will be prefixed with 'syncly-')"
    )
    parser.add_argument(
        "--command",
        required=True,
        help="Syncly command to run (e.g., 'ccv sync-hydrowear')"
    )

    # Schedule arguments
    schedule_group = parser.add_argument_group("scheduling options")
    schedule_group.add_argument(
        "--schedule",
        required=True,
        help="Schedule preset or custom systemd OnCalendar expression"
    )
    schedule_group.add_argument(
        "--time",
        help="Time to run (HH:MM format, for daily/weekly/monthly schedules)"
    )
    schedule_group.add_argument(
        "--no-persistent",
        action="store_true",
        help="Disable persistent timers (don't run missed jobs after system boot)"
    )

    # Configuration arguments
    config_group = parser.add_argument_group("configuration options")
    config_group.add_argument(
        "--description",
        help="Description for the systemd service"
    )
    config_group.add_argument(
        "--working-dir",
        default=os.getcwd(),
        help="Working directory for the sync command (default: current directory)"
    )
    config_group.add_argument(
        "--user",
        default=os.getenv("USER", "root"),
        help="User to run the service as (default: current user)"
    )
    config_group.add_argument(
        "--env-file",
        help="Path to environment file with API keys and secrets"
    )
    config_group.add_argument(
        "--python-path",
        help="Path to Python interpreter (default: use installed syncly command)"
    )
    config_group.add_argument(
        "--extra-args",
        help="Additional arguments to pass to the sync command"
    )

    # Output arguments
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write service and timer files (default: current directory)"
    )
    output_group.add_argument(
        "--install",
        action="store_true",
        help="Install and enable the systemd timer (requires appropriate permissions)"
    )
    output_group.add_argument(
        "--user-mode",
        action="store_true",
        help="Install as user service (--user flag for systemctl)"
    )

    args = parser.parse_args()

    # Validate schedule
    if args.schedule not in SCHEDULE_PRESETS and not args.schedule.startswith("*"):
        print(f"Warning: '{args.schedule}' is not a preset schedule.", file=sys.stderr)
        print("It will be used as a custom OnCalendar expression.", file=sys.stderr)
        print(f"Available presets: {', '.join(SCHEDULE_PRESETS.keys())}", file=sys.stderr)
        print()

    # Generate description if not provided
    description = args.description or f"Syncly {args.command} sync job"

    # Generate service file
    service_content = generate_service_file(
        name=args.name,
        command=args.command,
        description=description,
        working_dir=args.working_dir,
        user=args.user,
        env_file=args.env_file,
        python_path=args.python_path,
        extra_args=args.extra_args,
    )

    # Generate timer file
    timer_content = generate_timer_file(
        name=args.name,
        description=description,
        schedule=args.schedule,
        time=args.time,
        persistent=not args.no_persistent,
    )

    # Write files
    service_file, timer_file = write_systemd_files(
        name=args.name,
        service_content=service_content,
        timer_content=timer_content,
        output_dir=args.output_dir,
        install=args.install,
    )

    # Install if requested
    if args.install:
        print()
        install_systemd_jobs(service_file, timer_file, user_mode=args.user_mode)
    else:
        print("\nTo install manually, run:")
        if args.user_mode or (not os.access("/etc/systemd/system", os.W_OK)):
            print(f"  mkdir -p ~/.config/systemd/user")
            print(f"  cp {service_file} {timer_file} ~/.config/systemd/user/")
            print(f"  systemctl --user daemon-reload")
            print(f"  systemctl --user enable {timer_file.name}")
            print(f"  systemctl --user start {timer_file.name}")
            print(f"  systemctl --user status {timer_file.name}")
        else:
            print(f"  sudo cp {service_file} {timer_file} /etc/systemd/system/")
            print(f"  sudo systemctl daemon-reload")
            print(f"  sudo systemctl enable {timer_file.name}")
            print(f"  sudo systemctl start {timer_file.name}")
            print(f"  sudo systemctl status {timer_file.name}")

    print("\nUseful commands:")
    systemctl_prefix = "systemctl --user" if args.user_mode else "sudo systemctl"
    print(f"  {systemctl_prefix} status syncly-{args.name}.timer    # Check timer status")
    print(f"  {systemctl_prefix} list-timers                        # List all timers")
    print(f"  {systemctl_prefix} start syncly-{args.name}.service   # Run sync manually")
    print(f"  journalctl -u syncly-{args.name}.service -f           # View logs")


if __name__ == "__main__":
    main()
