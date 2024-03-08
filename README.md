# Description
This is a Python script designed for network security purposes, specifically for intrusion detection and prevention. It monitors incoming connections on specified ports, logs IP addresses, and can automatically ban suspicious IPs using firewalld.

# Features
- Monitors incoming connections on specified ports.
- Logs IP addresses of incoming connections along with timestamps.
- Automatically ban suspicious IPs using firewalld.
- Supports both IPv4 and IPv6 addresses.

*NOTICE: log will be saved to "/var/log/iptrap.log".*

# Usage
Run the script with the desired port numbers as command-line arguments. For example:
```bash
python3 iptrap.py 8081 8082
```
The script will start monitoring incoming connections on ports 8081 and 8082. Press `Ctrl + C` to stop the script and terminate the traps.

# Contributing
Contributions are welcome. If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

*P.S. I haven't learned Python so I can't offer you insights*

# License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
