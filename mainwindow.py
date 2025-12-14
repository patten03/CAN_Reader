# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QLineEdit
import re

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.load_bin.clicked.connect(self.click_load_bin)

    def calculate_crc15(self, id: int, rtr: bool, ide: bool, dlc: int, data: list[int]) -> int:
        # константы для CAN CRC15
        crc15_polynomial = 0x4599 # x^15 + x^14 + x^10 + x^8 + x^7 + x^4 + x^3 + 1
        crc15_mask = 0x7fff       # Маска для 15 бит (0b0111111111111111)
        crc15_length = 15         # Длина CRC в битах

        # Размеры полей CAN кадра в битах
        arbitration_field_bits = 15 # SOF(1) + ID(11) + RTR(1) + IDE(1) + r0(1)
        control_field_bits = 4      # DLC(4) + reserved(2)
        bits_per_byte = 8

        crc = 0
        bitstream = 0 + id + int(rtr) + int(ide) + 0

        # Общее количество бит для расчета CRC
        dataFieldBits = dlc * bits_per_byte
        totalBitsForCRC = arbitration_field_bits + control_field_bits + dataFieldBits

        for currentBit in range(0,totalBitsForCRC):
            inputBit = None
            
            # Определяем откуда брать текущий бит
            if(currentBit < arbitration_field_bits):
                # Биты из арбитражного поля
                bitPositionInArbitration = arbitration_field_bits - 1 - currentBit
                inputBit = (bitstream >> bitPositionInArbitration) & 0x01
            elif(currentBit < arbitration_field_bits + control_field_bits):
                # Биты из контрольного поля (DLC + reserved)
                # ЗАГЛУШКА - здесь нужно передавать полный контрольный field
                inputBit = False
            else:
                # Биты из поля данных
                bitIndexInDataField = currentBit - (arbitration_field_bits + control_field_bits)
                byteIndex = bitIndexInDataField // bits_per_byte
                bitIndexInByte = bits_per_byte - 1 - (bitIndexInDataField % bits_per_byte)

                if (byteIndex < dlc):
                    inputBit = (data[byteIndex] >> bitIndexInByte) & 0x01
                else:
                    inputBit = False

            # Сдвигаем CRC и обрабатываем новый бит
            crcMostSignificantBit = bool((crc >> (crc15_length - 1)) & 0x01)
            crc = (crc << 1) & crc15_mask

            # Применяем полином если MSB XOR inputBit = 1
            if (crcMostSignificantBit ^ inputBit):
                crc ^= crc15_polynomial

        return crc

    # функция, вызываемая по нажатию кнопки
    def click_load_bin(self):
        # получаем выбранный файл от пользователя
        abs_file = QFileDialog.getOpenFileName(self, 'Открыть бинарный файл', '.', "Binary files (*.bin)")
        abs_file = abs_file[0]

        # чистим старый вывод
        for line_edit in self.findChildren(QLineEdit):
            line_edit.clear()

        if(abs_file):
            binary = ''
            # чтение бинарного файла
            with open(abs_file,'rb') as f:
                a = f.read()
                size = len(a)
                b = int.from_bytes(a, byteorder='big')
                binary = (format(b,f'0{size * 8}b'))

            # находим CRC Delimiter + ACK + ACK Delimiter + End of frame и удаляем их
            binary = binary[0:binary.rfind('1011111111')]

            # находим stuff-bit error
            if (binary.find('111111') != -1 and binary.find('000000') != -1):
                self.ui.bit_stuffing.setText('Error')                
                return
            else:
                self.ui.bit_stuffing.setText('Ok')

            # удаляем все stuff bit
            binary = re.sub(r'(0{5}1)', '00000', binary)
            binary = re.sub(r'(1{5}0)', '11111', binary)

            # удаляем start bit
            binary = binary[1:]

            # определяем идентификатор
            id = int(binary[0:11], 2)
            self.ui.id.setText(f"0x{id:0{3}x}")
            binary = binary[11:]

            # определяем RTR
            rtr = bool(int(binary[0], 2))
            self.ui.rtr.setText(str(int(rtr)))
            binary = binary[1:]

            # определяем IDE
            ide = bool(int(binary[0], 2))
            self.ui.ide.setText(str(int(ide)))
            binary = binary[2:]

            # определяем DLC
            dlc = int(binary[0:4], 2)
            self.ui.dlc.setText(f"0x{dlc:0{2}x}")
            binary = binary[4:]

            # получаем данные, если не вызван rtr
            data = []
            bytes = [self.ui.byte_1,
                     self.ui.byte_2,
                     self.ui.byte_3,
                     self.ui.byte_4,
                     self.ui.byte_5,
                     self.ui.byte_6,
                     self.ui.byte_7,
                     self.ui.byte_8,
                     ]
            if not rtr:
                for i in range(dlc):
                    data.append(int(binary[0:8], 2))
                    bytes[i].setText(f"0x{data[i]:0{2}x}")
                    binary = binary[8:]

            # определяем CRC
            crc = int(binary[0:15], 2)
            self.ui.crc.setText(f"0x{crc:0{2}x}")
            binary = binary[15:]

            # определяем верность CRC
            if (self.calculate_crc15(id,rtr,ide,dlc,data) == crc):
                self.ui.crc_error.setText('Ok')
            else:
                self.ui.crc_error.setText('Error')



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
