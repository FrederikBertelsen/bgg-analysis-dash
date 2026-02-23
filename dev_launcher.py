import subprocess
import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.changed = False

    def on_any_event(self, event):
        # Normalize to str (some event implementations may provide bytes)
        path = str(event.src_path)
        if os.path.splitext(path)[1] == '.py':
            self.changed = True


def wait_for_change(path='.'):
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, path, recursive=True)
    observer.start()
    try:
        while not handler.changed:
            time.sleep(0.5)
    finally:
        observer.stop()
        observer.join()


def run_loop(cmd=None):
    if cmd is None:
        cmd = [sys.executable or 'python3', 'app.py']
    while True:
        p = subprocess.Popen(cmd)
        exitcode = p.wait()
        if exitcode == 0:
            # clean exit
            print('Process exited normally.')
            break
        print(f'Process exited with code {exitcode}. Waiting for .py file changes before restarting...')
        wait_for_change('.')
        print('Detected file change; restarting.')


if __name__ == '__main__':
    # Use python3 explicitly; change if needed.
    run_loop()
