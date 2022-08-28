import re
from utils import replacement, get_register_type
import os


class ReadTXT:

    def __init__(self, config):
        self.config = config

    ##step 1: file to dict
    def extract_csv(self, fn):

        def get_indexAll(lst=None, item=''):
            return [
                index for (index, value) in enumerate(lst) if value == item
            ]

        def load_path(path):
            if not os.path.isfile(path):
                print("Rules File not exist.")
                quit(-1)
            with open(path, 'r') as fp:
                return fp.read()

        def readMemo(lines):
            for row in lines:
                # get memory info
                row = row.split(';')
                tmp = {}
                tmp['address'] = str(hex(int(''.join(row[0].split('_')), 16)))
                tmp['name'] = row[1]
                tmp['width'] = row[2]
                tmp['access'] = row[3].strip()
                tmp['reset'] = row[4]
                tmp['long_name'] = re.search(self.config.name_pattern,
                                             row[1]).group(1)
                tmp['link'] = '_'.join(tmp['long_name'].split('_')[1:])
                tmp['type'] = get_register_type(row[1], row[5])
                reg_names[tmp['link']] = tmp['name'].lower()
                self.memory.append(tmp)

        def readInterrupt(lines):
            for row in lines:
                row = row.split(';')
                # get interrupt info
                self.interrupts.append([row[1].strip(" "), row[2].strip(" ")])
                self.interrupts[-1].append(row[0])
                if '-' not in row[3]:
                    self.interrupts[-1].append(row[3])

        def readField(lines):
            for row in lines:
                if row.count('|') > 1:
                    continue
                # get register name
                m = re.search(self.config.register_pattern, row)
                if m is not None:
                    if m.group(1) not in self.registers:
                        cur_reg_name = '_'.join(m.group(1).split('_')[1:])
                        if cur_reg_name in reg_names:
                            self.registers[cur_reg_name] = {
                                'title': reg_names[cur_reg_name]
                            }
                        else:
                            self.registers[cur_reg_name] = {'title': ''}
                        #self.registers[cur_reg_name]['Focus'] = set()
                    continue
                row = row.split(';')
                if row[0].lower() == "field":
                    continue

                if row[0] != "":
                    m = re.match(self.config.field_bit_pattern, row[0])
                    cur_field_condition = ""
                    if m is not None:
                        cur_field_name = row[0].split(' ')[1]
                        if cur_field_name.lower() == 'reserved':
                            cur_field_name = cur_reg_name + " " + row[0]
                            self.read_only.append(cur_reg_name + "[" +
                                                  cur_field_name + "]")
                            self.registers[cur_reg_name][cur_field_name] = {
                                '0': {
                                    'TA': 0
                                },
                                'B': m.group(1),
                                'title': 'reserved'
                            }
                        else:
                            named_entity = cur_reg_name + "[" + cur_field_name + "]"
                            if 'READ ONLY' in row[1]:
                                self.read_only.append(named_entity)
                            elif 'WRITE ONLY' in row[1]:
                                self.write_only.append(named_entity)
                            elif 'rc_w0' in row[1]:
                                self.read_clear.append(named_entity)
                                self.write1_clear.append(named_entity)
                            elif 'w1c' in row[1]:
                                self.write1_clear.append(named_entity)
                            self.registers[cur_reg_name][cur_field_name] = {
                                'B': m.group(1),
                                'title': replacement(self.config,
                                                     row[1].lower())
                            }
                    else:
                        cur_field_name = row[0]
                        if cur_field_name.lower() == 'reserved':
                            self.registers[cur_reg_name][cur_field_name] = {
                                '0': {
                                    'TA': 0
                                },
                                'title': 'reserved'
                            }
                        else:
                            self.registers[cur_reg_name][cur_field_name] = {
                                'title': replacement(self.config,
                                                     row[1].lower())
                            }
                    continue

                if len(row[1]) > 5:
                    if row[1].find('NOTE:') == -1:
                        cur_field_condition += row[1]
                    else:
                        self.registers[cur_reg_name][cur_field_name][
                            'NT'] = replacement(
                                self.config, row[1],
                                cur_reg_name + '[' + cur_field_name + ']')
                else:
                    self.registers[cur_reg_name][cur_field_name][row[1]] = {
                        'C':
                        replacement(self.config, row[2],
                                    cur_reg_name + '[' + cur_field_name + ']')
                    }
                self.registers[cur_reg_name][cur_field_name][
                    'GC'] = replacement(
                        self.config, cur_field_condition,
                        cur_reg_name + '[' + cur_field_name + ']')

        def readMode(lines):
            cur_mode_name = ""
            for row in lines:
                if row.count('|') > 1:
                    continue
                # mode description
                row = row.split(';')
                if row[0] != "":
                    cur_mode_name = row[0]
                    self.modes[cur_mode_name] = {'desc': '', 'req': ''}
                    self.modes[cur_mode_name]['desc'] = row[1]
                elif len(row) == 3:
                    self.modes[cur_mode_name]['req'] += "." + row[2]
                else:
                    self.modes[cur_mode_name]['desc'] += '\n' + row[1]

        self.registers = {}
        self.memory = []
        self.interrupts = []
        self.modes = {}
        self.read_only = []
        self.write_only = []
        self.read_clear = []
        self.write1_clear = []
        reg_names = {}
        fileContent = load_path(fn)
        rule_lines = fileContent.splitlines()
        rule_lines = [l for l in rule_lines if l != ""]
        splits_index = get_indexAll(rule_lines, '====')
        readMemo(rule_lines[0:splits_index[0]])
        readField(rule_lines[splits_index[0] + 1:splits_index[1]])
        if len(splits_index) == 3:
            if (rule_lines[splits_index[1] + 1] == 'Mode Description'):
                readMode(rule_lines[splits_index[1] + 2:splits_index[2]])
            else:
                readInterrupt(rule_lines[splits_index[1] + 1:splits_index[2]])

    def extract_dma_num(self, fn):
        self.dma_num = []
        with open(fn, 'r') as f:
            for row in f.readlines():
                row = row.strip('\n')
                if row == "":
                    continue
                row = row.split(';')
                for i in row[3:]:
                    tmp = {}
                    tmp['num'] = row[0]
                    tmp['peri'] = row[1]
                    tmp['channel'] = row[2]
                    tmp['source'] = i
                    self.dma_num.append(tmp)

    def extract_interrupt_num(self, fn):
        self.interrupt_num = []
        with open(fn, 'r') as f:
            for row in f.readlines():
                row = row.strip('\n')
                if row == "":
                    continue
                row = row.split(';')
                tmp = {}
                tmp['num'] = row[1]
                m = re.search(self.config.channel_pattern, row[6])
                if m is not None:
                    tmp['source'] = row[5] + m.group(1)
                else:
                    tmp['source'] = row[5].split('_')[0]
                tmp['error'] = row[6].lower().find('error') != -1
                tmp['type'] = row[6].lower()
                self.interrupt_num.append(tmp)

    def field2reg(self):
        f2r = {}
        for reg in self.registers:
            f2r[reg] = ''
            for key, value in self.registers[reg].items():
                if isinstance(value, dict):
                    if key in f2r:
                        f2r[f2r[key] + '+' + key] = f2r[key]
                        key = reg + '+' + key
                    f2r[key] = reg
        f2r['receive-buffer'] = ''
        f2r['transmit-buffer'] = ''
        f2r['receive buffer'] = ''
        f2r['transmit buffer'] = ''
        self.f2r = f2r

    def correference(self):
        self.reg_type = {}
        self.relation = {}
        self.prex = []
        for m in self.memory:
            self.prex.append(m['long_name'].split('_')[0])
            self.mapping_name(m['link'])
            tmp = self.relation[m['link']]
            self.reg_type[tmp] = m['type']
        self.width = int(m['width'])
        self.prex = list(set(self.prex))

    def save_mapping(self, reg_dec, tmp, link):
        if tmp in reg_dec:
            self.relation[link] = tmp
            if link == tmp:
                return
            if tmp in self.relation and link not in self.relation[tmp]:
                self.relation[tmp].append(link)
            else:
                self.relation[tmp] = [link]

    def mapping_name(self, link):
        tmp = link
        reg_dec = self.registers.keys()
        if ('SC1A' not in reg_dec):
            tmp = re.sub(r'SC1[AB]$', r'SC1n', tmp)
        if ('RA' not in reg_dec):
            tmp = re.sub(r'R[AB]$', r'Rn', tmp)
        if ('F1R1' not in reg_dec):
            tmp = re.sub(r'F\d{1,3}R\d$', r'FiRx', tmp)
        self.save_mapping(reg_dec, tmp, link)
        if re.search('\d', link) != None:
            tmp = re.sub(r'(.+[A-Z])(\d+)', r'\1n', link)
            self.save_mapping(reg_dec, tmp, link)
            tmp = re.sub(r'([A-Z]+)(\d)([A-Z]+)', r'\1n\3', link)
            self.save_mapping(reg_dec, tmp, link)