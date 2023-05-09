import customtkinter as ctk
import threading
import serial
import webbrowser
import sys
from serial.tools import list_ports


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
stop_threads = False


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        # configure window
        self.title("SeriaTerm")
        self.geometry(f"{1200}x{600}")
        # configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # default com init values
        self.baudrate = 9600
        self.bytesize = 8
        self.parity   = "N"
        self.stopbits = 1

        ### LEFT SIDEBAR
        # create sidebar frame
        self.sidebar_left = ctk.CTkFrame(self, width=140)
        self.sidebar_left.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_left.grid_rowconfigure(4, weight=1)
        # application name label
        self.logo_label = ctk.CTkLabel(self.sidebar_left, text="SeriaTerm", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        # connect button
        self.sideleft_button_connect = ctk.CTkButton(self.sidebar_left, text="Connect", command=self.event_connect)
        self.sideleft_button_connect.grid(row=1, column=0, padx=20, pady=20)
        # scan button
        self.sideleft_button_scan = ctk.CTkButton(self.sidebar_left, text="Scan", command=self.event_scan)
        self.sideleft_button_scan.grid(row=2, column=0, padx=20, pady=20)
        # clear button
        self.button_clear = ctk.CTkButton(master=self.sidebar_left, text="Clear", command=self.clear_callback)
        self.button_clear.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")
        # log box
        self.logbox = ctk.CTkTextbox(self.sidebar_left, width=20, height=100)
        self.logbox.grid(row=5, column=0, padx=20, pady=(30, 10), sticky="nsew")
        self.logbox.configure(state=ctk.DISABLED)

        ### CENTRAL MAIN
        # textbox
        self.textbox = ctk.CTkTextbox(self, width=500, height=400)
        self.textbox.grid(row=0, column=1, columnspan=3, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.textbox.configure(state=ctk.DISABLED)
        # read bar
        self.read_bar = ctk.CTkProgressBar(self)
        self.read_bar.grid(row=1, column=1, padx=(20, 10), pady=(10, 10), sticky="ew")
        self.read_bar.configure(mode="indeterminnate")
        self.read_bar.start()
        self.stop_bar()
        # read button
        self.main_button_read = ctk.CTkButton(master=self, text="Read", command=self.event_read)
        self.main_button_read.grid(row=1, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")
        # input entry
        self.input = ctk.StringVar(self)
        self.entry = ctk.CTkEntry(self, placeholder_text="", textvariable=self.input)
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")
        # write button
        self.main_button_write = ctk.CTkButton(master=self, text="Write", command=self.write_callback)
        self.main_button_write.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

        ### RIGHT SIDEBAR
        # sidebar
        self.sidebar_right = ctk.CTkTabview(self, width=140)
        self.sidebar_right.grid(row=0, column=4, rowspan=4, sticky="nsew")
        self.sidebar_right.add("COM")
        self.sidebar_right.add("UI")
        self.sidebar_right.add("info")
        ## COM TAB
        # comport
        self.label_comport = ctk.CTkLabel(self.sidebar_right.tab("COM"), text="COM Port")
        self.label_comport.grid(row=0, column=0, padx=20, pady=(10, 0))
        self.optionmenu_comport = ctk.CTkOptionMenu(self.sidebar_right.tab("COM"), dynamic_resizing=False, values=[], command=self.comport_callback)
        self.optionmenu_comport.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.optionmenu_comport.set("select")
        self.event_scan()
        # baudrate
        self.label_baudrate = ctk.CTkLabel(self.sidebar_right.tab("COM"), text="Baud Rate")
        self.label_baudrate.grid(row=2, column=0, padx=20, pady=(10, 0))
        self.optionmenu_baudrate = ctk.CTkOptionMenu(self.sidebar_right.tab("COM"),
            values=[
                #"custom",
                "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "28800", "38400", "56000", "57600", "115200", "128000", "256000"],
            command=self.baudrate_callback
            )
        self.optionmenu_baudrate.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.optionmenu_baudrate.set("9600")
        # bytesize
        self.label_bytesize = ctk.CTkLabel(self.sidebar_right.tab("COM"), text="Byte Size")
        self.label_bytesize.grid(row=4, column=0, padx=20, pady=(10, 0))
        self.optionmenu_bytesize = ctk.CTkOptionMenu(self.sidebar_right.tab("COM"), values=["5", "6", "7", "8"], command=self.bytesize_callback)
        self.optionmenu_bytesize.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.optionmenu_bytesize.set("8")
        # parity
        self.label_parity = ctk.CTkLabel(self.sidebar_right.tab("COM"), text="Parity")
        self.label_parity.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.optionmenu_parity = ctk.CTkOptionMenu(self.sidebar_right.tab("COM"), values=["none", "odd", "even", "mark", "space"], command=self.parity_callback)
        self.optionmenu_parity.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.optionmenu_parity.set("none")
        # stopbits
        self.label_stopbits = ctk.CTkLabel(self.sidebar_right.tab("COM"), text="Stop Bits")
        self.label_stopbits.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.optionmenu_stopbits = ctk.CTkOptionMenu(self.sidebar_right.tab("COM"), values=["1", "1.5", "2"], command=self.stopbits_callback)
        self.optionmenu_stopbits.grid(row=9, column=0, padx=20, pady=(10, 0))
        self.optionmenu_stopbits.set("1")
        ## UI TAB
        # appearence
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_right.tab("UI"), text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_right.tab("UI"), values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.appearance_mode_optionemenu.set("System")
        # scaling
        self.scaling_label = ctk.CTkLabel(self.sidebar_right.tab("UI"), text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_right.tab("UI"), values=["80%", "90%", "100%", "110%", "120%"], command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        self.scaling_optionemenu.set("100%")
        ## INFO TAB
        # contribute
        self.contribute_label = ctk.CTkLabel(self.sidebar_right.tab("info"), text="Contribute!", anchor="w")
        self.contribute_label.grid(row=0, column=0, padx=20, pady=(10, 0))
        self.contribute_button = ctk.CTkButton(self.sidebar_right.tab("info"), text="GitHub", command=self.contribute_callback)
        self.contribute_button.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")


    def open_input_dialog_event(self):
        dialog = ctk.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())


    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.stop_bar()


    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)


    def comport_callback(self, value):
        self.comport = value.split('-')[0].strip()


    def baudrate_callback(self, value):
        self.baudrate = int(value)


    def bytesize_callback(self, value):
        self.bytesize = int(value)


    def parity_callback(self, value):
        match value:
            case "none":
                self.parity = 'N'
            case "odd":
                self.parity = 'O'
            case "even":
                self.parity = 'E'
            case "mark":
                self.parity = 'M'
            case "space":
                self.parity = 'F'


    def stopbits_callback(self, value):
        self.stopbits = int(value)


    def write_callback(self):
        self.serial_write()


    def clear_callback(self):
        self.input.set("")


    def event_connect(self):
        if self.sideleft_button_connect._text == "Connect":
            self.connection = serial.Serial(
                port=self.comport,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits
            )
            self.sideleft_button_connect.configure(text="Disconnect")
        elif self.sideleft_button_connect._text == "Disconnect":
            self.connection.close()
            self.sideleft_button_connect.configure(text="Connect")


    def serial_read(self):
        while True:
            global stop_threads
            if stop_threads:
                break
            if self.stop_reading_thread:
                break
            buffer = self.connection.read(self.connection.in_waiting).decode()
            self.textbox.insert("0.0", buffer)


    def serial_write(self):
        self.connection.write(bytes(self.input.get(), "utf-8"))


    def start_bar(self):
        if ctk.get_appearance_mode() == "Dark":
            self.read_bar.configure(progress_color="#1F6AA5") # blue on black theme
        elif ctk.get_appearance_mode() == "Light":
            self.read_bar.configure(progress_color="#3B8ED0") # blue on light theme


    def stop_bar(self):
        if ctk.get_appearance_mode() == "Dark":
            self.read_bar.configure(progress_color="#4A4D50") # gray on dark theme
        elif ctk.get_appearance_mode() == "Light":
            self.read_bar.configure(progress_color="#939BA2") # gray on light theme


    def event_read(self):
        if self.main_button_read._text == "Read":
            if self.connection:
                self.start_bar()
                self.main_button_read.configure(text="Stop")
                self.stop_reading_thread = False
                self.reading_thread = threading.Thread(target=self.serial_read)
                self.reading_thread.start()
        elif self.main_button_read._text == "Stop":
            self.stop_bar()
            self.main_button_read.configure(text="Read")
            self.stop_reading_thread = True


    def event_scan(self):
        self.ports = {x.device: x.description for x in sorted(list_ports.comports())}
        self.optionmenu_comport.configure(values=[f"{e[0]} - {e[1]}" for e in self.ports.items()])


    def contribute_callback(self):
        webbrowser.open("https://github.com/voidpunk/seriaterm")



def on_closing():
    global stop_threads
    stop_threads = True
    sys.exit()




if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()