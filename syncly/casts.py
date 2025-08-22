def cast_bool(value):
    """
    Converts a string value to a boolean. Returns True if the string is 'true' (case-insensitive), otherwise False.
    """
    return value.lower() == 'true'
