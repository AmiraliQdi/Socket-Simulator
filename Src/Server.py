import socket
import threading
import time

from Src import Data
from Src.Data import *

DELAY = 0.2
SERVER_TIME_OUT_LIMIT = 5

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


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
        self.__last_sent_messages = []
        self.__ignore_flag = False

        self.__initialize_socket(connection_type, protocol_type, ip_address, port)
        self.connection_time = 0
        self.__time_out_counter = 0

    def get_connection_time(self, type="s"):
        if type == "s":
            return f"{(time.time() - self.connection_time):.1f}"
        elif type == "i":
            return (time.time() - self.connection_time) - (time.time() - self.connection_time) % 0.01

    def __initialize_socket(self, connection_type, protocol_type, server_ip, server_port):
        s = socket.socket(connection_type, protocol_type)
        s.bind((server_ip, server_port))
        self.__socket = s

    def listen(self):
        self.__socket.listen()
        print("Waiting for client to connect...")
        self.connection, self.client_ip_address = self.__socket.accept()
        self.connection.settimeout(DELAY)
        print(f"Connected to {self.client_ip_address}")
        self.__connection_flag = True
        print("Server is listening")
        print("----------------")
        self.connection_time = time.time()
        try:
            self.start()
        except socket.error:
            print("Disconnected")

    def start(self):
        while self.__connection_flag:
            # self.print_messages()
            self.__read_cycle()
            self.__time_out_logic()
            self.__send_cycle()
            print("----------------")
            self.check_end_flag()
        print(Data.output_stream(self.__buffer))
        self.disconnect()

    def check_end_flag(self):
        if self.__time_out_counter > SERVER_TIME_OUT_LIMIT:
            self.__connection_flag = False

    def disconnect(self):
        self.connection.close()
        self.__socket.close()
        self.__window.clear()
        self.__buffer.clear()

    def print_messages(self):
        print("##### MESSAGES LIST #####")
        for frame in self.__message_frames:
            print(frame.output())
            print(frame.timeout.sent_time)
        print("##########################")
        print("#####   SENT  LIST   #####")
        for frame in self.__last_sent_messages:
            print(frame.output())
            print(frame.timeout.sent_time)
        print("##########################")

    def __time_out_logic(self):
        for frame in self.__last_sent_messages:
            if frame.timeout.is_timed_out(self.get_connection_time("i")):
                self.__message_frames.append(frame)
                self.__last_sent_messages.remove(frame)

    def __read_cycle(self):
        print(f"t={self.get_connection_time()}|ReadCycle::")
        try:
            data = self.connection.recv(1024).decode()
            frame = Data.input_frame(data)
            print(f"Server recv data frame {frame.data}/{frame.id}/{frame.p}")
            time.sleep(DELAY)
        except socket.timeout:
            print("Timeout")
            return

        if frame.data == "NONE" and frame.id == -1 and frame.p == -1:
            self.__time_out_counter += 1

        if len(self.__buffer) == 0 and len(self.__window) == 0:
            suspected_frame_id = 0
        elif len(self.__buffer) != 0 and len(self.__window) == 0:
            suspected_frame_id = (self.__buffer[-1].id + 1) % self.__sequence_number
        else:
            suspected_frame_id = (self.__window[-1].id + 1) % self.__sequence_number

        # data not received TODO
        if frame.p == -1:
            print("Timeout")
        # INST frame TODO
        elif frame.p == 1:
            print("INST recv")
        # window id match suspected id
        elif frame.id == suspected_frame_id:
            self.__window.append(frame)
            print(f"***Correct frame received[{suspected_frame_id}]***")
            self.__ignore_flag = False
            self.__remove_error_frame(suspected_frame_id)
            suspected_frame_id += 1
        # just ignore
        elif self.__ignore_flag:
            print(f"*Wrong frame received[{suspected_frame_id}]*")
            print("Ignored receiving frame")
        # window id does not match suspected id
        else:
            # ignore packets with no data for error handling
            if frame.data != "NONE":
                print(f"*Wrong frame received[{suspected_frame_id}]*")
                if len(self.__last_sent_messages) > 0:
                    last_message = self.__last_sent_messages[-1]
                    # ignore recv frame until correct frame recv ( don't send new REJ frame)
                    if last_message.data == "REJ" and last_message.id == suspected_frame_id:
                        print("Ignored receiving frame")
                        self.__ignore_flag = True
                    # ignore recv frame and send new REJ frame
                    else:
                        self.__add_new_message("REJ", suspected_frame_id)
                else:
                    self.__add_new_message("REJ", suspected_frame_id)

        # window filled
        if len(self.__window) == self.__window_size:
            self.__add_window_to_buffer()
            self.__window.clear()
            # if last sent message had same frame id don't bother
            if len(self.__last_sent_messages) > 0 and self.__last_sent_messages[-1].id \
                    == suspected_frame_id % self.__sequence_number:
                pass
            else:
                self.__add_new_message("RR", suspected_frame_id % self.__sequence_number)

    def __add_new_message(self, data, f_id):
        if data == "REJ":
            for frame in self.__last_sent_messages:
                if frame.data == "RR" and frame.id == f_id:
                    self.__last_sent_messages.remove(frame)
            rej_frame = Frame("REJ", f_id, 1)
            self.__message_frames.append(rej_frame)
            print(f"new REJ message added to list")
        elif data == "RR":
            for frame in self.__last_sent_messages:
                if frame.data == "REJ":
                    return
            rej_frame = Frame("RR", f_id, 1)
            self.__message_frames.append(rej_frame)
            print(f"new RR message added to list")

    def __remove_error_frame(self, suspected_frame_id):
        for frame in self.__last_sent_messages:
            if frame.id == suspected_frame_id:
                self.__last_sent_messages.remove(frame)
                if frame.data == "REJ":
                    print(f"REJ frame with id {suspected_frame_id}, corrected and removed form sending list")
                elif frame.data == "RR":
                    print(f"RR frame with id {suspected_frame_id}, corrected and removed form sending list")

    def __add_window_to_buffer(self):
        for frame in self.__window:
            self.__buffer.append(frame)

    def __send_cycle(self):
        print(f"t={self.get_connection_time()}|SendCycle::")
        if len(self.__message_frames) > 0:
            sending_message = self.__message_frames.pop(0)
            sending_message.set_sent_time(self.get_connection_time(type="i"))
            self.__last_sent_messages.append(sending_message)
            print(f"Server trans: {sending_message.output()}")
            self.connection.send(sending_message.output().encode())
        else:
            print("Server trans nothing")
            pass

    def __print_message_buffer(self):
        for frame in server.__message_frames:
            print(frame.output())


server = Server("127.0.0.1", 8080, 5, 8)
server.listen()
