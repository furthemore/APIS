import enum
import errno
import fcntl
import os
import pathlib
import shutil
import subprocess
import sys


@enum.unique
class DatabaseStatus(enum.Enum):
    UNKNOWN = enum.auto()
    DOES_NOT_EXIST = enum.auto()
    DIRECTORY_EMPTY = enum.auto()
    INVALID_DIRECTORY = enum.auto()
    STOPPED = enum.auto()
    RUNNING = enum.auto()


class MissingExecutable(Exception):
    def __init__(self, executable: str):
        self.message = f"Unable to find system executable: {executable}"


class Postgres:
    """
    Utility class for interacting with Postgres databases.
    """
    def __init__(self, db_path_str: str):
        self.db_path = pathlib.Path(db_path_str).absolute()

        pg_ctl = shutil.which("pg_ctl")
        if not pg_ctl:
            raise MissingExecutable("pg_ctl")
        self.pg_ctl = pg_ctl

        createdb = shutil.which("createdb")
        if not createdb:
            raise MissingExecutable("createdb")
        self.createdb = createdb

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        """
        Run a process given a list of arguments.

        Rather than use subprocess.run, we have to jump through a few
        extra hoops to ensure that we don't hit the deadlock when using pipes.
        """
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            close_fds=True,
            text=True,
        )

        # Wait for the process to finish
        while proc.poll() is None:
            pass

        stdout_fd = proc.stdout.fileno()

        # Set the process' stdout file descriptor to non-blocking
        flags = fcntl.fcntl(stdout_fd, fcntl.F_GETFL)
        fcntl.fcntl(stdout_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Read all the data from stdout
        stdout_data = ""
        while True:
            try:
                data = os.read(stdout_fd, 10)
            except OSError as exc:
                if exc.errno == errno.EAGAIN:
                    break
                else:
                    raise

            if not data:
                break

            stdout_data += data.decode("utf-8")

        return subprocess.CompletedProcess(
            args=args,
            returncode=proc.returncode,
            stdout=stdout_data,
            stderr="",
        )

    def init(self) -> str:
        """
        Creates a new Postgres instance.
        """
        if not self.db_path.exists():
            self.db_path.mkdir()

        init_args = [
            self.pg_ctl, "initdb", "--pgdata", self.db_path
        ]
        result = self._run(init_args)
        output = result.stdout.strip()
        return output

    def create_db(self, db_name: str) -> bool:
        """
        Creates a new database within the Postgres instance.
        """
        create_db_args = [
            self.createdb, "-h", self.db_path, db_name,
        ]
        result = self._run(create_db_args)
        output = result.stdout.strip()

        # An empty response means the database was created successfully.
        return output == ""

    def start(self) -> bool:
        """
        Starts the Postgres database server.

        It is up to the caller to make sure init() is called first.
        Note that the only way to connect to this server is through
        a unix socket.
        """
        start_args = [
            self.pg_ctl,
            "--pgdata",
            str(self.db_path),
            "--wait",
            '--options',
            f'-h "" -k "{self.db_path}"',
            "start",
        ]

        result = self._run(start_args)
        if result.returncode != 0:
            print("An error occured!", file=sys.stderr)
            output = result.stdout.strip()
            print(output, file=sys.stderr)

        status = self.get_status()
        return status == DatabaseStatus.RUNNING

    def stop(self) -> bool:
        """
        Stops the Postgres database server.
        """
        stop_args = [
            self.pg_ctl, "-D", self.db_path, "-m", "immediate", "stop"
        ]
        result = self._run(stop_args)

        if result.returncode != 0:
            print("An error occured!", file=sys.stderr)
            output = result.stdout.strip()
            print(output, file=sys.stderr)

        status = self.get_status()
        return status == DatabaseStatus.STOPPED

    def delete(self) -> None:
        """
        Deletes the Postgres database server.

        It is up to the caller to make sure stop() is called first.
        """
        shutil.rmtree(self.db_path)

    def get_status(self) -> DatabaseStatus:
        """
        Returns the status of a Postgres database given a database path.
        """
        if not self.db_path.exists():
            return DatabaseStatus.DOES_NOT_EXIST

        if not self.db_path.is_dir():
            return DatabaseStatus.INVALID_DIRECTORY

        if not any(self.db_path.iterdir()):
            return DatabaseStatus.DIRECTORY_EMPTY

        status_args = [self.pg_ctl, "status", "-D", str(self.db_path)]
        result = self._run(status_args)
        output = result.stdout.strip()

        if "pg_ctl: server is running" in output:
            return DatabaseStatus.RUNNING

        if "pg_ctl: no server running" in output:
            return DatabaseStatus.STOPPED

        print(output, file=sys.stderr)
        return DatabaseStatus.UNKNOWN
