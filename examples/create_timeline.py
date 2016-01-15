from cbapi2 import CbApi2, CbFileModEvent, CbNetConnEvent, CbRegModEvent, CbChildProcEvent, CbModLoadEvent
from progressbar import ProgressBar, ETA, Percentage, Bar
import argparse
import csv
import datetime
import sys


def event_summary(event):
    if type(event) == CbFileModEvent:
        return [event.parent.path, event.timestamp, event.type, event.path, '', event.parent.url]
    elif type(event) == CbNetConnEvent:
        if event.dns:
            hostname = event.dns
        else:
            hostname = event.ipaddr
        hostname += ':%d' % event.port

        return [event.parent.path, event.timestamp, event.direction + ' netconn', hostname, '', event.parent.url]
    elif type(event) == CbRegModEvent:
        return [event.parent.path, event.timestamp, event.type, event.path, '', event.parent.url]
    elif type(event) == CbChildProcEvent:
        return [event.parent.path, event.timestamp, 'childproc', event.path, event.proc.cmdline, event.parent.url]
    elif type(event) == CbModLoadEvent:
        return [event.parent.path, event.timestamp, 'modload', event.path, event.md5, event.parent.url]
    else:
        return None


def dump_events(cb, start_time, end_time, hostname, fp):
    eventwriter = csv.writer(fp)

    eventwriter.writerow(['ProcessPath', 'Timestamp', 'Event', 'Path/IP/Domain', 'Comments', 'URL'])

    widgets = [Bar(), Percentage(), ' ', ETA()]
    progress = ProgressBar(widgets=widgets)

    proc_query = 'hostname:%s last_update:[%s TO *]' % \
                                      (hostname, (start_time - datetime.timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%S'))

    print "Generating timeline for host %s from %s to %s" % (hostname,
                                                             start_time.strftime('%Y-%m-%d %H:%M:%S'),
                                                             end_time.strftime('%Y-%m-%d %H:%M:%S'))

    num_docs = len(cb.process_search(proc_query))
    print "Please wait. Processing %d docs..." % num_docs

    for proc in progress(cb.process_search(proc_query)):
        for evt in proc.all_events:
            if start_time <= evt.timestamp <= end_time:
                eventwriter.writerow(event_summary(evt))


def main():
    parser = argparse.ArgumentParser(description="Dump full event timeline for a sensor")
    parser.add_argument('-o', '--output', action='store', help='Destination CSV file for the events')

    parser.add_argument('--start', action='store', dest='starttime', help='Start time in "YYYY-MM-DD HH:MM:SS" format',
                        default=[None], nargs='*')
    parser.add_argument('--duration', action='store', type=int, help='Number of minutes to capture', default=5,
                        nargs=1)
    parser.add_argument('--hostname', action='store', help='Sensor hostname', nargs=1)

    parser.add_argument(action='store', nargs=1, dest='url', help='Cb server base URL', default='')
    parser.add_argument(action='store', nargs=1, dest='apikey', help='Cb server API key', default='')

    results = parser.parse_args()
    cb = CbApi2(results.url[0], results.apikey[0], ssl_verify=False)

    start_time = datetime.datetime.strptime(' '.join(results.starttime), '%Y-%m-%d %H:%M:%S')
    end_time = start_time + datetime.timedelta(minutes=results.duration[0])

    with open(results.output, 'w') as fp:
        dump_events(cb, start_time, end_time, results.hostname[0], fp)

    return 0


if __name__ == '__main__':
    sys.exit(main())
