# Python's NoneType serializes to a JSON null, but we want to use a return of None as an indicator of failure
# So we just create an empty type to represent a JSON null and replace it with None before serializing in the caller
# (rUsT wOuLd sOlVe ThIs BtW)
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
    # Escape null/true/false with a backslash
    # If I ever need to type '\null' into the config then what am I even doing
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
    # Square brackets work as string escape, will return the exact string without the brackets
    if s.startswith('[') and s.endswith(']'):
        return s[1:-1]

    # If we have only a single value, pass it to the conversion function and return that
    is_list = s.count(',') != 0
    if not is_list:
        return __single_string_to_type(s)

    # Split a comma-separated list
    values = s.split(',')
    to_return = []

    # Save the type of the first value
    first = __single_string_to_type(values[0])
    first_type = type(first)

    # Convert the following values and check that the types match
    for val in values:
        converted = __single_string_to_type(val)
        if type(converted) is not first_type:
            return None
        to_return.append(converted)

    # Noting that JSON *does* support heterogeneous arrays, but no sane programmer would ever want to use one 
    # If you need to parse a dict you're out of luck bro, just use the SSH that you were gifted by god and edit the file using stupid neovim

    # MyPy doesn't know we're checking that the types inside the list match
    return to_return # type: ignore

def iterkeys_nested(v: dict, *, _prefix: str = ""):
    """
    Returns a list of keys in a nested dictionary as strings.

    Nesting levels are printed as `level0.level1.level2`
    """

    # I completely stole this from StackOverflow btw
    # Some guy over there said "Saying `yield from` is basically a for loop is an insult to its design"
    # Yeah bro I guess, I barely know how generators work
    for key, val in v.items():
        if type(val) is dict:
            yield from iterkeys_nested(val, _prefix=f'{key}.')
        else:
            yield _prefix + key