from formats.frm import Frm
from formats.geo import Geo
from formats.lod import Lod
from formats.mac import Mac
from formats.seq import Seq
from formats.skl import Skl
from formats.srf import Srf

def is_primitive(data):
    primitive = (int, str, bool, float, bytes)
    return isinstance(data, primitive)

def compare_data(obj1, obj2, var_path):
    print(var_path)

    if is_primitive(obj1):
        if not obj1 == obj2:
            print("Data value doesn't match for " + var_path)
            print("Expected: " + str(obj1) + " Got: " + str(obj2))
            raise ValueError
        return

    # Get all callable (and non internal) variables
    var_list1 = [var for var in vars(obj1) if not var.startswith("_")]
    var_list2 = [var for var in vars(obj2) if not var.startswith("_")]

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
            # Dive deeper into the data structure
            compare_data(data1, data2, var_path + "/" + name)

def parse_and_compare_data(key, data1, data2):
    if key == 'FRMB':
        frm1 = Frm.from_bytes(data1)
        frm2 = Frm.from_bytes(data2)
        compare_data(frm1, frm2, "")
        return
    if key == 'GEOB':
        geo1 = Geo.from_bytes(data1)
        geo2 = Geo.from_bytes(data2)
        compare_data(geo1, geo2, "")
        return
    if key == 'LODB':
        lod1 = Lod.from_bytes(data1)
        lod2 = Lod.from_bytes(data2)
        compare_data(lod1, lod2, "")
        return
    if key == 'MACB':
        mac1 = Mac.from_bytes(data1)
        mac2 = Mac.from_bytes(data2)
        compare_data(mac1, mac2, "")
        return
    if key == 'SEQB':
        seq1 = Seq.from_bytes(data1)
        seq2 = Seq.from_bytes(data2)
        compare_data(seq1, seq2, "")
        return
    if key == 'SKLB':
        skl1 = Skl.from_bytes(data1)
        skl2 = Skl.from_bytes(data2)
        compare_data(skl1, skl2, "")
        return
    if key == 'SRFB':
        srf1 = Srf.from_bytes(data1)
        srf2 = Srf.from_bytes(data2)
        compare_data(srf1, srf2, "")
        return
    print("Unknown format loaded")
    raise ValueError

def compare_cpj_data(cpj_data1, cpj_data2):
    if cpj_data1.keys() != cpj_data2.keys():
        print("The cpj files do not contain the same data chunk types!")
        raise ValueError

    for key in cpj_data1:
        list1 = cpj_data1[key]
        list2 = cpj_data2[key]

        if len(list1) != len(list2):
            print("The cpj files do not contain the same amount of chunks of type: " + str(key))
            raise ValueError
        for i in range(len(list1)):
            print("Comparing " + str(key) + "_" + str(i))
            parse_and_compare_data(key, list1[i], list2[i])
