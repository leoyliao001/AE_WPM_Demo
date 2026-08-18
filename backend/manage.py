#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import socket
import sys


# Port policy on this box (see E:\Apps\DEPLOYMENT.md):
#   8000 -> production Windows service AE_WPM (Waitress + MSSQL), owned by SYSTEM
#   8001 -> local development (`runserver` + SQLite)
# `runserver` with no address defaults to 8001 so a bare `manage.py runserver`
# can never collide with the running service.
DEV_DEFAULT_ADDRPORT = "127.0.0.1:8001"

# Base management options that consume the following argv token, so a value
# like the "2" in `-v 2` is not mistaken for an address.
_OPTIONS_WITH_VALUE = {"-v", "--verbosity", "--settings", "--pythonpath"}


def _find_addrport(args):
    """Index of the positional addrport in `args`, or None if not given."""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in _OPTIONS_WITH_VALUE:
            i += 2
        elif arg.startswith("-"):
            i += 1
        else:
            return i
    return None


def _split_addrport(addrport, use_ipv6):
    """Best-effort (host, port) split matching runserver's own parsing."""
    if addrport.startswith("["):  # [::1]:8001
        host, _, port = addrport.partition("]")
        return host[1:], (port.lstrip(":") or "8000")
    if ":" in addrport:
        host, _, port = addrport.rpartition(":")
        return host, port
    if addrport.isdigit():
        return ("::1" if use_ipv6 else "127.0.0.1"), addrport
    return addrport, "8000"


def _is_listening(host, port):
    if host in ("", "0.0.0.0", "::"):
        host = "127.0.0.1"
    try:
        port = int(port)
    except ValueError:
        return False
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _check_runserver_port(argv):
    """Default the dev port and refuse to start on an occupied one.

    Windows lets a second process bind an address that is already being
    listened on, so `runserver` starts silently next to the AE_WPM service
    instead of failing. Requests are then split unpredictably between two
    backends running different code against different databases. Fail loudly.
    """
    if len(argv) < 2 or argv[1] != "runserver":
        return

    args = argv[2:]
    use_ipv6 = "-6" in args or "--ipv6" in args
    index = _find_addrport(args)
    if index is None:
        addrport = DEV_DEFAULT_ADDRPORT
        argv.append(addrport)
    else:
        addrport = args[index]

    # Only the outer process checks: under autoreload the child (RUN_MAIN=true)
    # is the one that binds, and it restarts after the previous child is gone.
    if os.environ.get("RUN_MAIN") == "true":
        return

    host, port = _split_addrport(addrport, use_ipv6)
    if not _is_listening(host, port):
        return

    sys.stderr.write(
        "\n"
        "ERROR: {host}:{port} is already being listened on. Refusing to start.\n"
        "\n"
        "Windows allows a second process to bind a port that is already in use,\n"
        "so runserver would start without any error and requests would be split\n"
        "at random between the two backends -- which looks like 'my code changes\n"
        "do nothing' or 'the data keeps coming and going'.\n"
        "\n"
        "Find the current owner of the port:\n"
        "  Get-NetTCPConnection -LocalPort {port} -State Listen |\n"
        "    ForEach-Object {{ Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.OwningProcess)\" }} |\n"
        "    Select-Object ProcessId, CommandLine\n"
        "\n"
        "Port policy: 8000 = production service AE_WPM (Waitress + MSSQL),\n"
        "             8001 = local development (runserver + SQLite).\n"
        "To work against the production backend, do not start a second server --\n"
        "point the frontend at it instead:\n"
        "  $env:VITE_API_TARGET = 'http://127.0.0.1:8000'; npm run dev\n"
        "\n".format(host=host, port=port)
    )
    sys.exit(1)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    _check_runserver_port(sys.argv)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
