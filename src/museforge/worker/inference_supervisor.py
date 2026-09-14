"""Linux inference guardian: EOF means its owning pool child has disappeared.

The guardian owns the GPU lock until the inference process group is terminated
and reaped. It deliberately survives the Celery pool child and never imports
inference libraries.
"""
import argparse
import ctypes
import errno
import fcntl
import os
from pathlib import Path
import select
import signal
import subprocess
import time


def descendants(pid):
    """Include children launched by any thread and descendants in new sessions."""
    found = set()
    pending = [pid]
    while pending:
        parent = pending.pop()
        for children_file in Path(f'/proc/{parent}/task').glob('*/children'):
            try:
                children = [int(value) for value in children_file.read_text().split()]
            except (FileNotFoundError, ProcessLookupError):
                continue
            for child in children:
                if child not in found:
                    found.add(child)
                    pending.append(child)
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control-fd', type=int, required=True)
    parser.add_argument('--lock-path', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    stopping = [False]
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopping.__setitem__(0, True))
    # Adopt orphan descendants so cleanup also reaps subprocesses of inference.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), 'cannot enable inference subreaper')

    def owner_closed():
        if stopping[0]:
            return True
        readable, _, _ = select.select([args.control_fd], [], [], .1)
        return bool(readable) and not os.read(args.control_fd, 1)

    process = None
    with open(args.lock_path, 'a') as lock:
        while True:
            if owner_closed():
                return 125
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
        try:
            # Do not pass the control FD or lock FD to inference.
            process = subprocess.Popen(command, start_new_session=True, close_fds=True)
            while process.poll() is None:
                if owner_closed():
                    return 125
            return process.returncode
        finally:
            if process is not None:
                def signal_tree(sig):
                    children = descendants(os.getpid())
                    try:
                        os.killpg(process.pid, sig)
                    except ProcessLookupError:
                        pass
                    for pid in children:
                        try:
                            os.kill(pid, sig)
                        except ProcessLookupError:
                            pass
                signal_tree(signal.SIGTERM)
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    process.poll()
                    # Reap adopted descendants as they finish.
                    try:
                        while os.waitpid(-1, os.WNOHANG)[0]:
                            pass
                    except ChildProcessError:
                        pass
                    if not descendants(os.getpid()):
                        break
                    time.sleep(.05)
                signal_tree(signal.SIGKILL)
                process.wait()
                # After SIGKILL, keep the lock until every adopted child is reaped.
                try:
                    while True:
                        os.waitpid(-1, 0)
                except ChildProcessError:
                    pass
            os.close(args.control_fd)


if __name__ == '__main__':
    raise SystemExit(main())
