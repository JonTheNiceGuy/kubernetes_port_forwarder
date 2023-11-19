# Kubernetes Port Forwarder

This tool is [licensed under an MIT-based License](https://raw.githubusercontent.com/JonTheNiceGuy/kubernetes_port_forwarder/main/LICENSE).

## About the tool

This simple tool uses your existing Kubernetes configuration file to establish
port-forward connections to the services and deployments in your cluster.

## Setup

Download the [python script](https://raw.githubusercontent.com/JonTheNiceGuy/kubernetes_port_forwarder/main/kubernetes_port_forwarder.py)
and mark it as executable. Create a configuration file in
`~/.config/kubernetes_port_forwarder/config.json`, an example config file is
[provided here](https://raw.githubusercontent.com/JonTheNiceGuy/kubernetes_port_forwarder/main/example_config.json).

## Why it was created?

I was inspired by [Kube Forwarder](https://kube-forwarder.pixelpoint.io/),
however, this tool currently doesn't support wayland. I also wanted to become
more proficient at Python, and wanted to learn how to write a QT based
application. It's far from perfect! If you've got experience of writing an
application like this, please feel free to [get in touch](mailto:jon@sprig.gs)
or raise [issues](https://github.com/JonTheNiceGuy/kubernetes_port_forwarder/issues)
and [pull requests](https://github.com/JonTheNiceGuy/kubernetes_port_forwarder/pulls)
to fix any issues you want to see resolved.

## Security

This application isn't considered to be secure or even production ready.
However, if you find an issue which warrants an urgent response, please do
[contact me directly](mailto:jon@sprig.gs?subject=Kubernetes%20Port%20Forwarder%20-%20Security%20issue%20identified).
