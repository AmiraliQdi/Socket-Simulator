import sys
import tkinter as tk
from tkinter import ttk, simpledialog
from tkinter import scrolledtext
from threading import Thread

from Src.Client import Client
from Src.Server import Server


class SimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Selective Repeat / Go-Back-N Simulation")

        # Set fixed window size
        self.root.geometry("800x350")

        self.label_connection = ttk.Label(root, text="Select Server or Client:")
        self.label_connection.grid(row=0, column=0, columnspan=2, pady=10)

        self.connection_var = tk.StringVar(value="Server")
        self.connection_combobox = ttk.Combobox(root, textvariable=self.connection_var, values=["Server", "Client"])
        self.connection_combobox.grid(row=1, column=0, columnspan=2, pady=5)

        self.label_connection_type = ttk.Label(root, text="Select Connection Type:")
        self.label_connection_type.grid(row=2, column=0, columnspan=2, pady=10)

        self.connection_type_var = tk.StringVar(value="Selective")
        self.connection_type_combobox = ttk.Combobox(root, textvariable=self.connection_type_var,
                                                     values=["Selective", "Go-Back"])
        self.connection_type_combobox.grid(row=3, column=0, columnspan=2, pady=5)

        self.label_ip = ttk.Label(root, text="Enter IP Address:")
        self.label_ip.grid(row=4, column=0, pady=10)

        self.ip_entry = ttk.Entry(root)
        self.ip_entry.grid(row=4, column=1, pady=10)

        self.label_port = ttk.Label(root, text="Enter Port Number:")
        self.label_port.grid(row=5, column=0, pady=10)

        self.port_entry = ttk.Entry(root)
        self.port_entry.grid(row=5, column=1, pady=10)

        self.start_button = ttk.Button(root, text="Start Simulation", command=self.start_simulation)
        self.start_button.grid(row=6, column=0, columnspan=2, pady=20)

        # Text widget for displaying log messages
        self.log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=65, height=20)
        self.log_text.grid(row=0, column=3, rowspan=7, padx=20)

    def start_simulation(self):
        connection_type = self.connection_type_var.get()
        ip_address = self.ip_entry.get()
        port = int(self.port_entry.get())

        if self.connection_var.get() == "Server":
            print("START")
            server_thread = Thread(target=self.start_server, args=(ip_address, port, connection_type))
            server_thread.start()
        elif self.connection_var.get() == "Client":
            client_thread = Thread(target=self.start_client, args=(ip_address, port, connection_type))
            client_thread.start()

    def start_server(self, ip_address, port, connection_type):
        # Redirect stdout to the Text widget
        sys.stdout = TextRedirector(self.log_text, "stdout")
        print(f"Starting server with IP: {ip_address}, Port: {port}, Connection Type: {connection_type}")

        server = Server(str(ip_address), int(port), 4, 8)
        server.listen(connection_type)

    def start_client(self, ip_address, port, connection_type):
        # Redirect stdout to the Text widget
        sys.stdout = TextRedirector(self.log_text, "stdout")
        print(f"Starting client with IP: {ip_address}, Port: {port}, Connection Type: {connection_type}")

        client = Client(4, 8,self)
        client.connect(str(ip_address), int(port))
        client.send_data(
            "In a bustling city, a hidden cafe exudes warmth with the scent of freshly brewed coffee and soft jazz."
            " Patrons immersed in creativity, sunlight filtering through curtains, "
            "and a meticulous barista crafting indulgent moments. "
            "A quiet oasis where time slows amid aromatic swirls and hushed conversations.")
        client.send_data("NONE")
        client.start(connection_type)

class TextRedirector:
    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, str):
        self.text_widget.insert(tk.END, str, (self.tag,))
        self.text_widget.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()
