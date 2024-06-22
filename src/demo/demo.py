def is_while(block: str) -> bool:
    if "WHILE" in block and "DO" in block:
        return True
    else:
        return False


def is_end(block: str):
    if "END" in block:
        return True
    else:
        return False


def is_in_while(row: int) -> bool:
    for i, block in enumerate(prog[row::-1]):
        if not is_while(block):
            continue
        do = block[-1]
        for prog

prog = """
WHILE[#1EQ1]DO1

END1
"""

def main():
    ...

if __name__ == "__main__":
    main()