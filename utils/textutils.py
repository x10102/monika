class JSONNull:
    ...

def print_application_number(number: int) -> str:
    if number == 0:
        return "Žádné nové žádosti"
    elif number == 1:
        return "1 nová žádost"
    elif number < 5:
        return f"{number} nové žádosti"
    else:
        return f"{number} nových žádostí"

def __single_string_to_type(s: str) -> str | int | bool | JSONNull:
    if s.isnumeric():
        return int(s)
    match s:
        case 'true':
            return True
        case 'false':
            return False
        case 'null':
            return JSONNull()
        case '\\true':
            return 'true'
        case '\\false':
            return 'false'
        case '\\null':
            return 'null'
        case _:
            return s

def string_to_json_type(s: str) -> str | int | bool | list[str] | list[int] | list[bool] | list[JSONNull] | None | JSONNull:
    if s.startswith('[') and s.endswith(']'):
        return s[1:-1]
    is_list = s.count(',') != 0
    if not is_list:
        return __single_string_to_type(s)
    values = s.split(',')
    to_return = []
    first = __single_string_to_type(values[0])
    first_type = type(first)
    for val in values:
        converted = __single_string_to_type(val)
        if type(converted) is not first_type:
            return None
        to_return.append(converted)
    # MyPy doesn't know we're checking that the types inside the list match
    return to_return # type: ignore
