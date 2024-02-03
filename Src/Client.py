import socket
import time

import Data

DELAY = 0.2

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

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
        self.__window_index = 0
        self.connection_time = 0
        self.__waiting_flag = False

    def get_connection_time(self):
        return f"{(time.time() - self.connection_time):.1f}"

    def __initialize_socket(self):
        s = socket.socket(self.__connection_type, self.__protocol_type)
        s.settimeout(DELAY)
        return s

    def connect(self, ip_address, port):
        print(f"Trying to connect to {ip_address}:{port}")
        self.socket.connect((ip_address, port))
        self.__connection_flag = True
        print(f"Connection successful")
        print("----------------")
        self.connection_time = time.time()

    def start(self):
        self.__update_window()
        while self.__connection_flag:
            self.__print_window()

            self.__send_cycle()

            if self.__sending_index == self.__window_size:
                self.__waiting_flag = True

            self.__read_cycle()

            if self.__is_done():
                self.end_connection()
            print("----------------")

    def __is_done(self):
        if self.__window_index * self.__window_size + self.__sending_index >= len(self.__buffer):
            return True
        else:
            return False

    def __update_window(self):
        self.__last_window = self.__window
        self.__window.clear()
        for i in range(self.__window_size):
            try:
                self.__window.append(
                    self.__buffer[(self.__window_size * self.__window_index) + self.__sending_index + i])
            except IndexError:
                continue

    def end_connection(self):
        print("Disconnected")
        self.__connection_flag = False
        self.socket.close()
        self.__window.clear()

    def __send_cycle(self):
        print(f"t={self.get_connection_time()}|SendCycle::")
        if self.__waiting_flag:
            return
        else:
            pass
        data = self.__window[self.__sending_index]
        print(f"Client trans {data.data}/{data.id}")
        self.socket.send(data.output().encode())
        self.__sending_index += 1

    def __print_window(self):
        print("{ ", end="")
        for frame in self.__window:
            print(f"{frame.data}/{frame.id} ,", end="")
        print("}")

    def __read_cycle(self):
        print(f"t={self.get_connection_time()}|ReadCycle::")
        try:
            message = self.socket.recv(1024).decode()
            frame = Data.input_frame(message)
            time.sleep(DELAY)
        except socket.timeout:
            print("Timeout")
            return
        if frame.p == 1:
            if frame.data == "RR" and self.__check_if_RR_needed(frame):
                self.__waiting_flag = False
                self.__window_index += 1
                self.__sending_index = 0
                self.__update_window()
                print(f"Client recv: {GREEN}{frame.data}{RESET}/{frame.id}")
            elif frame.data == "REJ":
                #print(
                #    f"sending index was {self.__window[self.__sending_index].id} but changed to {frame.id} by REJ")
                self.__waiting_flag = False
                self.__sending_index = self.__find_frameIndex_from_frameID(frame.id)
                print(f"Client recv: {RED}{frame.data}{RESET}/{frame.id}")

    def __check_if_RR_needed(self, rr_frame):
        if self.__window[0].id == rr_frame.id:
            return False
        else:
            return True

    def __find_frameIndex_from_frameID(self, frameID):
        counter = 0
        for frame in self.__window:
            if frame.id == frameID:
                return counter
            else:
                counter += 1
        raise Exception("Could not find suspected frame in current window")

    def send_data(self, data):
        starting_index = 0
        if len(self.__buffer) != 0:
            starting_index = self.__buffer[-1].id + 1
        input_frames = Data.input_stream(data, self.__sequence_number, starting_index)
        self.__add_new_data_to_buffer(input_frames)

    def __add_new_data_to_buffer(self, input_frames):
        for frame in input_frames:
            self.__buffer.append(frame)

    def print_buffer(self):
        for frame in self.__buffer:
            print(frame.output())


client = Client(5, 8)
client.connect("127.0.0.1", 8080)
client.send_data(
    "In a bustling city, a hidden cafe exudes warmth with the scent of freshly brewed coffee and soft jazz."
    " Patrons immersed in creativity, sunlight filtering through curtains, "
    "and a meticulous barista crafting indulgent moments. "
    "A quiet oasis where time slows amid aromatic swirls and hushed conversations.")
client.send_data("NONE")
client.start()
