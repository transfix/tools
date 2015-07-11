"""This program is a tool for archiving old mail in mbox mailboxes. I neglected
my mailbox on sdf.org for years and wrote this to clean it up so pine wouldn't
barf all over my huge inbox because it's high time I start using sdf regularly
again! As a cronjob, this could be useful to regularly move old mail to another
mbox.
07/11/2015 - transfix@gmail.com

Change Log
----------
07/11/2015 - start

TODO
----
- Cleanup with flake8
"""

import argparse
import datetime
import email.utils
import mailbox
import time


def process_args():
  parser = argparse.ArgumentParser(description="""Move old mbox mail from one archive to another
                                                  older than a specified number of days.""")
  parser.add_argument('command', help='One of "list," "copy," or "move."')
  parser.add_argument('source_mbox', help='mbox file to list, copy or move messages from')
  parser.add_argument('target_mbox', nargs='?',
                      help='mbox file where old messages are copied or moved to')
  parser.add_argument('older_than', nargs='?', default=0, type=int,
                      help="Operate on mail older than this number of days. Default is 0")
  args = vars(parser.parse_args())
  return args

def main():
  args = process_args()
  source_mbox = args['source_mbox']
  target_mbox = None
  if 'target_mbox' in args.keys():
    target_mbox = args['target_mbox']
  older_than = args['older_than']
  cmd = args['command']
  now = datetime.datetime.now()

  source_mb = mailbox.mbox(source_mbox)

  copy_or_move = cmd == "copy" or cmd == "move";
  load_target_mb = target_mbox != None and copy_or_move
  if copy_or_move and target_mbox == None:
    raise RuntimeError('Must specify target for copy or move.')

  target_mb = None
  if load_target_mb:
    target_mb = mailbox.mbox(target_mbox)
    target_mb.lock()

  source_mb.lock()
  for message_key in source_mb.keys():
    message = source_mb.get_message(message_key)
    t = email.utils.parsedate(message['date'])
    if t == None:
      print ('-'*80)
      print "malformed email: ", message
      continue
    date = datetime.datetime.fromtimestamp(time.mktime(t))
    td = now - date
    if td >= datetime.timedelta(days=older_than):
      from_addr = message['from']
      subject = message['subject']
      date = message['date']

      if cmd == "list":
        print ('-'*80)
        print "From: {0}\nSubject: {1}\nDate: {2}".format(from_addr,
                                                          subject, date)
      else:
        if load_target_mb:
          target_mb.add(message)
        if cmd == "move":
          source_mb.remove(message_key)

  source_mb.flush()
  source_mb.unlock()
  if target_mb != None:
    target_mb.flush()
    target_mb.unlock()


if __name__ == '__main__':
  main()

