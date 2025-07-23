def __getjson(self, inpstr):
    from collections import defaultdict

    def parse_value(val):
        """ Zamień [x, y, z] na listę floatów, jeśli się da """
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            try:
                return [float(v.strip()) for v in val[1:-1].split(",")]
            except ValueError:
                return val  # Nie da się sparsować – zostaw jako string
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except ValueError:
            return val

    stack = [{}]  # pierwszy element to root dict
    indent_stack = [-1]  # poziomy wcięcia odpowiadające stackowi

    for line in inpstr.splitlines():
        if not line.strip():
            continue  # pomiń puste linie

        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        if ":" not in content:
            continue

        key, value = map(str.strip, content.split(":", 1))
        value = parse_value(value)

        # Ustal poziom zagnieżdżenia
        while indent <= indent_stack[-1] and len(stack) > 1:
            stack.pop()
            indent_stack.pop()

        # Jeśli nowy poziom – utwórz nowy słownik jako wartość klucza
        if value == "":
            stack[-1][key] = {}
            stack.append(stack[-1][key])
            indent_stack.append(indent)
        else:
            stack[-1][key] = value

    # Zapisz do globalnego jsondata
    MoCapData.jsondata.update(stack[0])
