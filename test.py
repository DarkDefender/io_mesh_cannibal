from cpj_utils import *

from formats.mac import Mac
from formats.srf import Srf
import struct

from compare_data import compare_data

file_data1 = load_cpj_data("/tmp/ASHTRAY1.cpj")
file_data2 = load_cpj_data("/tmp/smokealarm.cpj")

#geo_data1 = Geo.from_bytes(file_data1["GEOB"][0])
#geo_data2 = Geo.from_bytes(file_data2["GEOB"][0])

#compare_data(geo_data1, geo_data2, "geo")

mac_data1 = Mac.from_bytes(file_data1["MACB"][0])
#mac_data2 = Mac.from_bytes(file_data2["MACB"][0])

#compare_data(mac_data1, mac_data2, "mac")

srf_data = Srf.from_bytes(file_data1["SRFB"][0])

for com in mac_data1.data_block.commands:
    print(com.command_str)
