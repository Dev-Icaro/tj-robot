def flatten(array):
    flat_list = []
    for item in array:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)

    return flat_list


def remove_duplicate(array):
    unique_values = []

    for item in array:
        if item not in unique_values:
            unique_values.append(item)

    return unique_values
