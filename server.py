import socket
import string
import sys
import os
import random
import utils


def random_string_generator():
    # generate the numbers and digits
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(64)))
    str1 += ''.join(random.choice(string.digits) for x in range(64))
    # convert string to list
    str_list = list(str1)
    # shuffle the chars
    random.shuffle(str_list)
    return ''.join(str_list)


# checking  validation of args
if len(sys.argv) != 2:
    sys.exit()
PORT_SERVER = int(sys.argv[1])
# connecting to the client
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', PORT_SERVER))
server.listen(5)
# D1: key - identify string, value - int id
D1 = {}
# D2: key - id, value - D3
D2 = {}
# to identify users
id_user = 0
# to identify clients
id_client = 0
while True:
    # accept client
    client_socket, client_address = server.accept()
    # data represents the operation we need to do
    data = client_socket.recv(1)
    # data = 1 means new client
    if data.decode('utf-8') == "1":
        id_user += 1
        id_client += 1
        # generate string id
        stringid = random_string_generator()
        # key - string : value - num id
        D1[stringid] = id_user
        # key - socket : list of files that exchanged
        D2[id_user] = {id_client: []}
        print(stringid)
        # sending the stringid to the client
        client_socket.send(stringid.encode('utf-8'))
        # create root dir
        currentdir = os.path.join(os.getcwd(), str(id_user))
        os.makedirs(currentdir, 0o777, True)
        utils.syncReciver(currentdir, client_socket, True, id_user, 0)
        client_socket.send(utils.bytes4(id_client).encode('utf-8'))

        # data = 2 means existing client
    if data.decode('utf-8') == "2":
        id_client += 1
        strID = client_socket.recv(128).decode('utf-8')
        current_user_id = D1[strID]
        D2[current_user_id][id_client] = []  # insert new client to D2
        server_len_path = utils.bytes4(len(os.path.join(os.getcwd(), str(id_user))))
        client_socket.send(server_len_path.encode('utf-8'))
        path = os.path.join(os.getcwd(), str(D1[strID]))
        utils.syncSender(path, client_socket, 0)
        client_socket.send('3'.encode('utf-8'))
        client_socket.send(utils.bytes4(id_client).encode('utf-8'))

    # sync with running client
    if data.decode('utf-8') == "3":
        strID = client_socket.recv(128).decode('utf-8')
        cur_id_user = D1[strID]
        cur_id_client = int(client_socket.recv(4).decode('utf-8'))
        is_changed = int(client_socket.recv(1).decode('utf-8'))
        if is_changed != 0:
            utils.sync_changes_list(cur_id_user, cur_id_client, D2, client_socket, True, 0)
        list_change = D2[cur_id_user][cur_id_client]
        utils.server_send_changes_list(client_socket, list_change, cur_id_user)
        D2[cur_id_user][cur_id_client] = []
    client_socket.close()