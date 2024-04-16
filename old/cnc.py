import re


class CNC:
    def __init__(self):
        self.axis = Axis()

    def reset(self):
        self.axis.reset()

    def read(self, block):
        self.axis.read(block)


class Macro:
    def __init__(self):
        ...

    def string_to_float(self, value: str, micron: bool = False) -> float:
        ...

#
class Axis:
    def __init__(self, macro: Macro = None):
        self.__macro = macro
        self.__gr3 = 91
        self.__gr14 = 54
        self.__coordinates = WorkCoordinates()
        self.__last_position = [0, 0, 0, 0, 0]
        self.__position = [0, 0, 0, 0, 0]

    def reset(self):
        self.__gr3 = 91
        self.__gr14 = 54
        self.__last_position = [0, 0, 0, 0, 0]
        self.__position = [0, 0, 0, 0, 0]

    def read(self, block: str):
        self.__parse(block)

    def __parse(self, block: str):
        # コメント削除
        block = self.__remove_comment(block)

        # プログラム先頭でリセット
        if "O" in block:
            self.reset()

        # group3モーダル
        if gr3 := re.search(".*G(9[01])[^0-9]?", block):
            self.__gr3 = self.__stf(gr3.group(1))

        # group14モーダル
        if gr14 := re.search(".*G54\.1P([0-9]+)[^0-9]?|.*G(5[4-9])[^0-9]?",
                             block):
            if gr14.group(1) is not None:
                self.__gr14 = self.__stf(gr14.group(1))
            else:
                self.__gr14 = self.__stf(gr14.group(2))

        # モーダルチェック
        # Gコードグループ3の判別に失敗
        assert self.__gr3 in {90, 91}
        # Gコードグループ14の判別に失敗
        assert (1 <= self.__gr14 <= 48 or 54 <= self.__gr14 <= 59)

        # ワーク座標書き込み
        if wcp := re.findall("G10L(20?)P([0-9]+)", block):
            wcn = self.__stf(wcp[-1][1])
            if wcp[-1][0] == "2":
                wcn += 53
            axis = [0, 0, 0, 0, 0]
            for i, axadd in enumerate(("X", "Y", "Z", "A", "B")):
                if offset := re.search(f".*{axadd}(-?[0-9]+\.?[0-9]*)", block):
                    axis[i] = self.__stf(offset.group(1))
            if self.__gr3 == 90:
                self.__coordinates[wcn] = axis
            elif self.__gr3 == 91:
                self.__coordinates[wcn] = [ax1 + ax2 for ax1, ax2 in
                                           zip(axis, self.__coordinates[wcn])]
            return

        # 工具長書き込み

        # 工具径書き込み

        # 軸移動
        if "G65" in block or "G66" in block or "G4" in block:
            return
        for i, ax in enumerate(("X", "Y", "Z", "A", "B")):
            if pat := re.search(f".*{ax}(-?[0-9]+\.?[0-9]*)", block):
                coord = self.__stf(pat.group(1))
                if "G53" in block:
                    pass
                elif self.__gr3 == 90:
                    coord += self.__coordinates[53][i] + \
                             self.__coordinates[self.__gr14][i]
                elif self.__gr3 == 91:
                    coord += self.__position[i]
                self.__last_position[i] = self.__position[i]
                self.__position[i] = coord

    def __stf(self, value: str, is_micron: bool = False):
        if self.macro is None:
            return float(value)
        else:
            return self.__macro.string_to_float(value)

    @staticmethod
    def __remove_comment(block):
        while True:
            pattern = re.search("\(.*?\)", block)
            if pattern is None:
                break
            block = block[:pattern.start()] + block[pattern.end():]
        return block

    @property
    def x(self) -> float:
        return self.__position[0]

    @property
    def y(self) -> float:
        return self.__position[1]

    @property
    def z(self) -> float:
        return self.__position[2]

    @property
    def a(self) -> float:
        return self.__position[3]

    @property
    def b(self) -> float:
        return self.__position[4]

    @property
    def xyz(self):
        return tuple(self.__position[:3])

    @property
    def all(self) -> tuple:
        return tuple(self.__position)

    @property
    def group3(self) -> int:
        return self.__gr3

    @property
    def group14(self) -> int:
        return self.__gr14

    @property
    def is_movement(self):
        return (last != now for last, now in
                zip(self.__position, self.__last_position))

    @property
    def macro(self):
        return None

    @macro.setter
    def macro(self, macro):
        if not isinstance(macro, Macro):
            raise ValueError("argument, is not Macro instance")
        if self.__macro is not None:
            raise ValueError("this attribute cannot be set twice")
        self.__macro = macro


class WorkCoordinates:
    def __init__(self):
        self.__coordinates = {}
        self.reset()

    def __getitem__(self, item):
        return tuple(self.__coordinates[item])

    def __setitem__(self, key, value):
        if not key in self.__coordinates.keys():
            raise ValueError("key arg is value error")
        if not isinstance(value, (list, tuple)) or len(value) != 5:
            raise ValueError("value arg is value error")
        else:
            self.__coordinates[key] = value

    def reset(self):
        wc = {}
        for i in range(53, 60):
            wc[i] = [0, 0, 0, 0, 0]
        for i in range(1, 49):
            wc[i] = [0, 0, 0, 0, 0]
        self.__coordinates = wc
