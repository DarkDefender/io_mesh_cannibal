from formats.frm import Frm
from formats.geo import Geo
from formats.lod import Lod
from formats.mac import Mac
from formats.seq import Seq
from formats.skl import Skl
from formats.srf import Srf

import sys

# Save a reference to the original standard output
original_stdout = sys.stdout

def is_primitive(data):
    primitive = (int, str, bool, float, bytes)
    return isinstance(data, primitive)

def compare_data(obj1, obj2, var_path):
    #print(var_path)

    if is_primitive(obj1):
        if not obj1 == obj2:
            print("Data value doesn't match for " + var_path)
            print("Expected: " + str(obj1) + " Got: " + str(obj2))
            raise ValueError
        return

    # Get all callable (and non internal) variables
    var_list1 = [var for var in dir(obj1) if not var.startswith("_") and not callable(getattr(obj1, var))]
    var_list2 = [var for var in dir(obj2) if not var.startswith("_") and not callable(getattr(obj2, var))]

    # Make sure that both objects have the same set of keys
    if (var_list1 != var_list2):
        print("Variable list is not the same for: " + var_path)
        print("The following variables were not shared:")
        print(str(set(var_list1) ^ set(var_list2)))
        raise ValueError

    # Loop over all variable names
    for i in range(len(var_list1)):
        name = var_list1[i]
        data1 = getattr(obj1, name)
        data2 = getattr(obj2, name)
        if type(data1) != type(data2):
            print("Data type doesn't match for '" + name + "' in " + var_path)
            raise ValueError
        if type(data1) is list:
            if len(data1) != len(data2):
                print("Data list length doesn't match for '" + name + "' in " + var_path)
                print("Expected: " + len(data1) + " Got: " + len(data2))
                raise ValueError
            for list_idx in range(len(data1)):
                compare_data(data1[list_idx], data2[list_idx], var_path + "/" + name)
        else:
            if "offset" in name:
                # Don't compare offset variables.
                # We are usually more interested to see if the actual parsed data matches
                continue
            if "time_stamp" == name:
                # We don't either usually care if the write timestamp has changed either
                continue
            # Dive deeper into the data structure
            compare_data(data1, data2, var_path + "/" + name)

def print_data(obj1, var_path):
    #print(var_path)

    if is_primitive(obj1):
        print(var_path + ": " + str(obj1))
        return

    # Get all callable (and non internal) variables
    var_list1 = [var for var in dir(obj1) if not var.startswith("_") and not callable(getattr(obj1, var))]

    # Loop over all variable names
    for i in range(len(var_list1)):
        name = var_list1[i]
        data1 = getattr(obj1, name)
        if type(data1) is list:
            for list_idx in range(len(data1)):
                print_data(data1[list_idx], var_path + "/" + name)
        else:
            if "offset" in name:
                # Don't print offset variables.
                # We are usually more interested to see if the actual parsed data matches
                continue
            if "time_stamp" == name:
                # We don't either usually care if the write timestamp has changed either
                continue
            # Dive deeper into the data structure
            print_data(data1, var_path + "/" + name)

def parse_data(key, data1, data2):
    if key == 'FRMB':
        frm1 = Frm.from_bytes(data1)
        frm2 = Frm.from_bytes(data2)
        return frm1, frm2
    if key == 'GEOB':
        geo1 = Geo.from_bytes(data1)
        geo2 = Geo.from_bytes(data2)
        return geo1, geo2
    if key == 'LODB':
        lod1 = Lod.from_bytes(data1)
        lod2 = Lod.from_bytes(data2)
        return lod1, lod2
    if key == 'MACB':
        mac1 = Mac.from_bytes(data1)
        mac2 = Mac.from_bytes(data2)
        return mac1, mac2
    if key == 'SEQB':
        seq1 = Seq.from_bytes(data1)
        seq2 = Seq.from_bytes(data2)
        return seq1, seq2
    if key == 'SKLB':
        skl1 = Skl.from_bytes(data1)
        skl2 = Skl.from_bytes(data2)
        return skl1, skl2
    if key == 'SRFB':
        srf1 = Srf.from_bytes(data1)
        srf2 = Srf.from_bytes(data2)
        return srf1, srf2
    raise ValueError("Unknown format loaded")

def compare_cpj_data(cpj_data1, cpj_data2):
    if cpj_data1.keys() != cpj_data2.keys():
        raise ValueError("The cpj files do not contain the same data chunk types!")

    for key in cpj_data1:
        list1 = cpj_data1[key]
        list2 = cpj_data2[key]

        if len(list1) != len(list2):
            raise ValueError("The cpj files do not contain the same amount of chunks of type: " + str(key))
        for i in range(len(list1)):
            print("Comparing " + str(key) + "_" + str(i))
            p_data1, p_data2 = parse_data(key, list1[i], list2[i])
            try:
                compare_data(p_data1, p_data2, "")
            except ValueError:
                print("The two entries differ, printing out the data to /tmp/obj1-2")
                with open('/tmp/obj1', 'w') as f:
                    sys.stdout = f
                    print_data(p_data1, "")
                with open('/tmp/obj2', 'w') as f:
                    sys.stdout = f
                    print_data(p_data2, "")
                sys.stdout = original_stdout
