import socket
import time

from Src import Data
from Src.Data import *


class Server:

    def __init__(self, ip_address, port, window_size, sequence_number, connection_type=socket.AF_INET,
                 protocol_type=socket.SOCK_STREAM):

        self.connection, self.client_ip_address = None, None
        self.__connection_flag = False
        self.__socket = None

        self.__sequence_number = sequence_number
        self.__window_size = window_size
        self.__window = []
        self.__buffer = []
        self.__message_frames = []

        self.__initialize_socket(connection_type, protocol_type, ip_address, port)

    def __initialize_socket(self, connection_type, protocol_type, server_ip, server_port):
        s = socket.socket(connection_type, protocol_type)
        s.bind((server_ip, server_port))
        self.__socket = s

    def listen(self):
        self.__socket.listen()
        print("Waiting for client to connect...")
        self.connection, self.client_ip_address = self.__socket.accept()
        print(f"Connected to {self.client_ip_address}")
        self.__connection_flag = True
        print("Server is listening")
        self.start()

    def start(self):
        connection_time = 0
        while self.__connection_flag:
            time.sleep(1)
            print(f"t={connection_time}  ", end="")
            self.__read_cycle()
            self.__send_cycle()
            connection_time += 1

    def __read_cycle(self):
        data = self.connection.recv(1024).decode()
        frame = Data.input_frame(data)
        suspected_frame_id = (len(self.__buffer) + len(self.__window)) % self.__sequence_number
        # data not received TODO
        if frame.p == -1:
            print("No data received form client")
        # wrong frame type
        elif frame.p == 1:
            print("Wrong frame type from client, p bit was 1")
        # window id match suspected id
        elif frame.id == suspected_frame_id:
            print(f"Server recv data frame {frame.id}")
            self.__window.append(frame)
            suspected_frame_id += 1
        # window id does not match suspected id TODO
        else:
            srej_frame = Frame("REJ", suspected_frame_id, 1)
            self.__message_frames.append(srej_frame)

        # window filled
        if len(self.__window) == self.__window_size:
            self.__add_window_to_buffer()
            self.__window.clear()
            rr_frame = Frame("RR", suspected_frame_id % self.__sequence_number, 1)
            self.__message_frames.append(rr_frame)

    def __add_window_to_buffer(self):
        for frame in self.__window:
            self.__buffer.append(frame)

    def __send_cycle(self):
        if len(self.__message_frames) > 0:
            data = self.__message_frames[0].output()
            self.__message_frames.pop(0)
            print(f"Server trans: {data}")
            self.connection.sendall(data.encode())
        else:
            pass

    def __print_message_buffer(self):
        for frame in server.__message_frames:
            print(frame.output())


server = Server("127.0.0.1", 8080, 2, 8)
server.listen()
