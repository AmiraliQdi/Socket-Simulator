class Frame:

    def __init__(self, data, frame_id, p_data):
        self.data = data
        self.id = frame_id
        self.p = p_data

    def output(self):
        output_string = str(self.data) + "/" + str(self.id) + "/" + str(self.p)
        return output_string


def input_frame(data):
    try:
        data_list = data.split("/")
        frame = Frame(data_list[0], int(data_list[1]), int(data_list[2]))
    except:
        frame = Frame("NONE", -1, -1)
    return frame


def input_stream(big_data, sequence_number, starting_number):
    frame_list = []
    big_data_list = big_data.split(" ")
    counter = starting_number
    for data in big_data_list:
        frame = Frame(str(data), counter, 0)
        frame_list.append(frame)
        counter += 1
        if counter == sequence_number:
            counter = 0
    return frame_list