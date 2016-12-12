

def json_traverse(obj, func):
    """
    Traverse a parsed json string and execute
    a function on all key-value pairs
    :param obj: The output of json.parse
    :param func: return True to traverse the processed value
    """
    if type(obj) is list:
        for elt in obj:
            json_traverse(elt, func)
    elif type(obj) is dict:
        for key, value in obj.iteritems():
            if func(obj, key, value):
                json_traverse(value, func)
    else:
        pass
