import socket
import time

import Data

DELAY = 1

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
        self.__corrupted_frames = []
        self.__buffer_index = 0
        self.__waiting_flag = False
        self.__connection_module = None
        self.__last_sent_frames = []

        self.text_redirector = None

    def set_text_redirector(self, text_redirector):
        self.text_redirector = text_redirector

    def print_to_gui(self, message):
        if self.text_redirector:
            self.text_redirector.write(message)

    def get_connection_time(self):
        return f"{(time.time() - self.connection_time):.1f}"

    def __initialize_socket(self):
        s = socket.socket(self.__connection_type, self.__protocol_type)
        s.settimeout(DELAY)
        return s

    def connect(self, ip_address, port):
        self.print_to_gui(f"Trying to connect to {ip_address}:{port}\n")
        self.socket.connect((ip_address, port))
        self.__connection_flag = True
        self.print_to_gui(f"Connection successful\n")
        self.print_to_gui("----------------\n")
        self.connection_time = time.time()

    def start(self, connection_module):
        self.__connection_module = connection_module
        if connection_module == "GOBACK":
            self.__go_back_module()
        elif connection_module == "SELECTIVE":
            self.__selective_module()

    def __go_back_module(self):
        self.__update_window()
        while self.__connection_flag:
            self.__print_window()

            self.__send_cycle()

            if self.__sending_index == self.__window_size:
                self.__waiting_flag = True

            self.__read_cycle()

            if self.__is_done():
                self.end_connection()
            self.print_to_gui("----------------\n")

    def __is_done(self):
        if self.__window_index * self.__window_size + self.__sending_index >= len(self.__buffer):
            return True
        else:
            return False

    def __update_window(self):
        self.__window.clear()
        for i in range(self.__window_size):
            try:
                self.__window.append(
                    self.__buffer[(self.__window_size * self.__window_index) + self.__sending_index + i])
            except IndexError:
                continue

    def end_connection(self):
        self.print_to_gui("Disconnected\n")
        self.__connection_flag = False
        self.socket.close()
        self.__window.clear()

    def __send_cycle(self):
        self.print_to_gui(f"t={self.get_connection_time()}|SendCycle::\n")
        if self.__waiting_flag:
            return
        else:
            pass
        data = self.__window[self.__sending_index]
        self.print_to_gui(f"Client trans {data.data}/{data.id}\n")
        self.socket.send(data.output().encode())
        self.__sending_index += 1

    def __selective_module(self):
        for i in range(self.__sequence_number):
            self.__last_sent_frames.append(None)

        self.__update_window_SEL()

        while self.__connection_flag:

            self.__print_window()

            self.__send_cycle_SEL()

            self.__read_cycle_SEL()

            self.__update_window_SEL()

            self.__corruption_logic()

            if self.__is_done():
                self.end_connection()
            self.print_to_gui("----------------\n")

    def __update_window_SEL(self):
        self.__window.clear()
        for i in range(self.__window_size):
            try:
                self.__window.append(self.__buffer[self.__buffer_index + i])
            except:
                self.disconnect()

    def __update_last_frames(self, frame):
        self.__last_sent_frames[frame.id] = frame

    def __corruption_logic(self):
        if len(self.__corrupted_frames) > 0:
            first_corrupted_in_list = self.__corrupted_frames.pop(0)
            fixing_frame = self.__last_sent_frames[first_corrupted_in_list]
            new_window = self.__shift()
            try:
                new_window.insert(0, fixing_frame)
            except:
                self.disconnect()
            self.__window = new_window
            self.__buffer_index -= 1

    def __shift(self):
        new_window = []
        try:
            for i in range(self.__window_size - 1):
                new_window.append(self.__window[i])
            return new_window
        except:
            self.disconnect()
            return

    def disconnect(self):
        self.socket.close()
        self.__connection_flag = False
        self.print_to_gui("Disconnected\n")
        return

    def __send_cycle_SEL(self):
        self.print_to_gui(f"t={self.get_connection_time()}|SendCycle::\n")
        if self.__waiting_flag:
            self.print_to_gui("Waiting\n")
            return
        else:
            pass
        for i in range(self.__window_size):
            frame = self.__window[i]
            self.__update_last_frames(frame)
            data = self.__window[i]
            self.print_to_gui(f"Client trans {data.data}/{data.id}\n")
            self.socket.send(data.output().encode())
            time.sleep(DELAY)
            self.__buffer_index += 1
            self.__waiting_flag = True

    def __read_cycle_SEL(self):
        self.print_to_gui(f"t={self.get_connection_time()}|ReadCycle::\n")
        try:
            message = self.socket.recv(1024).decode()
            frame = Data.input_frame(message)
            time.sleep(DELAY)
        except socket.timeout:
            self.print_to_gui("Timeout\n")
            return
        if frame.p == 1:
            if frame.data == "RR":
                self.__waiting_flag = False
                self.print_to_gui(f"Client recv: {GREEN}{frame.data}{RESET}/{frame.id}\n")
            elif frame.data == "REJ":
                # self.print_to_gui(
                #    f"sending index was {self.__window[self.__sending_index].id} but changed to {frame.id} by REJ")
                self.print_to_gui(f"Client recv: {RED}{frame.data}{RESET}/{frame.id}\n")
                self.__corrupted_frames.append(frame.id)
                self.__waiting_flag = False

    def __print_window(self):
        self.print_to_gui("{ ")
        for frame in self.__window:
            self.print_to_gui(f"{frame.data}/{frame.id} ,")
        self.print_to_gui("}")

    def __read_cycle(self):
        self.print_to_gui(f"t={self.get_connection_time()}|ReadCycle::\n")
        try:
            message = self.socket.recv(1024).decode()
            frame = Data.input_frame(message)
            time.sleep(DELAY)
        except socket.timeout:
            self.print_to_gui("Timeout\n")
            return
        if frame.p == 1:
            if frame.data == "RR" and self.__check_if_RR_needed(frame):
                self.__waiting_flag = False
                self.__window_index += 1
                self.__sending_index = 0
                self.__update_window()
                self.print_to_gui(f"Client recv: {GREEN}{frame.data}{RESET}/{frame.id}\n")
            elif frame.data == "REJ":
                # self.print_to_gui(
                #    f"sending index was {self.__window[self.__sending_index].id} but changed to {frame.id} by REJ")
                self.__waiting_flag = False
                self.__sending_index = self.__find_frameIndex_from_frameID(frame.id)
                self.print_to_gui(f"Client recv: {RED}{frame.data}{RESET}/{frame.id}\n")

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
            self.print_to_gui(frame.output())


# client = Client(4, 8)
# client.connect("127.0.0.1", 8080)
# client.send_data(
#     "In a bustling city, a hidden cafe exudes warmth with the scent of freshly brewed coffee and soft jazz."
#     " Patrons immersed in creativity, sunlight filtering through curtains, "
#     "and a meticulous barista crafting indulgent moments. "
#     "A quiet oasis where time slows amid aromatic swirls and hushed conversations.")
# client.send_data("NONE")
# client.start("GOBACK")
