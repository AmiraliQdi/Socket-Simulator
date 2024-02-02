import socket
import threading
import time

from Src import Data
from Src.Data import *

RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'


class Server:

    def __init__(self, ip_address, port, window_size, sequence_number, timeout=1.0, connection_type=socket.AF_INET,
                 protocol_type=socket.SOCK_STREAM):

        self.connection, self.client_ip_address = None, None
        self.__connection_flag = False
        self.__socket = self.__initialize_socket(connection_type, protocol_type, ip_address, port)
        self.__socket.settimeout(timeout)

        self.__sequence_number = sequence_number
        self.__window_size = window_size
        self.__window = []
        self.__buffer = []
        self.__message_frames = []

        self.__receiving_thread = threading.Thread(target=self.__read_cycle, name="R-thread")
        self.__sending_thread = threading.Thread(target=self.__send_cycle, name="S-thread")
        self.__manage_thread = threading.Thread(target=self.__manage_thread_start, name="M-thread")
        self.connection_time = 0

    def __initialize_socket(self, connection_type, protocol_type, server_ip, server_port):
        s = socket.socket(connection_type, protocol_type)
        s.bind((server_ip, server_port))
        return s

    def listen(self, timeout=1.0):
        try:
            self.__socket.listen()
            self.connection, self.client_ip_address = self.__socket.accept()
            print(f"Connected to {self.client_ip_address}")
            self.__connection_flag = True
            print("Server is listening")
            self.connection.settimeout(timeout)
            return
        except socket.timeout:
            print("Waiting for client to connect...")
            self.listen()

    def start(self):
        self.__manage_thread.start()

    def __manage_thread_start(self):
        self.connection_time = time.time()
        self.__receiving_thread.start()
        # self.__sending_thread.start()
        while self.__connection_flag:
            pass

    def __get_current_time(self):
        return time.time() - self.connection_time

    def __read_cycle(self):
        counter = 0
        while self.__connection_flag:
            if len(self.__window) == 0 and len(self.__buffer) == 0:
                suspected_frame_id = 0
            elif len(self.__window) == 0 and len(self.__buffer) != 0:
                suspected_frame_id = self.__buffer[-1].id + 1
            else:
                suspected_frame_id = self.__window[-1].id + 1
            try:
                data = self.connection.recv(1024).decode()
                frame = Data.input_frame(data)
            except socket.timeout:
                print(
                    f"Server/{RED}Read{RESET} {self.__get_current_time():.1f} | Timeout: No data received from client. {counter}")
                continue
            print(f"recv frame :{data}, wanted:{suspected_frame_id}| {counter}")
            counter += 1
            # data not received TODO
            if frame.p == -1:
                print(
                    f"Server/{RED}Read{RESET} {self.__get_current_time():.1f} | (OLD ERROR)")
                pass
            # Inst FRAME
            elif frame.p == 1:
                pass
            # TODO
            # window id match suspected id
            elif frame.id == suspected_frame_id:
                print(f"Server/{RED}Read{RESET} {self.__get_current_time():.1f} | recv data frame {frame.id}")
                self.__window.append(frame)
                suspected_frame_id += 1
            # window id does not match suspected id TODO
            else:
                print("ERROR ADDED")
                rej_frame = Frame("REJ", suspected_frame_id, 1)
                self.__message_frames.append(rej_frame)

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
        while self.__connection_flag:
            if len(self.__message_frames) > 0:
                data = self.__message_frames[0].output()
                self.__message_frames.pop(0)
                self.connection.sendall(data.encode())
                print(f"Server/{GREEN}Send{RESET} {self.__get_current_time():.1f} | trans: {data}")
            else:
                print(f"Server/{GREEN}Send{RESET} {self.__get_current_time():.1f} | trans: none")
                pass
            time.sleep(1)

    def __print_message_buffer(self):
        for frame in server.__message_frames:
            print(frame.output())


server = Server("127.0.0.1", 8080, 2, 8)
server.listen()
server.start()
