import socket
import threading
import time

import Data

RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'


class Client:

    def __init__(self, window_size, sequence_number, timeout=1.0, connection_type=socket.AF_INET,
                 protocol_type=socket.SOCK_STREAM):
        self.__sequence_number = sequence_number
        self.socket = self.__initialize_socket(connection_type, protocol_type)
        self.socket.settimeout(timeout)
        self.__connection_flag = False
        self.__buffer = []
        self.__window = []
        self.__window_size = window_size
        self.__message_buffer = []
        self.__sending_index = 0
        self.__sequence_packet_counter = 0
        self.__receiving_thread = threading.Thread(target=self.__read_cycle, daemon=True, name="R-thread")
        self.__sending_thread = threading.Thread(target=self.__send_cycle, daemon=True, name="S-thread")
        self.__manage_thread = threading.Thread(target=self.__manage_thread_start, name="M-thread")
        self.connection_time = 0

    def __initialize_socket(self, connection_type, protocol_type):
        s = socket.socket(connection_type, protocol_type)
        return s

    def connect(self, ip_address, port):
        print(f"Trying to connect to {ip_address}:{port}")
        try:
            self.socket.connect((ip_address, port))
            self.__connection_flag = True
            print(f"Connection successful")
            return
        except socket.timeout:
            time.sleep(1)
            self.connect(ip_address, port)

    def start(self):
        self.__manage_thread.start()

    def __manage_thread_start(self):

        self.connection_time = time.time()
        self.__update_window()

        self.__sending_thread.start()
        # self.__receiving_thread.start()

    def close_connection(self):
        self.__buffer.clear()
        self.__window.clear()
        self.__connection_flag = False
        self.socket.close()

    def __update_window(self):
        for i in range(self.__window_size):
            self.__window.append(
                self.__buffer[(self.__sequence_number * self.__sequence_packet_counter) + self.__sending_index + i])

    def __send_cycle(self):
        while self.__connection_flag:
            sending_frame = self.__window.pop(0)
            self.socket.send(sending_frame.output().encode())
            print(
                f"Client/{GREEN}Send{RESET} {self.__get_current_time():.1f} | trans data frame {sending_frame.id}")
            self.__sending_index += 1
            if len(self.__window) == 0:
                print("window empt")
                self.__sequence_packet_counter += 1
                self.__update_window()
            if (self.__sequence_packet_counter * self.__sequence_number) + self.__sending_index > len(self.__buffer):
                print("ALL DATA TRANSMITTED")
                self.__connection_flag = False
                self.close_connection()
            time.sleep(1)

    def __get_current_time(self):
        return time.time() - self.connection_time

    def __read_cycle(self):
        while self.__connection_flag:
            try:
                message = self.socket.recv(1024).decode()
                frame = Data.input_frame(message)
                self.__message_buffer.append(frame)
                print(f"Client/{RED}Read{RESET} {self.__get_current_time():.1f} | recv: {frame.data}/{frame.id}")
            except socket.timeout:
                print(
                    f"Client/{RED}Read{RESET} {self.__get_current_time():.1f} |Timeout: No data received from server.")

    def send_data(self, data):
        input_frames = Data.input_stream(data, self.__sequence_number, len(self.__buffer) + len(self.__window))
        self.__add_new_data_to_buffer(input_frames)

    def __add_new_data_to_buffer(self, input_frames):
        for frame in input_frames:
            self.__buffer.append(frame)

    def print_buffer(self):
        for frame in self.__buffer:
            print(frame.output())


client = Client(2, 8)
client.connect("127.0.0.1", 8080)
client.send_data("Hi my name is Amirali Ghaedi")
client.send_data("and I am so happy to be here with you guys and so funny too hooray")
client.start()
