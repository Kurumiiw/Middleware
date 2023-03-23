import configparser
import os
import sys
import subprocess


def error_print(msg: str):
    print("\033[91m\033[4m" + msg + "\033[0m")


def main():
    if os.geteuid() != 0:
        error_print("This script must be run with sudo")
        sys.exit(1)

    try:
        result = subprocess.run(["modprobe", "tcp_vegas"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except:
        error_print("Failed to load the kernel module for tcp vegas.")
        print("Reason:", result.stderr)
        print("Exiting.")
        sys.exit(1)

    try:
        subprocess.run(["sysctl", "-w", "net.ipv4.tcp_congestion_control=vegas"], capture_output=True, check=True)
        subprocess.run(["sysctl", "-w", "net.ipv4.tcp_congestion_control=reno"], capture_output=True, check=True)
        subprocess.run(["sysctl", "-w", "net.ipv4.tcp_available_congestion_control=\"reno cubic vegas\""], capture_output=True, check=True)
        subprocess.run(["sysctl", "-w", "net.ipv4.tcp_allowed_congestion_control=\"reno cubic vegas\""], capture_output=True, check=True)
    except:
        error_print("Failed to force load tcp vegas. Exiting.")
        sys.exit(1)

    conf_reader = configparser.ConfigParser()
    conf_reader.read(os.path.join(os.path.dirname(__file__), "system_config.ini"))

    sys_conf_section_name = "system_configuration"
    if conf_reader.sections() != [sys_conf_section_name]:
        error_print(
            'Illegal system config sections. The only allowed section is "system_configuration"'
        )
        sys.exit(1)

    for option in conf_reader.options(sys_conf_section_name):
        option_values = conf_reader.get(sys_conf_section_name, option)
        try:
            result = subprocess.run(
                ["sysctl", "-w", 'net.ipv4.{}={}'.format(option, option_values)],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as err:
            error_print(
                "Failed to set the system config option net.ipv4.{}. Exiting.".format(
                    option
                )
            )
            sys.exit(1)

        try:
            result = subprocess.run(
                ["sysctl", "net.ipv4.{}".format(option)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as err:
            error_print(
                "Failed to query system config net.ipv4.{}. Cannot verify option has been set correctly. Exiting.".format(
                    option
                )
            )
            sys.exit(1)

        result_string = str(result.stdout)
        values_string = result_string.split("=")[1].removesuffix("\\n'").strip()

        if set(values_string.split(" ")) != set(option_values.split(" ")):
            error_print(
                "Failed to set the system config option net.ipv4.{}. Queried value does not equal set value. Exiting.".format(
                    option
                )
            )
            sys.exit(1)
        else:
            print("net.ipv4.{}={}".format(option, values_string))

    print("\033[92mSystem configuration done successfully\033[0m")


if __name__ == "__main__":
    main()
