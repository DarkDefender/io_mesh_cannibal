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
