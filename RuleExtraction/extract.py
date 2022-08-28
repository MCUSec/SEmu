from read_txt import ReadTXT
import sys
import json
import os
from os.path import exists
from utils import Config, Signals
from ca import ExtractCA
from interrupt import ExtractInterrupt
from hw import ExtractHardwareSignals
from transform import Transform


class RuleExtraction:

    def __init__(self, argv):
        self.config = Config()
        self.signals = Signals()
        self.get_new_json = True
        device = "Manuals/" + argv[1]
        chip_name = argv[2]
        self.device = device
        self.config.chip_name = chip_name
        if len(argv) == 4:
            #chip_prex = argv[3]
            self.get_new_json = int(argv[3])
        self.csv_file = device + '/tabula-' + chip_name + '.csv'
        if not exists(device + '/data/'):
            os.mkdir(device + '/data/')
        self.memory_file = device + '/data/' + chip_name + 'memory.txt'
        self.memory_json_file = device + '/data/' + chip_name + 'memory.json'
        self.register_file = device + '/data/' + chip_name + 'registers.json'
        self.result_file = device + '/data/' + chip_name + 'result.json'
        self.mode_file = device + '/data/' + chip_name + 'mode.json'
        self.flag_txt_file = device + '/data/' + chip_name + 'flag.txt'
        self.register_txt_file = device + '/data/' + chip_name + 'registers.txt'
        self.ta_txt_file = device + '/data/' + chip_name + 'tas.txt'
        self.interrupts_file = device + '/data/' + chip_name + 'interrupts.json'

    def extract(self):
        self.txt = ReadTXT(self.config)
        self.txt.extract_csv(self.csv_file)
        if len(self.txt.registers) == 0:
            return
        self.txt.extract_interrupt_num(self.device + '/interrupt.csv')
        self.txt.dma_num = []
        if exists(self.device + '/dma.csv'):
            self.txt.extract_dma_num(self.device + '/dma.csv')

        self.txt.field2reg()
        self.txt.correference()

        #self.test()
        self.extract_rule()

        self.extract_interrupt()

        self.extract_signals()

    def extract_signals(self):
        self.hw = ExtractHardwareSignals(self.txt, self.signals)
        self.hw.extract_signals()

    def extract_interrupt(self):
        self.interrupt = ExtractInterrupt(self.txt)
        self.interrupt.get_interrupt()
        with open(self.interrupts_file, 'w') as outfile:
            json.dump(self.txt.interrupt_res, outfile)

    def extract_rule(self):
        if self.get_new_json is 0:
            self.load_from_file()
            return
        self.ca = ExtractCA(self.txt, self.signals)
        self.ca.extract_TA()
        if self.config.chip_name == 'MCG':
            print('mode...')
            self.ca.extract_mode()
        self.save_to_file()

    def test(self):
        from utils import replacement
        seq = "LOCK0 is enabled when the PLL is enabled (either through clock mode selection or PLLCLKEN0 = 1 setting)."
        seq = "Writing 1 to RSTCNT[RSTCNT] to be cleared enables you to clear the contents of RSTCNT[RSTCNT]."
        seq = "BDH[SBNS] is not valid when C7816[ISO7816E] is enabled."
        seq = "If read D ,  the amount of the receive-buffer is 0."
        seq = " SFIFO[RXOF] is cleared by writing a 1."
        self.ca = ExtractCA(self.txt, self.signals)
        self.ca.extract(replacement(self.config, seq), None)
        exit()

    def load_from_file(self):
        print("loading...")
        with open(self.register_file, 'r') as outfile:
            self.txt.registers = json.load(outfile)
        with open(self.result_file, 'r') as outfile:
            self.txt.result = json.load(outfile)
        if self.config.chip_name == 'MCG':
            with open(self.mode_file, 'r') as outfile:
                self.txt.mode_result = json.load(outfile)

    def save_to_file(self):
        with open(self.memory_json_file, 'w') as outfile:
            json.dump(self.txt.memory, outfile)
        with open(self.register_file, 'w') as outfile:
            json.dump(self.txt.registers, outfile)
        with open(self.result_file, 'w') as outfile:
            json.dump(self.txt.result, outfile)
        if self.config.chip_name == 'MCG':
            with open(self.mode_file, 'w') as outfile:
                json.dump(self.txt.mode_result, outfile)

    def save(self):
        transform = Transform(self.txt, self.signals)
        transform.save_memory(self.memory_file)
        if len(self.txt.registers) == 0:
            return
        transform.save(self.ta_txt_file, self.flag_txt_file)
        pass


if __name__ == '__main__':
    rule = RuleExtraction(sys.argv)
    rule.extract()
    rule.save()
