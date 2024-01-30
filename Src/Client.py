import socket
import time

import Data


class Client:

    def __init__(self, connection_type=socket.AF_INET, protocol_type=socket.SOCK_STREAM):
        self.__connection_type = connection_type
        self.__protocol_type = protocol_type
        self.socket = self.__initialize_socket()
        self.__transmit_window = []
        self.__reciever_window = []
        self.__connection_flag = False
        self.__current_frame = None

    def __initialize_socket(self):
        s = socket.socket(self.__connection_type, self.__protocol_type)
        return s

    def connect(self, ip_address, port):
        self.socket.connect((ip_address, port))
        self.__connection_flag = True

    def start(self):
        while self.__connection_flag:
            data = self.socket.recv(1024)
            frame = Data.make_frame(data)
            if frame.p == 0:


