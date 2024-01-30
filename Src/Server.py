import socket


class Server:

    def __init__(self, ip_address, port, connection_type=socket.AF_INET, protocol_type=socket.SOCK_STREAM):
        self.__initialize_socket(connection_type, protocol_type, ip_address, port)
        self.connection, self.client_ip_address = None, None

    def __initialize_socket(self, connection_type, protocol_type, server_ip, server_port):
        s = socket.socket(connection_type, protocol_type)
        s.bind((server_ip, server_port))
        self.socket = s

    def start_listening(self):
        self.socket.listen()
        self.connection, self.client_ip_address = self.socket.accept()
