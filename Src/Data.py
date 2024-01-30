class Frame:

    def __init__(self, data, frame_id, p_data):
        self.data = data
        self.id = frame_id
        self.p = p_data

    def output(self):
        output_string = str(self.data) + "/" + str(self.id) + "/" + str(self.p)
        return output_string


def make_frame(data):
    data_list = data.split("/")
    frame = Frame(data_list[0], data_list[1], data_list[2])
    return frame


class Window:

    def __init__(self, window_size):
        self.buffer = []
        self.window_size = window_size

    def fill_window(self, frame_list):
        if len(frame_list) != self.window_size:
            raise Exception("Window size does not match frame list")
        else:
            self.__index_frames(frame_list)

    def __index_frames(self, frame_list):
        counter = 0
        for frame in frame_list:
            frame.id = counter
            counter += 1
            self.buffer.append(frame)

