import re
import math


def bcd(value: str) -> float:
    if re.search("[^01]", value):
        raise NCParserError("BCD計算出来ません．")
    q, mod = divmod(len(value), 4)
    result = 0
    # 足りない0を補充
    if mod != 0:
        value = "0" * (4 - mod) + value
        q += 1
    # 計算
    for i, j in enumerate(range(q-1, -1, -1)):
        i = i * 4
        result += int(value[i:i+4], 2) * 10 ** j
    return result


def bin_(value: str) -> float:
    if not is_num(value, True):
        raise NCParserError("BIN計算出来ません．")
    result = ""
    for s in value:
        b = bin(int(s))[2:].zfill(4)
        result += b
    return float(result)


def split_asmd(value: str) -> list:
    result = []
    bkt_cnt = 0
    tmp = ""
    for val in value:
        if val == "[":
            bkt_cnt += 1
        elif val == "]":
            bkt_cnt -= 1
        if bkt_cnt == 0 and val in {"+", "-", "*", "/"}:
            result.append(tmp)
            result.append(val)
            tmp = ""
        else:
            tmp += val
    result.append(tmp)
    if not result[0]:
        result[0] = "0"
    return result


def is_num(value: str, int_only: bool) -> bool:
    try:
        f = float(value)
    except ValueError:
        return False
    if int_only:
        if int(f) != f:
            return False
    return True


class NCParserError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


def solve(value: str) -> float:
    """エンコードされた値を計算"""
    # 四則演算で分割
    result = split_asmd(value)
    print("split", result)
    # 分割した要素の偶数番目を式から値に変換
    for i, val in enumerate(result[::2]):
        i = i * 2
        if is_num(val, False):
            pass
        elif val[0] == "[" and val[-1] == "]":
            result[i] = solve(val[1:-1])
        elif val[0] == "#":
            v = solve(val[1:])
            if not is_num(str(v), True):
                raise NCParserError("マクロキーが整数ではありません．")
            result[i] = v * 2
        elif val[:4] == "SQRT":
            v = solve(val[5:-1])
            result[i] = math.sqrt(v)
        elif val[:3] == "ABS":
            v = solve(val[4:-1])
            result[i] = abs(v)
        elif val[:3] == "SIN":
            v = solve(val[4:-1])
            result[i] = math.sin(v)
        elif val[:3] == "COS":
            v = solve(val[4:-1])
            result[i] = math.cos(v)
        elif val[:3] == "TAN":
            v = solve(val[4:-1])
            result[i] = math.tan(v)
        elif val[:4] == "ATAN":
            v = solve(val[5:-1])
            result[i] = math.atan(v)
        elif val[:5] == "ROUND":
            v = solve(val[6:-1])
            result[i] = round(v)
        elif val[:3] == "FIX":
            v = solve(val[4:-1])
            result[i] = math.floor(v)
        elif val[:3] == "FUP":
            v = solve(val[4:-1])
            result[i] = math.ceil(v)
        elif val[:3] == "BIN":
            v = solve(val[4:-1])
            result[i] = bin_(str(v))
        elif val[:3] == "BCD":
            v = solve(val[4:-1])
            result[i] = bcd(str(v))
        else:
            v = solve(val)
            result
    # 四則演算
    return eval("".join(map(str, result)))


val = "#4*[#2-5]"
val = "-#1+5*[SQRT[#2+#3/#4]-ABS[#6*2]]"
val = solve(val)
print(val)
