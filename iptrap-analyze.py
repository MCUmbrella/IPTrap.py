#!/usr/bin/python3

import os
import sys
import re
import pandas as pd
import matplotlib.pyplot as plt
import geoip2.database


# Configurable arguments
logDir: str = "/var/log"
dbDir: str = "."
flInteractive: bool = False
flNoGeo: bool = False  #TODO: implement this option

# File names
logName: str = "iptrap.log"
countryDbName: str = "GeoLite2-Country.mmdb"
cityDbName: str = "GeoLite2-City.mmdb"

# Lists to store the parsed data
dates = []
ips = []
protocols = []
ports = []
countries = []
cities = []

# Regex pattern to extract relevant information
pattern = re.compile(r"\[(?P<datetime>[^\]]+)\] \[(?P<protocol>ipv[46])\] Caught (?P<ip>[\d\.]+|[\da-f:]+) on port (?P<port>\d+)")

# Parse arguments from command line
#TODO: consider using argparse when the project is getting bigger
if len(sys.argv) > 1:
	for arg in sys.argv[1:]:
		if arg.startswith("--logdir="):
			logDir = arg[9:]
		elif arg.startswith("--dbdir="):
			dbDir = arg[8:]
		elif arg == "-i" or arg == "--interactive":
			flInteractive = True

# Load the log
if os.path.isdir(logDir) and os.access(logDir, os.R_OK):
	log_path: str = os.path.join(logDir, logName)
	print("Loading IPTrap log from", log_path)
	with open(log_path, "r") as file:
		rawData = file.readlines()
else:
	raise Exception("Invalid log directory: \"" + logDir + "\" (change the direcroty with \"--logdir=<directory>\")")

# Load MaxMind GeoIP2 database
if os.path.isdir(dbDir) and os.access(dbDir, os.R_OK):
	country_db_path: str = os.path.join(dbDir, countryDbName)
	city_db_path: str = os.path.join(dbDir, cityDbName)
	print("Loading MaxMind GeoIP2 country database from", country_db_path)
	countryReader = geoip2.database.Reader(country_db_path)
	print("Loading MaxMind GeoIP2 city database from", city_db_path)
	cityReader = geoip2.database.Reader(city_db_path)
else:
	raise Exception("Invalid database directory: \"" + dbDir + "\" (change the direcroty with \"--dbdir=<directory>\")")

print("Parsing")
for line in rawData:
	match = pattern.search(line)
	if match:
		datetime_str = match.group("datetime")
		date_str = datetime_str.split()[0]
		ip = match.group("ip")
		protocol = match.group("protocol")
		port = match.group("port")

		dates.append(date_str)
		ips.append(ip)
		protocols.append(protocol)
		ports.append(port)
		try:
			countries.append(countryReader.country(ip).country.name)
		except geoip2.errors.AddressNotFoundError:
			countries.append("Unknown")
		try:
			cities.append(cityReader.city(ip).city.name)
		except geoip2.errors.AddressNotFoundError:
			cities.append("Unknown")

# Create a DataFrame from the parsed data
print("Formatting")
data: pd.DataFrame = pd.DataFrame({"date": dates, "ip": ips, "protocol": protocols, "port": ports, "countries": countries, "cities": cities})
print("Deduplicating")
data.drop_duplicates(subset=["date", "ip"], inplace=True)


############################################################
# Display a line graph of the number of IPs blocked per day
############################################################
def chartIpBlocks() -> None:
	print("Displaying: number of IPs blocked per day")

	# Count the number of unique IPs blocked per day
	ip_counts_per_day = data.groupby("date").size()
	print(ip_counts_per_day)

	# Plot the line graph for the number of IPs blocked per day
	plt.figure(figsize=(16, 9))
	plt.plot(ip_counts_per_day.index, ip_counts_per_day.values, marker="o")
	plt.title("Number of Blocked IPs Per Day")
	plt.xlabel("Date")
	plt.ylabel("Number of Unique IPs")
	plt.xticks(rotation=30)
	plt.grid(True)
	plt.gca().xaxis.set_major_locator(plt.MaxNLocator(nbins=ip_counts_per_day.size // 7))
	plt.tight_layout()
	plt.show()


#########################################################
# Display a pie chart of the percentage of ports blocked
#########################################################
def chartPortBlocks() -> None:
	print("Displaying: percentage of ports blocked")

	# Count the number of unique IPs blocked by each port
	port_counts = data["port"].value_counts()
	print(port_counts)

	# Plot the pie chart for the percentage of IPs blocked by port
	plt.figure(figsize=(16, 9))
	plt.pie(port_counts, labels=port_counts.index, autopct="%1.3f%%", startangle=140)
	plt.title("Percentage of Blocked IPs by Port")
	plt.axis("equal")
	plt.show()


#################################################################
# Display a pie chart of the percentage of IPv4 and IPv6 blocked
#################################################################
def chartFamilyBlocks() -> None:
	print("Displaying: percentage of IPv4 and IPv6 blocked")

	# Count the number of unique IPv4 and IPv6 addresses
	protocol_counts = data["protocol"].value_counts()
	print(protocol_counts)

	# Plot the pie chart for the percentage of IPv4 and IPv6 blocked
	plt.figure(figsize=(16, 9))
	plt.pie(protocol_counts, labels=protocol_counts.index, autopct="%1.3f%%", startangle=140)
	plt.title("Percentage of IPv4 and IPv6 Blocked")
	plt.axis("equal")
	plt.show()


##################################################################
# Display a pie chart of the percentage of blocked IPs by country
##################################################################
def chartCountryBlocks() -> None:
	print("Displaying: percentage of blocked IPs by country")

	country_counts = data["countries"].value_counts()
	print(country_counts)

	plt.figure(figsize=(16, 9))
	plt.pie(country_counts, labels=country_counts.index, autopct="%1.3f%%", startangle=140)
	plt.title("Percentage of Blocked IPs by Country")
	plt.axis("equal")
	plt.show()


#####################
# Display all charts
#####################
def chartAll() -> None:
	chartIpBlocks()
	chartPortBlocks()
	chartFamilyBlocks()
	chartCountryBlocks()


if flInteractive:
	import readline # optional, will allow Up/Down/History in the console
	import code
	variables = globals().copy()
	variables.update(locals())
	shell = code.InteractiveConsole(variables)
	print("Done! All records stored in DataFrame object \"data\"")
	print("""Available functions:
	chartAll()
	chartIpBlocks()
	chartPortBlocks()
	chartFamilyBlocks()
	chartCountryBlocks()""")
	print("Press Ctrl+D or use \"exit()\" to exit")
	shell.interact()
else:
	print("For interactive operation, run the script with argument \"-i\"")
	chartAll()
	exit()
