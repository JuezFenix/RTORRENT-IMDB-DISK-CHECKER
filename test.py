# -*- coding: utf-8 -*-

from datetime import datetime

start = datetime.now()

import sys, os, smtplib, config as cfg
from remotecaller import xmlrpc

try:
        from torrents import completed
        from mountpoints import mount_points
except:
        print('Building cache. Please wait.')
        import cacher

        try:
                cacher.build_cache('test')
        except:
                print('Failed\nRun the script with its full path like:\npython /path/to/test.py 69')
                sys.exit()

        print('Cache built. Please run the code again.')
        sys.exit()

def send_email():
        server = False

        try:
                try:
                        try:
                                print('\nAttempting to email using TLS\n')
                                server = smtplib.SMTP(cfg.smtp_server, cfg.port, timeout=10)
                                server.starttls()
                                server.login(cfg.account, cfg.password)
                        except Exception as e:
                                print('Failed\n\nTLS Related Error:\n')
                                print(e)
                                print('\nAttempting to email using SSL\n')

                                if server:
                                        server.quit()

                                server = smtplib.SMTP_SSL(cfg.smtp_server, cfg.port, timeout=10)
                                server.login(cfg.account, cfg.password)
                except Exception as e:
                        print('Failed\n\nSSL Related Error:\n')
                        print(e)
                        print('\nAttempting to email without TLS/SSL\n')

                        if server:
                                server.quit()

                        server = smtplib.SMTP(cfg.smtp_server, cfg.port, timeout=10)
                        server.login(cfg.account, cfg.password)

                message = 'Subject: {}\n\n{}'.format(cfg.subject, cfg.body)
                server.sendmail(cfg.account, cfg.receiver, message)
                server.quit()
                print('Succeeded')
        except Exception as e:
                print('Failed\n\nNon TLS/SSL Related Error:\n')
                print(e)

if sys.argv[1] == 'email':
        send_email()
        sys.exit()

try:
        torrent_size = float(sys.argv[1])
        script_path = os.path.dirname(sys.argv[0])
        queue = script_path + '/queue.txt'
        remover = script_path + '/remover.py'
        remover_queue = script_path + '/' + 'hash'
        emailer = script_path + '/emailer.py'
        last_torrent = script_path + '/hash.txt'
        downloading = xmlrpc('d.multicall2', ('', 'leeching', 'd.left_bytes='))
        downloading = 0
        disk = os.statvfs('/')
        available_space = (disk.f_bsize * disk.f_bavail - downloading) / 1073741824.0
        required_space = torrent_size - (available_space - cfg.minimum_space)
        requirements = cfg.minimum_size, cfg.minimum_age, cfg.minimum_ratio, cfg.fallback_age, cfg.fallback_ratio
        current_date = datetime.now()
        include = override = True
        exclude = no = False
        freed_space = count = 0
        fallback_torrents, deleted = [], []

        while freed_space < required_space:

                if not completed and not fallback_torrents:
                        break

                if completed:
                        t_age, t_label, t_tracker, t_ratio, t_size_b, t_name, t_hash, t_path, parent_directory = completed[0]

                        if override:
                                override = False
                                min_size, min_age, min_ratio, fb_age, fb_ratio = requirements

                        if cfg.exclude_unlabelled and not t_label:
                                del completed[0]
                                continue

                        if cfg.labels:

                                if t_label in cfg.labels:
                                        label_rule = cfg.labels[t_label]
                                        rule = label_rule[0]

                                        if rule is exclude:
                                                del completed[0]
                                                continue

                                        if rule is not include:
                                                override = True
                                                min_size, min_age, min_ratio, fb_age, fb_ratio = label_rule

                                elif cfg.labels_only:
                                        del completed[0]
                                        continue

                        if cfg.trackers and not override:
                                tracker_rule = [tracker for tracker in cfg.trackers for url in t_tracker if tracker in url[0]]

                                if tracker_rule:
                                        tracker_rule = cfg.trackers[tracker_rule[0]]
                                        rule = tracker_rule[0]

                                        if rule is exclude:
                                                del completed[0]
                                                continue

                                        if rule is not include:
                                                override = True
                                                min_size, min_age, min_ratio, fb_age, fb_ratio = tracker_rule

                                elif cfg.trackers_only:
                                        del completed[0]
                                        continue

                        t_age = (current_date - datetime.utcfromtimestamp(t_age)).days
                        t_ratio /= 1000.0
                        t_size_g = t_size_b / 1073741824.0

                        if t_age < min_age or t_ratio < min_ratio or t_size_g < min_size:

                                if fb_age is not no and t_age >= fb_age and t_size_g >= min_size:
                                        fallback_torrents.append([parent_directory, t_age, t_label, t_tracker, t_size_g, t_name])

                                elif fb_ratio is not no and t_ratio >= fb_ratio and t_size_g >= min_size:
                                        fallback_torrents.append([parent_directory, t_age, t_label, t_tracker, t_size_g, t_name])

                                del completed[0]
                                continue

                        del completed[0]
                else:
                        parent_directory, t_age, t_label, t_tracker, t_size_g, t_name = fallback_torrents[0]
                        del fallback_torrents[0]

                count += 1
                freed_space += t_size_g
                deleted.append('%s. TA: %s Days Old\n%s. TN: %s\n%s. TL: %s\n%s. TT: %s\n' % (count, t_age, count, t_name, count, t_label, count, t_tracker))
except Exception as e:
        print(e)

time = datetime.now() - start

try:
        xmlrpc('d.multicall2', ('', 'leeching', 'd.down.total='))
except:
        print('SCGI address not configured properly. Please adjust it in your config.py file before continuing.')
        sys.exit()

calc = available_space + freed_space - torrent_size

with open('testresult.txt', 'w+') as textfile:
        textfile.write('Script Executed in %s Seconds\n%s Torrent(s) Deleted Totaling %.2f GB\n' % (time, count, freed_space))
        textfile.write('%.2f GB Free Space Before Torrent Download\n%.2f GB Free Space After %.2f GB Torrent Download\n\n' % (available_space, calc, torrent_size))
        textfile.write('TA = Torrent Age  TN = Torrent Name  TL = Torrent Label  TT = Torrent Tracker\n\n')

        for result in deleted:

                if sys.version_info[0] == 3:
                        textfile.write(result + '\n')
                else:
                        textfile.write(result.encode('utf-8') + '\n')

print('\nTA = Torrent Age  TN = Torrent Name  TL = Torrent Label  TT = Torrent Tracker\n')

for result in deleted:
        print(result)

print('TA = Torrent Age  TN = Torrent Name  TL = Torrent Label  TT = Torrent Tracker\n')
print('Script Executed in %s Seconds\n%s Torrent(s) Deleted Totaling %.2f GB' % (time, count, freed_space))
print('%.2f GB Free Space Before Torrent Download\n%.2f GB Free Space After %.2f GB Torrent Download\n' % (available_space, calc, torrent_size))
