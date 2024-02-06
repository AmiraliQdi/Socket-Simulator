import socket
import threading
import time

from Src import Data
from Src.Data import *

DELAY = 1
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

        self.__srej_flag = False
        self.__suspected_mistaken_frame = -1
        self.__last_correct_frame = -1
        self.__srej_buffer = []
        self.__srej_buffer_frames_index = []

        self.text_redirector = None

    def set_text_redirector(self, text_redirector):
        self.text_redirector = text_redirector

    def print_to_gui(self, message):
        if self.text_redirector:
            self.text_redirector.write(message)
            self.text_redirector.text_widget.after(0, lambda: self.text_redirector.text_widget.update_idletasks())

    def get_connection_time(self, type="s"):
        if type == "s":
            return f"{(time.time() - self.connection_time):.1f}"
        elif type == "i":
            return (time.time() - self.connection_time) - (time.time() - self.connection_time) % 0.01

    def __initialize_socket(self, connection_type, protocol_type, server_ip, server_port):
        s = socket.socket(connection_type, protocol_type)
        s.bind((server_ip, server_port))
        self.__socket = s

    def listen(self, connection_module):
        self.__socket.listen()
        self.print_to_gui("Waiting for client to connect...\n")
        self.connection, self.client_ip_address = self.__socket.accept()
        self.connection.settimeout(DELAY)
        self.print_to_gui(f"Connected to {self.client_ip_address}\n")
        self.__connection_flag = True
        self.print_to_gui("Server is listening\n")
        self.print_to_gui("----------------")
        self.connection_time = time.time()
        try:
            self.start(connection_module)
        except socket.error:
            self.print_to_gui("Disconnected\n")

    def start(self, connection_module):
        if connection_module == "GOBACK":
            self.__go_back_module()
        elif connection_module == "SELECTIVE":
            self.__selective_module()

        self.print_to_gui(Data.output_stream(self.__buffer))
        self.disconnect()

    def __go_back_module(self):
        while self.__connection_flag:
            # self.print_messages()
            self.__read_cycle()
            self.__time_out_logic()
            self.__send_cycle()
            self.print_to_gui("----------------\n")
            self.check_end_flag()

    def __selective_module(self):
        while self.__connection_flag:
            self.__print_srej_buffer()
            self.__read_cycle_SEL()
            self.__rej_buffer_logic()
            self.__send_cycle_SEL()
            time.sleep(DELAY)
            self.print_to_gui("----------------\n")
            self.check_end_flag()

    def check_end_flag(self):
        if self.__time_out_counter > SERVER_TIME_OUT_LIMIT:
            self.__connection_flag = False

    def disconnect(self):
        self.connection.close()
        self.__socket.close()
        self.__window.clear()
        self.__buffer.clear()

    def print_messages(self):
        self.print_to_gui("##### MESSAGES LIST #####\n")
        for frame in self.__message_frames:
            self.print_to_gui(frame.output())
            self.print_to_gui(frame.timeout.sent_time)
        self.print_to_gui("##########################\n")
        self.print_to_gui("#####   SENT  LIST   #####\n")
        for frame in self.__last_sent_messages:
            self.print_to_gui(frame.output())
            self.print_to_gui(frame.timeout.sent_time)
        self.print_to_gui("##########################\n")

    def __time_out_logic(self):
        for frame in self.__last_sent_messages:
            if frame.timeout.is_timed_out(self.get_connection_time("i")):
                self.__message_frames.append(frame)
                self.__last_sent_messages.remove(frame)

    def __read_cycle(self):
        self.print_to_gui(f"t={self.get_connection_time()}|ReadCycle::\n")
        try:
            data = self.connection.recv(1024).decode()
            frame = Data.input_frame(data)
            self.print_to_gui(f"Server recv data frame {frame.data}/{frame.id}/{frame.p}\n")
            time.sleep(DELAY)
        except socket.timeout:
            self.print_to_gui("Timeout\n")
            return

        # counting timeout limit for disconnect
        if frame.data == "NONE" and frame.id == -1 and frame.p == -1:
            self.__time_out_counter += 1

        # calculate suspected frame id
        if len(self.__buffer) == 0 and len(self.__window) == 0:
            suspected_frame_id = 0
        elif len(self.__buffer) != 0 and len(self.__window) == 0:
            suspected_frame_id = (self.__buffer[-1].id + 1) % self.__sequence_number
        else:
            suspected_frame_id = (self.__window[-1].id + 1) % self.__sequence_number

        # data not received TODO
        if frame.p == -1:
            self.print_to_gui("Timeout (p = -1)\n")
        # INST frame TODO
        elif frame.p == 1:
            self.print_to_gui("INST recv\n")
        # window id match suspected id
        elif frame.id == suspected_frame_id:
            self.__window.append(frame)
            self.print_to_gui(f"***Correct frame received[{suspected_frame_id}]***\n")
            self.__ignore_flag = False
            # TODO REMOVED ERROR CLEARING
            self.__remove_error_frame(suspected_frame_id)
            suspected_frame_id += 1
        # just ignore
        elif self.__ignore_flag:
            self.print_to_gui(f"*Wrong frame received[{suspected_frame_id}]*\n")
            self.print_to_gui("Ignored receiving frame\n")
        # window id does not match suspected id
        else:
            # ignore packets with no data for error detection
            if frame.data != "NONE":
                self.print_to_gui(f"*Wrong frame received[{suspected_frame_id}]*\n")
                if len(self.__last_sent_messages) > 0:
                    last_message = self.__last_sent_messages[-1]
                    # ignore recv frame until correct frame recv ( don't send new REJ frame)
                    if last_message.data == "REJ" and last_message.id == suspected_frame_id:
                        self.print_to_gui("Ignored receiving frame\n")
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

    def __rej_buffer_logic(self):
        if len(self.__srej_buffer) > 0:
            corrupted_frame = self.__srej_buffer[0]
            self.__srej_flag = True
            self.__suspected_mistaken_frame = corrupted_frame.id
        else:
            self.__srej_flag = False
            self.__suspected_mistaken_frame = -1

    def __read_cycle_SEL(self):
        self.print_to_gui(f"t={self.get_connection_time()}|ReadCycle::\n")
        frame = None
        if self.__srej_flag:
            try:
                data = self.connection.recv(1024).decode()
                frame = Data.input_frame(data)
                self.print_to_gui(f"Server recv data frame {frame.data}/{frame.id}/{frame.p}\n")
                time.sleep(DELAY)
            except socket.timeout:
                self.print_to_gui("Timeout\n")
                self.__read_cycle_SEL()

            if frame.id == self.__suspected_mistaken_frame:
                self.print_to_gui(f"***Correct frame received[{frame.id}]***\n")
                self.__buffer[self.__srej_buffer_frames_index[0]] = frame
                self.print_to_gui(f"{GREEN}SREJ corruption fixed{RESET}\n")
                # self.__srej_buffer.pop(0)
                self.__srej_buffer_frames_index.pop(0)
            else:
                self.print_to_gui(f"*Wrong frame received[{self.__suspected_mistaken_frame}]*\n")
                self.__srej_buffer_frames_index.pop(0)
                self.print_to_gui("Ignored this corruption because of timeout\n")

            for i in range(self.__window_size - 1):

                try:
                    data = self.connection.recv(1024).decode()
                    frame = Data.input_frame(data)
                    self.print_to_gui(f"Server recv data frame {frame.data}/{frame.id}/{frame.p}\n")
                    time.sleep(DELAY)
                except socket.timeout:
                    self.print_to_gui("Timeout\n")
                    continue

                self.__buffer.append(frame)

                suspected_frame_id = self.__last_correct_frame + 1
                if suspected_frame_id >= self.__sequence_number:
                    suspected_frame_id = 0

                if frame.id == suspected_frame_id:
                    self.print_to_gui(f"***Correct frame received[{suspected_frame_id}]***\n")
                    self.__window.append(frame)
                    self.__last_correct_frame += 1
                    if self.__last_correct_frame >= self.__sequence_number:
                        self.__last_correct_frame = 0


                else:
                    self.print_to_gui(f"*Wrong frame received[{suspected_frame_id}]*\n")
                    srej_frame = Frame("REJ", suspected_frame_id, 1)
                    self.__srej_buffer.append(srej_frame)
                    self.__srej_buffer_frames_index.append(len(self.__buffer) - 1)
                    self.__window.append(frame)
                    self.__last_correct_frame += 1
                    if self.__last_correct_frame >= self.__sequence_number:
                        self.__last_correct_frame = 0


        else:
            for i in range(self.__window_size):
                try:
                    data = self.connection.recv(1024).decode()
                    frame = Data.input_frame(data)
                    self.print_to_gui(f"Server recv data frame {frame.data}/{frame.id}/{frame.p}\n")
                    time.sleep(DELAY)
                except socket.timeout:
                    self.print_to_gui("Timeout\n")
                    continue

                suspected_frame_id = self.__last_correct_frame + 1
                if suspected_frame_id >= self.__sequence_number:
                    suspected_frame_id = 0

                self.__buffer.append(frame)

                if frame.id == suspected_frame_id:
                    self.print_to_gui(f"***Correct frame received[{suspected_frame_id}]***\n")
                    self.__window.append(frame)
                    self.__last_correct_frame += 1
                    if self.__last_correct_frame >= self.__sequence_number:
                        self.__last_correct_frame = 0

                else:
                    self.print_to_gui(f"*Wrong frame received[{suspected_frame_id}]*\n")
                    srej_frame = Frame("REJ", suspected_frame_id, 1)
                    self.__srej_buffer.append(srej_frame)
                    self.__srej_buffer_frames_index.append(len(self.__buffer) - 1)
                    self.__window.append(frame)
                    self.__last_correct_frame += 1
                    if self.__last_correct_frame >= self.__sequence_number:
                        self.__last_correct_frame = 0

    def __send_cycle_SEL(self):
        self.print_to_gui(f"t={self.get_connection_time()}|SendCycle::\n")
        if len(self.__srej_buffer) > 0:
            sending_message = self.__srej_buffer.pop(0)
            self.__srej_flag = True
            self.__suspected_mistaken_frame = sending_message.id
        else:
            rr_frame = Frame("RR", (self.__last_correct_frame + 1) % self.__sequence_number, 1)
            sending_message = rr_frame
        self.connection.send(sending_message.output().encode())
        self.print_to_gui(f"Server trans: {sending_message.output()}\n")
        time.time()

    def __add_new_message(self, data, f_id):
        if data == "REJ":
            for frame in self.__last_sent_messages:
                if frame.data == "RR" and frame.id == f_id:
                    self.__last_sent_messages.remove(frame)
            rej_frame = Frame("REJ", f_id, 1)
            self.__message_frames.append(rej_frame)
            self.print_to_gui(f"new REJ message added to list\n")
        elif data == "RR":
            for frame in self.__last_sent_messages:
                if frame.data == "REJ":
                    return
            rej_frame = Frame("RR", f_id, 1)
            self.__message_frames.append(rej_frame)
            self.print_to_gui(f"new RR message added to list\n")

    def __remove_error_frame(self, suspected_frame_id):
        for frame in self.__last_sent_messages:
            if frame.id == suspected_frame_id:
                self.__last_sent_messages.remove(frame)
                if frame.data == "REJ":
                    self.print_to_gui(f"REJ frame with id {suspected_frame_id}, corrected and removed form sending list\n")
                elif frame.data == "RR":
                    self.print_to_gui(f"RR frame with id {suspected_frame_id}, corrected and removed form sending list\n")

    def __add_window_to_buffer(self):
        for frame in self.__window:
            self.__buffer.append(frame)

    def __send_cycle(self):
        self.print_to_gui(f"t={self.get_connection_time()}|SendCycle::\n")
        if len(self.__message_frames) > 0:
            sending_message = self.__message_frames.pop(0)
            sending_message.set_sent_time(self.get_connection_time(type="i"))
            self.__last_sent_messages.append(sending_message)
            self.print_to_gui(f"Server trans: {sending_message.output()}\n")
            self.connection.send(sending_message.output().encode())
        else:
            self.print_to_gui("Server trans nothing\n")
            pass

    def __print_message_buffer(self):
        for frame in self.__message_frames:
            self.print_to_gui(frame.output())

    def __print_srej_buffer(self):
        for i in range(len(self.__srej_buffer)):
            self.print_to_gui(self.__srej_buffer[i].output())


# server = Server("192.168.100.2", 8080, 4, 8)
# server.listen("SELECTIVE")
