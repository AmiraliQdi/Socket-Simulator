import random

CORRUPTION_RATE = 0.1


class Frame:

    def __init__(self, data, frame_id, p_data):
        self.data = data
        self.id = frame_id
        self.p = p_data
        self.timeout = None

    def output(self):
        output_id = str(self.id)
        random_number = random.random()
        if random_number < CORRUPTION_RATE and self.p == 0:
            output_id = str(-1)
        output_string = f"{str(self.data)}/{output_id}/{str(self.p)}"
        return output_string

    def set_sent_time(self, sent_time):
        if self.timeout is not None:
            print(f"Resending (TIMED OUT) |{self.data}/{self.id}")
            self.timeout.reset(sent_time)
        self.timeout = Timeout(sent_time)



class Timeout:

    def __init__(self, sent_time, timeout=2.0):
        self.sent_time = sent_time
        self.timeout = timeout

    def reset(self, current_time):
        self.sent_time = current_time

    def is_timed_out(self, current_time):
        return current_time - self.sent_time > 2.0


def input_frame(data):
    try:
        data_list = data.split("/")
        frame = Frame(data_list[0], int(data_list[1]), int(data_list[2]))
    except:
        frame = Frame("NONE", -1, -1)
    return frame


def empty_packets(count):
    frame_list = []
    for i in range(count):
        frame = Frame("EMPTY", -1, -1)


def input_stream(big_data, sequence_number, starting_number):
    frame_list = []
    big_data_list = big_data.split(" ")
    counter = starting_number
    for data in big_data_list:
        if counter == sequence_number:
            counter = 0
        frame = Frame(str(data), counter, 0)
        frame_list.append(frame)
        counter += 1

    return frame_list


def output_stream(frame_list):
    stream = ""
    enter_counter = 0
    for frame in frame_list:
        stream += frame.data + " "
        if enter_counter == 10:
            stream += f"\n"
            enter_counter = 0
        enter_counter += 1
    return stream
