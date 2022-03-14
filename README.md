# DriveCloud
a cloud which you upload a directory to, it saves the directory on the cloud.
In addition, it monitors the changes on the directory on the client's computer and change the directory on the cloud according to those changes.
the comminucation is based on TCP.

# Instructions
on one computer open the server, on the other one open the client (the functions for both of them are in utils.py)
the arguments for the server is the number of the port.
the arguments for the client are 1. Ip of the server, 2. port of the server, 3. path to the directory, 4. time (in seconds) to sync with the server.
