from cpj_utils import *
from compare_data import *
from test_utils import *

file_data1 = load_cpj_data("../Database/MainAnimsData/AllBones/AllBones.cpj")
#file_data2 = load_cpj_data("/tmp/smokealarm.cpj")

frm_byte_data_list = []

if "FRMB" in file_data1:
    for frm in file_data1["FRMB"]:
        frm_data = Frm.from_bytes(frm)
        frm_byte_data_list.append(round_trip_frm_data(frm_data))

geo_byte_data_list = []

if "GEOB" in file_data1:
    for geo in file_data1["GEOB"]:
        geo_data = Geo.from_bytes(geo)
        geo_byte_data_list.append(round_trip_geo_data(geo_data))

lod_byte_data_list = []

if "LODB" in file_data1:
    for lod in file_data1["LODB"]:
        lod_data = Lod.from_bytes(lod)
        lod_byte_data_list.append(round_trip_lod_data(lod_data))

mac_byte_data_list = []

if "MACB" in file_data1:
    for mac in file_data1["MACB"]:
        mac_data = Mac.from_bytes(mac)
        mac_byte_data_list.append(round_trip_mac_data(mac_data))

seq_byte_data_list = []

if "SEQB" in file_data1:
    for seq in file_data1["SEQB"]:
        seq_data = Seq.from_bytes(seq)
        seq_byte_data_list.append(round_trip_seq_data(seq_data))

skl_byte_data_list = []

if "SKLB" in file_data1:
    for skl in file_data1["SKLB"]:
        skl_data = Skl.from_bytes(skl)
        skl_byte_data_list.append(round_trip_skl_data(skl_data))

srf_byte_data_list = []

if "SRFB" in file_data1:
    for srf in file_data1["SRFB"]:
        srf_data = Srf.from_bytes(srf)
        srf_byte_data_list.append(round_trip_srf_data(srf_data))

#parse_and_compare_data("SEQB", file_data1["SEQB"][0], seq_byte_data)
byte_array_list = []

byte_array_list += frm_byte_data_list
byte_array_list += geo_byte_data_list
byte_array_list += lod_byte_data_list
byte_array_list += mac_byte_data_list
byte_array_list += seq_byte_data_list
byte_array_list += skl_byte_data_list
byte_array_list += srf_byte_data_list

# Finally write the cpj file to disk
write_cpj_file("/tmp/out.cpj", byte_array_list)
#
file_data2 = load_cpj_data("/tmp/out.cpj")

compare_cpj_data(file_data1, file_data2)
