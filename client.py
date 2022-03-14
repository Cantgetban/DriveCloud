import socket
import sys
import utils
import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

if len(sys.argv) != 6 and len(sys.argv) != 5:
    sys.exit()
IP_SERVER = sys.argv[1]
PORT_SERVER = int(sys.argv[2])
PATH = sys.argv[3]
TIME_FOR_UPDATE = int(sys.argv[4])

# ID_FLAG = False, no id, upload user folder to the server
ID_FLAG = False
STRING_ID = ""
if len(sys.argv) == 6:
    STRING_ID = sys.argv[5]

    # ID_FLAG = True- id entered, download user folder
    ID_FLAG = True

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP_SERVER, PORT_SERVER))
if not ID_FLAG:
    # 1 - new user->new client
    avoid = len(PATH.encode('utf-8'))
    s.send('1'.encode('utf-8'))
    STRING_ID = s.recv(128).decode('utf-8')
    utils.syncSender(PATH, s, avoid)
    s.send('3'.encode('utf-8'))
else:
    # 2 - exist user->new client
    ID = sys.argv[5]
    s.send('2'.encode('utf-8'))
    s.send(ID.encode('utf-8'))
    server_path_len = int((s.recv(4)).decode('utf-8'))
    utils.syncReciver(PATH, s, False, 0, server_path_len)

my_id = s.recv(4).decode('utf-8')

avoid = len(PATH.encode('utf-8'))
utils.set_ignore(avoid)
utils.set_socket(s)
# init the event handler
my_event_handler = PatternMatchingEventHandler(["*"], None, False, True)
my_event_handler.on_created = utils.created
my_event_handler.on_deleted = utils.deleted
my_event_handler.on_modified = utils.modified
my_event_handler.on_moved = utils.moved
# init the observer
my_observer = Observer()
my_observer.schedule(my_event_handler, PATH, True)
my_observer.start()
s.close()
while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP_SERVER, PORT_SERVER))
    utils.set_socket(s)
    s.send('3'.encode('utf-8'))

    s.send(STRING_ID.encode('utf-8'))
    s.send(my_id.encode('utf-8'))
    if utils.flag:
        # some changes happened
        s.send('1'.encode('utf-8'))
        utils.send_changes_list(PATH, s, avoid)

    else:
        s.send('0'.encode('utf-8'))
    utils.client_sync_changes_list(s, PATH, my_id)
    utils.set_change_list()
    s.close()
    utils.set_flag()
    time.sleep(TIME_FOR_UPDATE)