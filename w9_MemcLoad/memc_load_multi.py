#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pip install protobuf==3.20 !!!
# pip install python-memcached

import os
import gzip
import sys
import glob
import logging
import collections
from optparse import OptionParser
import appsinstalled_pb2
import memcache
from threading import Thread
from queue import Queue, Empty
import multiprocessing
from functools import partial
import time

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])
config = {
    'MEMC_MAX_RETRIES': 1,
    'MEMC_TIMEOUT': 3,
    'MAX_JOB_QUEUE_SIZE': 0,
    'MAX_RESULT_QUEUE_SIZE': 0,
    'MAX_DATA_SIZE': 3,
    'THREADS_PER_WORKER': 4,
    'MEMC_BACKOFF_FACTOR': 0.3
}


def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def insert_appsinstalled(pools, appsinstalled, dry_run=False):
    for memc_addr in appsinstalled:
        data = {}
        ua = appsinstalled_pb2.UserApps()

        memc_pool = pools[memc_addr]
        for appsinst in appsinstalled[memc_addr]:
            if appsinst:
                key = f"%s:%s" % (appsinst.dev_type, appsinst.dev_id)
                ua.lat = appsinst.lat
                ua.lon = appsinst.lon
                ua.apps.extend(appsinst.apps)
                packed = ua.SerializeToString()
                data.update({key: packed})

        # return None
        # ua.lat = appsinstalled.lat
        # ua.lon = appsinstalled.lon
        # ua.apps.extend(appsinstalled.apps)
        # key = f"%s:%s" % (appsinstalled[memc_addr].dev_type, appsinstalled[memc_addr].dev_id)
        # packed = ua.SerializeToString()
        try:
            if dry_run:
                logging.debug("%s -> data length: %s (key: %s)" % (memc_addr, len(data), data))
            else:
                try:
                    memc = memc_pool.get(timeout=0.1)
                except Empty:
                    memc = memcache.Client([memc_addr], socket_timeout=config['MEMC_TIMEOUT'])
                ok = False
                for n in range(config['MEMC_MAX_RETRIES']):
                    ok = memc.set_multi(data)
                    if ok:
                        break
                    backoff_value = config['MEMC_BACKOFF_FACTOR'] * (2 ** n)
                    time.sleep(backoff_value)
                memc_pool.put(memc)
                return ok
        except Exception as e:
            logging.exception("Cannot write to memc %s: %s" % (memc_addr, e))
            return False
        return True


def parse_appsinstalled(line):
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isidigit()]
        logging.info("Not all user apps are digits: `%s`" % line)
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)
    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def handle_task(job_queue, result_queue):
    processed = errors = 0
    while True:
        try:
            task = job_queue.get(timeout=0.1)
        except Empty:
            result_queue.put((processed, errors))
            return

        # job_queue.put((pools[memc_addr], memc_addr, appsinstalled, options.dry))
        pools, appsinstalled, dry_run = task
        ok = insert_appsinstalled(pools, appsinstalled, dry_run)
        if ok:
            processed += 1
        else:
            errors += 1


def parsing_file(filename: str, options):
    memc_addr = None
    appsinstalled = None
    apps_inner = []
    errors = 0
    index = 0
    inner_count = 0

    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }

    for line in parse_next_line(filename=filename):
        apps = parse_appsinstalled(line)
        if not apps:
            errors += 1
            logging.error(f"line {line[0:10]} cannot be processed")
            continue

        memc_addr = device_memc.get(apps.dev_type)
        if not memc_addr:
            errors += 1
            logging.error(f"Unknown device type: {apps.dev_type}")
            continue

        # index: memc_addr: [appsinstalled, ] <= MAX_DATA_SIZE
        apps_inner.append(apps)
        inner_count += 1
        if inner_count > config['MAX_DATA_SIZE']:
            appsinstalled = add_appsinstalled_struct(memc_addr, apps_inner)
            inner_count = 0
            apps_inner = []
            index += 1
            yield appsinstalled, errors

    if apps_inner:
        appsinstalled = add_appsinstalled_struct(memc_addr, apps_inner)

    yield appsinstalled, errors


def parse_next_line(filename: str):
    with gzip.open(filename) as fd:
        for line in fd:
            line = line.strip().decode("UTF-8")
            if line.find('tsv') != -1 or not line:
                continue
            yield line


def add_appsinstalled_struct(memc_addr, appsinstalled):
    return {memc_addr: appsinstalled}


def handle_logfile(fn, options):
    pools = collections.defaultdict(Queue)
    job_queue = Queue(maxsize=config['MAX_JOB_QUEUE_SIZE'])
    result_queue = Queue(maxsize=config['MAX_RESULT_QUEUE_SIZE'])

    workers = []
    for i in range(config['THREADS_PER_WORKER']):
        thread = Thread(target=handle_task, args=(job_queue, result_queue))
        thread.daemon = True
        workers.append(thread)

    for thread in workers:
        thread.start()

    processed = errors = 0
    logging.info(f'Processing {fn}')

    for (appsinstalled_struct, error) in parsing_file(filename=fn, options=options):
        errors += error

        job_queue.put((pools, appsinstalled_struct, options.dry))

        if not all(thread.is_alive() for thread in workers):
            break

    for thread in workers:
        if thread.is_alive():
            thread.join()

    while not Empty:
        processed_per_worker, errors_per_worker = result_queue.get()
        processed += processed_per_worker
        errors += errors_per_worker

    if processed:
        err_rate = float(errors) / processed
        if err_rate < NORMAL_ERR_RATE:
            logging.info("Acceptable error rate (%s). Successfull load" % err_rate)
        else:
            logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))

    return fn


def main(options):
    num_processes = multiprocessing.cpu_count() - 1
    with multiprocessing.Pool(processes=num_processes) as pool:
        fnames = sorted(fn for fn in glob.iglob(options.pattern))
        handler = partial(handle_logfile, options=options)
        for fn in pool.imap(handler, fnames):
            # dot_rename(fn)
            pass


def prototest():
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="data/appsinstalled/*.tsv.gz")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).5s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    if opts.test:
        prototest()
        sys.exit(0)

    logging.info(f"Memc loader started with options: {opts}")
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Process terminated")
