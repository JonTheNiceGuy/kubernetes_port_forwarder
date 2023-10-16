import os
import sys
import json
import subprocess
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QComboBox, QLineEdit, QLabel, QTextBrowser

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config_path = os.path.expanduser("~/.config/kubernetes_port_forwarder/config.json")
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

        # Create widgets
        self.output_text = QTextBrowser(self)
        self.output_text.setOpenExternalLinks(True)
        self.output_text.setReadOnly(True)
        self.label1 = QLabel("Context", self)
        self.context_combobox = QComboBox(self)
        self.update_context_combobox()
        self.label2 = QLabel("Service", self)
        self.service_combobox = QComboBox(self)
        for service in self.services.keys():
            self.service_combobox.addItems([service])
        self.label3 = QLabel("Bound IP", self)
        self.bind_address = QLineEdit(self)
        self.bind_address.setText("127.0.0.1")
        self.label4 = QLabel("State", self)
        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self.toggle_connection)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label1)
        layout.addWidget(self.context_combobox)
        layout.addWidget(self.label2)
        layout.addWidget(self.service_combobox)
        layout.addWidget(self.label3)
        layout.addWidget(self.bind_address)
        layout.addWidget(self.label4)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.output_text)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.process = None
        self.connected = False

    def toggle_connection(self):
        if not self.connected and not self.shutdown_received:
            # Start the shell command
            self.process = QProcess()

            # Connect the process's signals
            self.process.readyReadStandardOutput.connect(self.handle_stdout_and_stderr)
            self.process.readyReadStandardError.connect(self.handle_stdout_and_stderr)
            self.process.finished.connect(self.restart_process)
            
            service = self.services[self.service_combobox.currentText()]

            command = f"kubectl port-forward "
            command+= f"--context {self.context_combobox.currentText()} "
            if 'namespace' in service:
                command+= f"--namespace {service['namespace']} "
            if 'kind' in service:
                command+= f"{service['kind']}/"
            if 'object' in service:
                command+= f"{service['object']} "
            else:
                command+= f"{self.service_combobox.currentText()} "
            command+= f"--address {self.bind_address.text()} {service['port']}"
            if 'serviceport' in service:
                command+= f":{service['serviceport']}"

            self.log_output("Starting process", 'black')
            self.process.start(command)

            self.connected = True
            self.connect_button.setText("Disconnect")
        else:
            # Stop the shell command
            self.connected = False
            self.log_output("Killing process", 'black')
            self.process.kill()
            self.log_output("Waiting for process to die", 'black')
            self.process.waitForFinished()
            self.log_output("Process Dead", 'black')
            self.connect_button.setText("Connect")

    def restart_process(self, exitCode, exitStatus):
        if self.connected and not self.shutdown_received:
            # If the process terminated and we are still connected, restart it
            self.log_output("Restart process received", 'black')
            self.log_output(f"Previous RC {str(exitCode)}", 'black')
            self.log_output(f"Previous Message {str(exitStatus)}", 'black')
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

    def log_output(self, message, color = 'black'):
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
            # Run 'kubectl config get-contexts --no-headers' and capture its output
            output = subprocess.check_output(['kubectl', 'config', 'get-contexts', '--no-headers'], universal_newlines=True)
            
            context_names = []

            # Split the output by lines and extract the first column (context names)
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

            index = 0
            active_item = 0
            for item in context_names:
                if item == active_context:
                    active_item = index
                index+=1
            
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
