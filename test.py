from cpj_utils import *

from formats.mac import Mac
from formats.srf import Srf

from compare_data import *

file_data1 = load_cpj_data("/tmp/ASHTRAY1.cpj")
#file_data2 = load_cpj_data("/tmp/smokealarm.cpj")

#geo_data1 = Geo.from_bytes(file_data1["GEOB"][0])
#geo_data2 = Geo.from_bytes(file_data2["GEOB"][0])

#compare_data(geo_data1, geo_data2, "geo")

#mac_data1 = Mac.from_bytes(file_data1["MACB"][0])
#mac_data2 = Mac.from_bytes(file_data2["MACB"][0])

#compare_data(mac_data1, mac_data2, "mac")

#srf_data = Srf.from_bytes(file_data1["SRFB"][0])

#for com in mac_data1.data_block.commands:
#    print(com.command_str)

byte_array_list = []

for key in file_data1:
    for byte_array in file_data1[key]:
        byte_array_list.append(byte_array)

write_cpj_file("/tmp/out.cpj", byte_array_list)

file_data2 = load_cpj_data("/tmp/out.cpj")

compare_cpj_data(file_data1, file_data2)
