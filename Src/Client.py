import socket
import time

import Data


class Client:

    def __init__(self, window_size, sequence_number, connection_type=socket.AF_INET, protocol_type=socket.SOCK_STREAM):
        self.__connection_type = connection_type
        self.__sequence_number = sequence_number
        self.__protocol_type = protocol_type
        self.socket = self.__initialize_socket()
        self.__connection_flag = False
        self.__buffer = []
        self.__window = []
        self.__window_size = window_size
        self.__message_buffer = []
        self.__sending_index = 0

    def __initialize_socket(self):
        s = socket.socket(self.__connection_type, self.__protocol_type)
        return s

    def connect(self, ip_address, port):
        print(f"Trying to connect to {ip_address}:{port}")
        self.socket.connect((ip_address, port))
        self.__connection_flag = True
        print(f"Connection successful")

    def start(self):
        read_cycle_counter = 1
        connection_time = 0
        while self.__connection_flag:
            print(f"t={connection_time} ",end=" ")
            if self.__sending_index == len(self.__buffer):
                self.__connection_flag = False
                self.socket.close()
                break
            time.sleep(1)
            self.__send_cycle()
            if read_cycle_counter % self.__window_size == 0:
                self.__read_cycle()
            connection_time += 1
            read_cycle_counter += 1

    def __send_cycle(self):
        data = self.__buffer[self.__sending_index].output()
        print(f"Client trans data frame {self.__sending_index}")
        self.__sending_index += 1
        self.socket.send(data.encode())

    def __read_cycle(self):
        message = self.socket.recv(1024).decode()
        frame = Data.input_frame(message)
        print(f"Client recv: {frame.data}/{frame.id}")


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