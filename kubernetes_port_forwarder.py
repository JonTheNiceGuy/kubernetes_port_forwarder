import os
import sys
import json
import subprocess
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QLineEdit, QLabel, QTextBrowser, QHBoxLayout, QAction, QTabWidget


class ForwarderTab(QWidget):
    def __init__(self, parent, services):
        super().__init__(parent)
        self.services = services
        self.connected = False
        self.process = None
        self.shutdown_received = False
        self.debug = False

        self.init_ui()

    def set_index(self, tab_index: int):
        self.my_tab_index = tab_index

    def set_widget(self, widget: QTabWidget):
        self.my_tab_parent = widget

    def init_ui(self):
        self.context_label = QLabel("Context", self)
        self.context_combobox = QComboBox(self)
        self.update_context_combobox()

        self.service_label = QLabel("Service", self)
        self.service_combobox = QComboBox(self)
        for service in self.services.keys():
            self.service_combobox.addItems([service])

        self.bound_ip_label = QLabel("Bound IP", self)
        self.bind_address = QLineEdit(self)
        self.bind_address.setText("127.0.0.1")

        self.state_label = QLabel("State", self)
        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.toggle_connection)

        self.output_text = QTextBrowser(self)
        self.output_text.setOpenExternalLinks(True)
        self.output_text.setReadOnly(True)

        layout = QHBoxLayout()
        layout.addWidget(self.context_label)
        layout.addWidget(self.context_combobox)
        layout.addWidget(self.service_label)
        layout.addWidget(self.service_combobox)
        layout.addWidget(self.bound_ip_label)
        layout.addWidget(self.bind_address)
        layout.addWidget(self.state_label)
        layout.addWidget(self.connect_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(self.output_text)

        self.setLayout(main_layout)

    def set_tab_title(self, title: str):
        self.my_tab_parent.setTabText(self.my_tab_index, title)

    def toggle_connection(self):
        if not self.connected and not self.shutdown_received:
            # Start the shell command
            self.process = QProcess()

            # Connect the process's signals
            self.process.readyReadStandardOutput.connect(
                self.handle_stdout_and_stderr)
            self.process.readyReadStandardError.connect(
                self.handle_stdout_and_stderr)
            self.process.finished.connect(self.restart_process)

            service = self.services[self.service_combobox.currentText()]

            command = f"kubectl port-forward "
            command += f"--context {self.context_combobox.currentText()} "
            windowTitle = self.context_combobox.currentText()
            if 'namespace' in service:
                command += f"--namespace {service['namespace']} "
                windowTitle += f":{service['namespace']}"
            if 'kind' in service:
                command += f"{service['kind']}/"
            if 'object' in service:
                command += f"{service['object']} "
                windowTitle += f":{service['object']}"
            else:
                command += f"{self.service_combobox.currentText()} "
                windowTitle += f":{self.service_combobox.currentText()}"
            command += f"--address {self.bind_address.text()} {service['port']}"
            windowTitle += f":{service['port']}"
            if 'serviceport' in service:
                command += f":{service['serviceport']}"

            self.log_output("Starting process", 'black')
            self.log_output(
                f"Access service using nip.io via <a href='https://{self.service_combobox.currentText()}.{self.context_combobox.currentText()}.{self.bind_address.text()}.nip.io:{service['port']}'>HTTPS</a>, <a href='http://{self.service_combobox.currentText()}.{self.context_combobox.currentText()}.{self.bind_address.text()}.nip.io:{service['port']}'>HTTP</a>.")
            self.log_output(
                f"Access service using IP Only via <a href='https://{self.bind_address.text()}:{service['port']}'>HTTPS</a>, <a href='http://{self.bind_address.text()}:{service['port']}'>HTTP</a>.")
            self.log_output(
                f"Connect to {self.bind_address.text()}:{service['port']}")
            self.process.start(command)

            self.connected = True
            self.set_tab_title(windowTitle)
            self.connect_button.setText("Disconnect")
        else:
            # Stop the shell command
            self.connected = False
            self.log_debug_output("Killing process")
            self.process.kill()
            self.log_debug_output("Waiting for process to die")
            self.process.waitForFinished()
            self.log_output("Process stopped")
            self.set_tab_title("Available Forwarder")
            self.connect_button.setText("Connect")

    def restart_process(self, exitCode, exitStatus):
        if self.connected and not self.shutdown_received:
            # If the process terminated and we are still connected and not shutting down, restart it
            self.log_output("Restart process required")
            self.log_debug_output(f"Previous RC {str(exitCode)}")
            self.log_debug_output(f"Previous Message {str(exitStatus)}")
            self.connected = False
            self.toggle_connection()

    def handle_stdout_and_stderr(self):
        if self.process is not None and not self.shutdown_received:
            data_stdout = self.process.readAllStandardOutput()
            data_stderr = self.process.readAllStandardError()

            if data_stdout:
                self.log_output(data_stdout, "green")
            if data_stderr:
                self.log_output(data_stderr, "red")

    def log_debug_output(self, message):
        if self.debug:
            self.log_output(message, color='black')

    def log_output(self, message, color='black'):
        if type(message) != str:
            output = str(message, encoding="utf-8")
        else:
            output = message

        if color == "green":
            output = f'<span style="color: green;">{output}</span>'
        elif color == "red":
            output = f'<span style="color: red;">{output}</span>'
        else:
            output = f'<span style="color: black;">{output}</span>'

        self.output_text.append(output)

    def update_context_combobox(self):
        try:
            # Get the current list of contexts
            output = subprocess.check_output(
                ['kubectl', 'config', 'get-contexts', '--no-headers'], universal_newlines=True)
            context_names = []

            # Get the context names (either first column or second column if context is active)
            for line in output.split('\n'):
                line = line.strip()
                if line:
                    parts = line.split()
                    if parts[0].startswith('*'):
                        context_names.append(parts[1])
                        active_context = parts[1]
                    else:
                        context_names.append(parts[0])

            context_names = list(set(context_names))
            context_names.sort()

            index = 0
            active_item = 0
            for item in context_names:
                if item == active_context:
                    active_item = index
                index += 1

            self.context_combobox.clear()
            self.context_combobox.addItems(context_names)
            self.context_combobox.setCurrentIndex(active_item)

        except subprocess.CalledProcessError as e:
            # Handle any errors that occur when running the command
            print(f"Error: {e}")

    def closeEvent(self, event):
        if self.process is not None:
            self.shutdown_received = True
            if self.process.state() == QProcess.Running:
                self.process.kill()
                self.process.waitForFinished()
            self.process.close()  # Close the process to release resources
            self.process.deleteLater()  # Ensure that the process is properly destroyed
        event.accept()


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config_path = os.path.expanduser(
            "~/.config/kubernetes_port_forwarder/config.json")
        self.services = self.load_config()
        self.shutdown_received = False
        self.debug = False

        self.init_ui()

    def load_config(self):
        default_services = {}

        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                config = json.load(file)
        else:
            config = default_services

        return config

    def init_ui(self):
        self.setWindowTitle('Kubernetes Port Forwarder')

        # Create a menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')

        # Add an action to create a new forwarder tab
        new_forwarder_action = QAction('New Forwarder', self)
        new_forwarder_action.triggered.connect(self.create_forwarder_tab)
        file_menu.addAction(new_forwarder_action)

        # Create a tab widget to hold forwarder tabs
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # Create the initial forwarder tab
        self.create_forwarder_tab()

    def create_forwarder_tab(self):
        tab = ForwarderTab(self, self.services)
        index = self.tab_widget.addTab(tab, "Available Forwarder")
        tab.set_index(index)
        tab.set_widget(self.tab_widget)
        self.tab_widget.setCurrentIndex(index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
