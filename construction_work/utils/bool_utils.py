def string_to_bool(data) -> bool:
    if str(data).lower() in ["true", "1", "yes", "on"]:
        return True
    elif str(data).lower() in ["false", "0", "no", "off", "none", "null"]:
        return False
    else:
        raise ValueError("String could not be translated to boolean")
