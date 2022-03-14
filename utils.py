import os
import socket

ignore = 0
c_socket = socket.socket()
changes_list = [[], [], [], []]
flag = False
mod = False


def set_change_list():
    global changes_list
    changes_list = [[], [], [], []]


def set_ignore(num):
    global ignore
    ignore = num


def set_flag():
    global flag
    flag = False


def set_socket(s):
    global c_socket
    c_socket = s


def syncSender(path, s, avoid):
    for root, dirs, files in os.walk(path):
        for file in files:
            s.send('2'.encode('utf-8'))
            counter = 0
            fpath = os.path.join(root, file)
            fpath_receiver = fpath[avoid + 1:]
            lengthpath = bytes4(len(fpath_receiver.encode('utf-8')))
            s.send(lengthpath.encode('utf-8'))
            s.send(fpath_receiver.encode('utf-8'))

            filesize = bytes10(os.path.getsize(fpath))
            s.send(filesize.encode('utf-8'))
            f = open(fpath, "rb")
            while counter <= int(filesize):
                data1 = f.read(1024)
                if not (data1):
                    break
                s.send(data1)
                counter += len(data1)
            f.close()
        for dir in dirs:
            s.send('1'.encode('utf-8'))
            length1 = len((os.path.join(root, dir)).encode('utf-8')) - (avoid + 1)
            s.send(bytes4(length1).encode('utf-8'))
            fpath = os.path.join(root, dir)
            fpath = fpath[avoid + 1:]
            s.send(fpath.encode('utf-8'))
            syncSender(os.path.join(root, dir), s, avoid)


def syncReciver(p, s, flag, id, serv_len_path):
    data = s.recv(1)
    # open current dir if not exist
    if not os.path.exists(p):
        os.makedirs(p, 0o777, True)
    # data = 3 means we finished to sync
    while data.decode('utf-8') != "3":
        # data = 1 create dir
        if data.decode('utf-8') == "1":
            length = (s.recv(4)).decode('utf-8')
            path = (s.recv(int(length))).decode('utf-8')
            if flag:
                path = os.path.join(str(id), path)
                currentdir = os.path.join(os.getcwd(), path)
            if not flag:
                # +1 for linux
                currentdir = os.path.join(p, path[serv_len_path:])
            os.makedirs(currentdir, 0o777, True)
        # data = 2 create file
        if data.decode('utf-8') == "2":
            lenpath = (s.recv(4)).decode('utf-8')
            path = s.recv(int(lenpath)).decode('utf-8')
            if flag:
                path = os.path.join(str(id), path)
            if not flag:
                # +1 for linux
                path = os.path.join(p, path[serv_len_path:])
            file = open(path, 'wb')
            filesize = s.recv(10).decode('utf-8')
            buffer = bytearray()
            while len(buffer) < int(filesize):
                d = (s.recv(int(filesize) - len(buffer)))
                buffer.extend(d)
            file.write(buffer)
            file.close()
        data = s.recv(1)


def bytes4(num):
    if num < 10:
        return "000" + str(num)
    if num < 100:
        return "00" + str(num)
    if num < 1000:
        return "0" + str(num)
    if num < 10000:
        return str(num)


def bytes10(num):
    if num < 10:
        return "000000000" + str(num)
    if num < 100:
        return "00000000" + str(num)
    if num < 1000:
        return "0000000" + str(num)
    if num < 10000:
        return "000000" + str(num)
    if num < 100000:
        return "00000" + str(num)
    if num < 1000000:
        return "0000" + str(num)
    if num < 10000000:
        return "000" + str(num)
    if num < 100000000:
        return "00" + str(num)
    if num < 100000000:
        return "0" + str(num)
    return str(num)


def created(event):
    global changes_list
    global flag
    flag = True

    # ignoring file system events
    if not os.path.basename(event.src_path).startswith(".goutputstream-"):
        if os.path.isdir(event.src_path):
            changes_list[0].append(["1", event.src_path])
        else:
            changes_list[0].append(["2", event.src_path])


def deleted(event):
    global changes_list
    global flag
    flag = True
    changes_list[2].append([event.src_path])

def modified(event):
    global mod
    mod = True

def moved(event):
    global flag
    flag = True

    # if existing file changed-> delete old and create new
    if os.path.basename(event.src_path).startswith(".goutputstream-"):
        if os.path.exists(event.dest_path):
            # delete
            changes_list[2].append([event.dest_path])
            # create
            changes_list[0].append(["2", event.dest_path])

    # change name or move
    else:
        changes_list[1].append([event.src_path, event.dest_path])


def delete_dir(target):
    for d in os.listdir(target):
        try:
            delete_dir(os.path.join(target, d))
        except OSError:
            os.remove(os.path.join(target, d))
    os.rmdir(target)


def sync_changes_list(user_id, client_id, dic2, s, is_server, serv_len_path):
    currentdir = os.path.join(os.getcwd(), str(user_id))
    data = s.recv(1)
    new_change = []
    # data = 0 means we finished to sync
    while data.decode('utf-8') != "0":
        # data = 1 create dir
        if data.decode('utf-8') == "1":
            length = (s.recv(4)).decode('utf-8')
            path = (s.recv(int(length))).decode('utf-8')
            new_change = ["1", path]
            if is_server:
                path = os.path.join(str(user_id), path)
                currentdir = os.path.join(os.getcwd(), path)
            if not is_server:
                # +1 for linux
                currentdir = os.path.join(currentdir, path[serv_len_path + 1:])
            os.makedirs(currentdir, 0o777, True)

        # data = 2 create file
        if data.decode('utf-8') == "2":
            lenpath = (s.recv(4)).decode('utf-8')
            path = s.recv(int(lenpath)).decode('utf-8')
            new_change = ["2", path]
            if is_server:
                path = os.path.join(str(user_id), path)
            if not is_server:
                # +1 for linux
                path = os.path.join(currentdir, path[serv_len_path + 1:])
            file = open(path, 'wb')
            filesize = s.recv(10).decode('utf-8')
            buffer = bytearray()
            while len(buffer) < int(filesize):
                d = (s.recv(int(filesize) - len(buffer)))
                buffer.extend(d)
            file.write(buffer)
            file.close()

        # data = 3 delete dir or file
        if data.decode('utf-8') == "3":
            length = (s.recv(4)).decode('utf-8')
            path = (s.recv(int(length))).decode('utf-8')
            new_change = ["3", path]
            if is_server:
                path = os.path.join(str(user_id), path)
                currentdir = os.path.join(os.getcwd(), path)
            if not is_server:
                # +1 for linux
                currentdir = os.path.join(currentdir, path[serv_len_path + 1:])
            if os.path.exists(currentdir):
                if os.path.isdir(currentdir):
                    delete_dir(currentdir)
                elif os.path.isfile(currentdir):
                    os.remove(currentdir)

        # data = 4 rename file or dir
        if data.decode('utf-8') == "4":
            src_length = (s.recv(4)).decode('utf-8')
            src_path = (s.recv(int(src_length))).decode('utf-8')
            dest_length = (s.recv(4)).decode('utf-8')
            dest_path = (s.recv(int(dest_length))).decode('utf-8')
            new_change = ["4", src_path, dest_path]
            src_path = os.path.join(str(user_id), src_path)
            src_path = os.path.join(os.getcwd(), src_path)
            dest_path = os.path.join(str(user_id), dest_path)
            dest_path = os.path.join(os.getcwd(), dest_path)
            if os.path.exists(src_path):
                os.rename(src_path, dest_path)
        data = s.recv(1)
        for key in dic2[user_id].keys():
            if key != client_id:
                dic2[user_id][key].append(new_change)


def send_changes_list(path, s, avoid):
    global changes_list
    avoid = avoid + 1
    # changes_list[2] - list of deleted lists info - important! this is must be the first loop
    for change in changes_list[2]:
        s.send('3'.encode('utf-8'))
        delt_path = change[0]
        length1 = len(delt_path.encode('utf-8')) - avoid
        s.send(bytes4(length1).encode('utf-8'))
        delt_path = delt_path[avoid:]
        s.send(delt_path.encode('utf-8'))

    # changes_list[0] - list of created lists info
    for change in changes_list[0]:
        # create dir
        if change[0] == "1":
            s.send('1'.encode('utf-8'))
            dir_path = change[1]
            length1 = len(dir_path.encode('utf-8')) - avoid
            s.send(bytes4(length1).encode('utf-8'))
            dir_path = dir_path[avoid:]
            s.send(dir_path.encode('utf-8'))
        # create file
        if change[0] == "2":
            s.send('2'.encode('utf-8'))
            counter = 0
            fpath = change[1]
            fpath_receiver = fpath[avoid:]
            lengthpath = bytes4(len(fpath_receiver.encode('utf-8')))
            s.send(lengthpath.encode('utf-8'))
            s.send(fpath_receiver.encode('utf-8'))

            filesize = bytes10(os.path.getsize(fpath))
            s.send(filesize.encode('utf-8'))
            f = open(fpath, "rb")
            while counter <= int(filesize):
                data1 = f.read(1024)
                if not (data1):
                    break
                s.send(data1)
                counter += len(data1)
            f.close()

    # changes_list[1] - list of moved lists info
    for change in changes_list[1]:
        s.send('4'.encode('utf-8'))
        src_path = change[0]
        dset_path = change[1]
        src_length = len(src_path.encode('utf-8')) - avoid
        dest_length = len(dset_path.encode('utf-8')) - avoid
        s.send(bytes4(src_length).encode('utf-8'))
        src_path = src_path[avoid:]
        s.send(src_path.encode('utf-8'))

        s.send(bytes4(dest_length).encode('utf-8'))
        dset_path = dset_path[avoid:]
        s.send(dset_path.encode('utf-8'))

    # no more changes to sync
    s.send('0'.encode('utf-8'))


def server_send_changes_list(s, list_change, id):
    # changes_list[2] - list of deleted lists info - important! this is must be the first loop
    for change in list_change:
        option = change[0]
        if option == "3":
            s.send('3'.encode('utf-8'))
            delt_path = change[1]
            length1 = len(delt_path.encode('utf-8'))
            s.send(bytes4(length1).encode('utf-8'))
            s.send(delt_path.encode('utf-8'))

        if option == "1":
            s.send('1'.encode('utf-8'))
            dir_path = change[1]
            length1 = len(dir_path.encode('utf-8'))
            s.send(bytes4(length1).encode('utf-8'))
            s.send(dir_path.encode('utf-8'))
        # create file
        if option == "2":
            s.send('2'.encode('utf-8'))
            counter = 0
            fpath = change[1]
            lengthpath = bytes4(len(fpath.encode('utf-8')))
            s.send(lengthpath.encode('utf-8'))
            s.send(fpath.encode('utf-8'))
            fpath_sender = os.path.join(str(id), fpath)
            filesize = bytes10(os.path.getsize(fpath_sender))
            s.send(filesize.encode('utf-8'))
            f = open(fpath_sender, "rb")
            while counter <= int(filesize):
                data1 = f.read(1024)
                if not (data1):
                    break
                s.send(data1)
                counter += len(data1)
            f.close()

        if option == "4":
            s.send('4'.encode('utf-8'))
            src_path = change[1]
            dest_path = change[2]
            src_length = len(src_path.encode('utf-8'))
            dest_length = len(dest_path.encode('utf-8'))
            s.send(bytes4(src_length).encode('utf-8'))
            s.send(src_path.encode('utf-8'))
            s.send(bytes4(dest_length).encode('utf-8'))
            s.send(dest_path.encode('utf-8'))

    # no more changes to sync
    s.send('0'.encode('utf-8'))

def client_sync_changes_list(s, path, id):
    data = s.recv(1)
    # data = 0 means we finished to sync
    while data.decode('utf-8') != "0":
        # data = 1 create dir
        if data.decode('utf-8') == "1":
            length = (s.recv(4)).decode('utf-8')
            dir_path = (s.recv(int(length))).decode('utf-8')
            currentdir = os.path.join(path, dir_path)
            os.makedirs(currentdir, 0o777, True)

        # data = 2 create file
        if data.decode('utf-8') == "2":
            lenpath = (s.recv(4)).decode('utf-8')
            file_path = s.recv(int(lenpath)).decode('utf-8')
            path = os.path.join(path, file_path)
            file = open(path, 'wb')
            filesize = s.recv(10).decode('utf-8')
            buffer = bytearray()
            while len(buffer) < int(filesize):
                d = (s.recv(int(filesize) - len(buffer)))
                buffer.extend(d)
            file.write(buffer)
            file.close()

        # data = 3 delete dir or file
        if data.decode('utf-8') == "3":
            length = (s.recv(4)).decode('utf-8')
            del_path = (s.recv(int(length))).decode('utf-8')
            currentdir = os.path.join(path, del_path)
            if os.path.exists(currentdir):
                if os.path.isdir(currentdir):
                    delete_dir(currentdir)
                elif os.path.isfile(currentdir):
                    os.remove(currentdir)

        # data = 4 rename file or dir
        if data.decode('utf-8') == "4":
            src_length = (s.recv(4)).decode('utf-8')
            src_path = (s.recv(int(src_length))).decode('utf-8')
            dest_length = (s.recv(4)).decode('utf-8')
            dest_path = (s.recv(int(dest_length))).decode('utf-8')
            src_path = os.path.join(path, src_path)
            dest_path = os.path.join(path, dest_path)
            if os.path.exists(src_path):
                os.rename(src_path, dest_path)
        data = s.recv(1)