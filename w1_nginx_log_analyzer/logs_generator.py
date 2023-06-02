# log name may be as nginx-access-ui.log-%Ym%%d or in gzip format nginx-access-ui.log-%Y%m%d.gz
# also in log_dir must be located log files from different services with different name

import random
import time
from shutil import copy2

LOG_DIR = "./data"


def create_rnd_dt() -> str:
    random.seed()
    year = random.randint(2023, 2023)
    mon = random.randint(3, 5)
    day = random.randint(1, 24)
    return f"{year}{mon if mon > 9 else '0' + str(mon)}{day if day > 9 else '0' + str(day)}"


def create_rnd_ext() -> str | None:
    random.seed()
    ext = [".gz", ".tar", ".bz2", None]
    idx = random.randint(0, len(ext)-1)
    return ext[idx]


def create_file_mask() -> str:
    mask = ["access", "nginx-access-ui", "uzik-access-ui"]
    random.seed()
    idx = random.randint(0, 2)
    return mask[idx]


def generate_file():
    dt = create_rnd_dt()
    ext = create_rnd_ext()
    file_mask = create_file_mask()

    print(f"file={file_mask}.log-{dt}{ext if ext is not None else ''}")
    copy2(src=f"{LOG_DIR}/{file_mask}.log{ext if ext is not None else ''}",
          dst=f"{LOG_DIR}/{file_mask}.log-{dt}{ext if ext is not None else ''}"
          )


if __name__ == '__main__':
    try:
        for i in range(10):
            generate_file()
            time.sleep(1)
    except KeyboardInterrupt:
        print('process terminated')
