import re
from utils import field_reg_search


class Field:

    def __init__(self, name):
        self.name = name
        self.init_status = ""
        self.bit = []
        self.uncheck = False
        self.cur_status = self.init_status
        self.general_trigger_action = []  #[[t1, a1],[t2,a2]]
        self.specific_trigger_action = {}  #{0:[t3, a3],1:[t4, a4]}

    def __str__(self):
        return self.name + " " + str(self.init_status) + " " + str(
            self.bit) + " " + str(self.general_trigger_action) + " " + str(
                self.specific_trigger_action)


class Register:

    def __init__(self, link, address, width, t, access, reset, name):
        self.name = link
        self.long_name = name
        self.address = address
        self.width = int(width)
        self.type = t  #1 read only #0 write and read
        self.access = access
        self.reset = bin(int(reset.strip('h'), 16))[2:].zfill(self.width)
        self.cur_value = self.reset
        self.fields = {}

    def add_field(self, field):
        for i in field.bit:
            field.init_status += self.reset[i]
        field.cur_status = field.init_status
        self.fields[field.name] = field

    def set_graph(self, field2reg, entities):
        self.field2reg = field2reg
        self.entities = entities

    def __str__(self):
        return self.name + " " + str(self.address) + " " + str(
            self.width) + " " + self.reset


class Transform:

    def __init__(self, txt, signals):
        self.txt = txt
        self.signals = signals
        #self.hw = hw

    def save_memory(self, memory_file):
        prev = int(''.join(self.txt.memory[0]['address'].split('_')), 16)
        real_width = 0x100
        for idx in range(1, len(self.txt.memory)):
            m = self.txt.memory[idx]
            cur = int(''.join(m['address'].split('_')), 16)
            if (cur >= prev + 0x100) or (cur <= prev - 0x100) or cur == prev:
                prev = cur
                continue
            #print(m, abs(cur - prev)*8, real_width)
            real_width = min(real_width, abs(cur - prev) * 8)
            prev = cur
        with open(memory_file, 'w') as f:
            for m in self.txt.memory:
                length = set(list(range(0, int(m['width']))))
                cur = int(''.join(m['address'].split('_')), 16)
                if len(self.txt.registers) != 0 and m['type'] in [
                        'R', 'T', 'D'
                ]:
                    tmp = self.txt.relation[m['link']]
                    final_length = set()
                    for field_name, field in self.txt.registers[tmp].items():
                        #print(field_name, field)
                        if isinstance(field, dict) == False:
                            continue
                        if 'Reserved' not in field_name:
                            if 'B' not in field:
                                continue
                            bit = field['B'].split('-')
                            if len(bit) == 2:
                                final_length = final_length.union(
                                    set(
                                        list(
                                            range(int(bit[1]),
                                                  int(bit[0]) + 1))))
                            else:
                                final_length = final_length.union(
                                    set([int(field['B'])]))
                    if len(final_length) != 0:
                        length = final_length
                eth = ""
                real_width = max(real_width, len(length))
                if 'Ethernet' in memory_file:
                    eth += 'E'
                if m['type'] == 'R':
                    self.txt.f2r['receive-buffer'] = m['link']
                    self.txt.f2r['receive buffer'] = m['link']
                    f.write(m['type'] + eth + '_' + str(hex(cur)) + '_' +
                            str(hex(int(m['reset'].strip('h'), 16))) + '_' +
                            str(real_width) + '_' + str(len(length)) + '\n')
                elif m['type'] == 'T':
                    self.txt.f2r['transmit-buffer'] = m['link']
                    self.txt.f2r['transmit buffer'] = m['link']
                    f.write(m['type'] + eth + '_' + str(hex(cur)) + '_' +
                            str(hex(int(m['reset'].strip('h'), 16))) + '_' +
                            str(real_width) + '_' + str(len(length)) + '\n')
                elif m['type'] == 'D':
                    #data_addr = str(hex(cur))
                    f.write('R' + eth + '_' + str(hex(cur)) + '_' +
                            str(hex(int(m['reset'].strip('h'), 16))) + '_' +
                            str(real_width) + '_' + str(len(length)) + '\n')
                    f.write('T' + eth + '_' + str(hex(cur)) + '_' +
                            str(hex(int(m['reset'].strip('h'), 16))) + '_' +
                            str(real_width) + '_' + str(len(length)) + '\n')
                    self.txt.f2r['receive-buffer'] = m['link']
                    self.txt.f2r['transmit-buffer'] = m['link']
                    self.txt.f2r['receive buffer'] = m['link']
                    self.txt.f2r['transmit buffer'] = m['link']
                elif m['type'] == 'ED':
                    f.write('O' + eth + '_' + str(hex(cur)) + '_' +
                            str(hex(int(m['reset'].strip('h'), 16))) + '_' +
                            str(real_width) + '_' + str(m['width'].strip()) +
                            '\n')
                else:
                    f.write(m['type'] + eth + '_' + str(hex(cur)) + '_' +
                            str(hex(int(m['reset'].strip('h'), 16))) + '_' +
                            str(real_width) + '_' + str(m['width'].strip()) +
                            '\n')

    def combination(self, check, i, tmp, res):
        if (len(check) == i):
            res.append(tmp)
            return res
        for k in range(len(check[i])):
            _tmp = tmp.copy()
            _tmp.append(check[i][k])
            self.combination(check, i + 1, _tmp, res)
        return res

    def get_pairs(self):
        check = []
        szs = []
        for r in self.txt.relation:
            if type(self.txt.relation[r]) == list:
                check.append(self.txt.relation[r])
                szs.append(len(self.txt.relation[r]))
        if len(szs) == 0:
            return [("", "")]
        pairs = []
        tmp1 = []
        for j in check:
            tmp1.append(self.txt.relation[j[0]])

        if len(set(szs)) == 1:
            for i in range(szs[0]):
                tmp2 = []
                end = check[0][i][-1]
                for j in check:
                    tmp2.append(j[i])
                    if (j[i][-1] != end or end == 'R'):
                        end = str(i)
                pairs.append(((tmp1, tmp2), end))
        else:
            res = []
            tmp = self.combination(check, 0, [], res)
            for tmp2 in tmp:
                pairs.append(((tmp1, tmp2), ''))
        return pairs

    def construct(self, prex, check):
        self.entities = {}
        field2reg = {}
        self.data_addr = {}
        for m in self.txt.memory:
            if m['long_name'].split('_')[0] != prex:
                continue
            link = m['link']
            if check != '':
                if link in check[1]:
                    link = self.txt.relation[link]
                elif self.txt.relation[link] in check[0]:
                    continue

            reg = Register(link, m['address'], m['width'], m['type'],
                           m['access'], m['reset'], m['long_name'])
            if reg.type == 'D':
                self.data_addr['T'] = reg.address
                self.data_addr['R'] = reg.address
                field2reg['receive-buffer'] = reg.name
                field2reg['transmit-buffer'] = reg.name
            elif reg.type == 'R':
                self.data_addr['R'] = reg.address
                field2reg['receive-buffer'] = reg.name
            elif reg.type == 'T':
                self.data_addr['T'] = reg.address
                field2reg['transmit-buffer'] = reg.name

            fields = self.txt.registers[link]
            all_bits = set(list(range(0, int(m['width']))))
            for key, value in fields.items():
                if isinstance(value, dict) == False:
                    continue
                tmp = Field(key)
                for k, v in value.items():
                    if k == 'B':
                        bit = v.split('-')
                        if len(bit) == 2:
                            tmp.bit = set(
                                list(range(int(bit[1]),
                                           int(bit[0]) + 1)))
                            all_bits = all_bits - tmp.bit
                        else:
                            tmp.bit = set([int(v)])
                            all_bits = all_bits - tmp.bit
                    elif k == 'EGTA':
                        tmp.general_trigger_action = v
                        #print(v)
                    elif k == 'GC':
                        continue
                    elif 'ETA' in v:
                        tmp.specific_trigger_action[k] = v['ETA']
                if 'B' not in value.keys():
                    tmp.bit = all_bits
                tmp.bit = sorted(tmp.bit, reverse=True)
                #print(tmp.bit, value)
                reg.add_field(tmp)
                field2reg[tmp.name] = reg.name
            self.entities[reg.name] = reg

        for r in self.entities:
            self.entities[r].set_graph(field2reg, self.entities)

    def to_address(self, field, _type=''):
        if field.find('[') == -1:
            if field in self.entities:
                reg = field
                field = '*'
            else:
                return field
        else:
            reg, field = field.split('[')[0], field[field.index('[') + 1:-1]

        if reg not in self.entities:
            print(f'Error 925:', field, reg, self.entities.keys())
            return ""
        if self.entities[reg].type == 'L' and _type == 'V':
            _type = 'L'
        a = _type + ',' if _type != '' else ""
        if field == '*' or len(self.entities[reg].fields[field].bit
                               ) == self.entities[reg].width:
            a += str(self.entities[reg].address) + ',' + '*'
        else:
            a += str(self.entities[reg].address) + ',' + '/'.join(
                [str(i) for i in self.entities[reg].fields[field].bit])
        return a

    #type address bit value
    def locate_eq(self, equation, action):
        if equation == 'ALL':
            return "O,*"
        address, value = equation.split(' = ')[0], equation.split(' = ')[1]
        if 'transmit-buffer' in value:
            value = '#T' + self.data_addr['T']
        elif 'receive-buffer' in value:
            value = '#R' + self.data_addr['R']
        elif value == 'read':
            pass
        elif value == 'write':
            pass
        elif value == 'write1':
            pass
        else:
            value = self.to_address(value)

        if address == 'D' or address == 'DR':
            #return 'R', '*R'+data_addr, '*', '=', '*'
            if value == 'read':
                return ','.join(
                    ['R', '*R' + self.data_addr['R'], '*', '=', '*'])
            elif value == 'write':
                return ','.join(
                    ['W', '*T' + self.data_addr['T'], '*', '=', '*'])
        elif value == 'write1':
            return self.to_address(address, 'W') + ',=,1'
        elif value == 'read':
            return self.to_address(address, 'R') + ',=,*'
        elif address == 'transmit-buffer':
            if 'T' not in self.data_addr:
                import pdb
                pdb.set_trace()
            tag = "" if action else "V"
            return ','.join([
                '#T' + self.data_addr['T'], '*', '=',
                str(bin(int(value))[2:])
            ])
        elif address == 'receive-buffer':
            #return 'R', '*R'+data_addr, '*', '=', value
            if 'R' not in self.data_addr:
                import pdb
                pdb.set_trace()
            tag = "" if action else "V"
            return ','.join([
                '#R' + self.data_addr['R'], '*', '=',
                str(bin(int(value))[2:])
            ])
        else:
            tag = "" if action else "V"
            address = self.to_address(address, tag)
            if value.isdigit():
                return address + ',=,' + str(bin(int(value))[2:])
            else:
                return address + ',=,' + value

    def locate_neq(self, equation, action):
        tag = "" if action else "B"
        a1 = self.to_address(equation[2], tag)

        if a1.isnumeric():
            if equation[1] == 'transmit-buffer':
                if 'T' not in self.data_addr:
                    return None
                return 'B,#T' + self.data_addr['T'] + ',*,' + equation[
                    0] + ',' + equation[2]
            elif equation[1] == 'receive-buffer':
                if 'R' not in self.data_addr:
                    return None
                return 'B,#R' + self.data_addr['R'] + ',*,' + equation[
                    0] + ',' + equation[2]
            else:
                tag = "" if action else "V"
                return self.to_address(
                    equation[1],
                    tag) + ',' + equation[0].strip(' ') + ',' + equation[2]
        check = False
        if equation[0].find('>') != -1:
            a1 += ',<'
            check = True
        if equation[0].find('<') != -1:
            a1 += ',>'
            check = True
        if equation[0].find('=') != -1:
            if check:
                a1 += '='
            else:
                a1 += ',='

        if equation[1].find('transmit-buffer') != -1:
            a1 += ',#T' + self.data_addr['T']
        elif equation[1].find('receive-buffer') != -1:
            a1 += ',#R' + self.data_addr['R']
        return a1

    def merge(self, trigger, action=False):
        check = False
        res = []
        for eq in trigger:
            if '&&' in eq:
                continue
            if '||' in eq:
                check = True
                continue
            if eq[0].find('<') != -1 or eq[0].find('>') != -1:
                tmp = self.locate_neq(eq, action)
                if tmp == None:
                    return tmp
                res.append(tmp)
                #print(eq, res[-1])
            else:
                res.append(self.locate_eq(eq, action))
                #print(eq, res[-1])
        if check == False:
            return '&'.join(res)
        else:
            return '|'.join(res)

    def save_signals_by_value(self, repeat_res, res):
        for f in self.txt.signals:
            if " = " in f:
                tmp = f.split(" = ")
                if tmp[1] != '*':
                    tmp = self.to_address(tmp[0]) + ",=," + tmp[1] + "\n"
                    if tmp not in repeat_res:
                        repeat_res.append(tmp)
                        res.append(tmp)
                    continue
                elif '[' not in tmp[0]:
                    value = hex(int('1' * self.entities[tmp[0]].width, 2))[2:]
                else:
                    reg, field_name = tmp[0].split('[')[0], tmp[0].split(
                        '[')[1].strip(']')
                    value = hex(
                        int(
                            '1' *
                            len(self.entities[reg].fields[field_name].bit),
                            2))[2:]
                tmp = self.to_address(tmp[0]) + ",=,0/" + value + "\n"
                if tmp not in repeat_res:
                    repeat_res.append(tmp)
                    res.append(tmp)

    def save_signals(self, repeat_res):
        res = []
        self.save_signals_by_value(repeat_res, res)
        for reg, fields in self.txt.registers.items():
            for field_name, field in fields.items():
                cur_field = reg + '[' + field_name + ']'
                if 'title' in field and re.search(
                        '|'.join(self.signals.non_conditions),
                        field['title'].lower()) != None:
                    continue
                if cur_field in self.txt.signals:
                    tag = ''
                    if re.search('counter|current timer|increment',
                                 field['title']) != None:
                        tag = '^'
                    if 'sspecific' in field['title']:
                        tag = '|'
                    if (tag != ''):
                        value = hex(
                            int(
                                '1' *
                                len(self.entities[reg].fields[field_name].bit),
                                2))[2:]
                        tmp = self.to_address(
                            cur_field) + ",=," + tag + value + "\n"
                        if tmp not in repeat_res:
                            repeat_res.append(tmp)
                            res.append(tmp)
                        continue

                    if re.search(
                            '|'.join(self.signals.receive +
                                     self.signals.transmit),
                            field['title']) != None:
                        if re.search('|'.join(self.signals.buffer_signal),
                                     field['title']) != None:
                            continue
                    value = ""
                    if re.search('|'.join(self.signals.flag_signal),
                                 field['title']) != None:
                        value = "0/" + hex(
                            int(
                                '1' *
                                len(self.entities[reg].fields[field_name].bit),
                                2))[2:]
                    elif re.search(
                            '|'.join(self.signals.signal_certain_1_signal),
                            field['title']) != None:
                        value = '1'
                    elif re.search(
                            '|'.join(self.signals.signal_certain_0_signal),
                            field['title']) != None:
                        value = '0'
                    if value == "":
                        #if 'GC' in field and field['GC'] != '' and 'EGTA' not in field:
                        #    tmp = field['GC'].lower()
                        #    new_flag = []
                        #    self.hw.defined_by_hardware(tmp, cur_field, field)
                        #    self.save_signals_by_value(repeat_res, res)
                        continue
                    tmp = self.to_address(cur_field) + ",=," + value + "\n"
                    if tmp not in repeat_res:
                        repeat_res.append(tmp)
                        res.append(tmp)
        return res

    def find_dma_num(self, source, field1):
        field1 = field1.split(' =')[0]
        #print(field1)
        if field1.find('[') == -1:
            return None

        reg, field = field1.split('[')[0], field1.split('[')[1].strip(']')
        channel = re.search(self.txt.config.channel_pattern,
                            self.txt.registers[reg]['title'])
        if channel is not None:
            channel = channel.group(1)
        title = self.txt.registers[reg][field]['title']
        error = title.find('error') != -1
        title = title[:title.find('interrupt') - 1].split('/')[0]
        if 'transmi' in title or 'tx' in title:
            source = [s + '_TX' for s in source]
        elif 'receive' in title or 'rx' in title:
            source = [s + '_RX' for s in source]
        interrupt = None
        for tmp in self.txt.dma_num:
            if (tmp['source'] in source):
                interrupt = tmp['num']
                #for c in dma_channels:
                #    if c[0] == tmp['peri'] and c[1] == tmp['channel']:
                #        interrupt+';'+';'.join(c[2:])
                break
        return interrupt

    def find_interrupt_num(self, source, field1):
        field1 = field1.split(' =')[0]

        if field1.find('[') == -1:
            return None

        reg, field = field1.split('[')[0], field1.split('[')[1].strip(']')
        title = self.txt.registers[reg][field]['title']
        channel = re.search(self.txt.config.channel_pattern,
                            self.txt.registers[reg]['title'])
        if channel is not None:
            channel = channel.group(1)
        error = title.find('error') != -1
        title = title[:title.find('interrupt') - 1].split('/')[0]
        interrupt = None
        for tmp in self.txt.interrupt_num:
            if (tmp['source']
                    in source) and error == tmp['error'] and error == True:
                interrupt = tmp['num']
            elif (tmp['source'] in source) and title in tmp['type']:
                interrupt = tmp['num']
            elif (tmp['source'] in source
                  ) and channel is not None and channel in tmp['type']:
                interrupt = tmp['num']
            elif tmp['source'] in source and interrupt == None:
                interrupt = tmp['num']

        return interrupt

    def save_result(self, f, _repeat_res, results, source=None):
        check = False
        for tas in results:
            for value in tas:
                trigger = value['trigger']
                action = value['action']
                trigger = self.merge(trigger)
                if trigger == None:
                    continue
                action = self.merge(action, True)

                tmp = trigger + '->' + action
                if tmp in _repeat_res:
                    continue
                _repeat_res.append(tmp)
                check = True
                if 'interrupt' in value:
                    interrupt = value['interrupt']
                    if interrupt == 'DMA':
                        num = self.find_dma_num(source, value['action'][0])
                        if num != None:
                            #print(tmp+'&DMA('+num+')\n')
                            f.write(tmp + '&DMA(' + num + ')\n')
                        #else:
                        #    action = 'D'+','+','.join(action.split(',')[1:])
                        #    f.write(trigger+':'+action+':'+str(0)+'\n')
                        continue
                    if interrupt.isnumeric():
                        f.write(tmp + '&IRQ(' + interrupt + ')\n')
                        continue
                    num = self.find_interrupt_num(source, value['trigger'][1])
                    if num != None:
                        f.write(tmp + '&IRQ(' + num + ')\n')
                    else:
                        #import pdb
                        #pdb.set_trace()
                        print('ERROR! No interrupt num:', source)
                else:
                    f.write(tmp + '\n')
        return check

    def save_dma(self, ta_txt_file, channel, peri):
        if channel.isdigit() is False:
            return ""
        if 'f429' in ta_txt_file:
            CMAR1 = self.to_address("SnMAAR", "")
            CMAR2 = self.to_address("SnMBAR", "")
            CMARn = CMAR1 + "|" + CMAR2
            CPARn = self.to_address("SnPAR", "")
            CNDTRn = self.to_address("SnNDTR", "")
            GIF = ""
        else:
            CMARn = self.to_address("CMARn", "")
            CPARn = self.to_address("CPARn", "")
            CNDTRn = self.to_address("CNDTRn", "")
            GIF = "GIF" + str(channel)
            GIF = self.txt.f2r[GIF] + "[" + GIF + "]"
            GIF = self.to_address(GIF, "")
        #print(field_reg_search("HTIF" + str(channel), self.txt, None), "HTIF" + str(channel))
        HTIF = field_reg_search("HTIF" + str(channel), self.txt, None)[0][0]
        #print('htif:',HTIF)
        HTIF = self.to_address(HTIF, "")
        TCIF = field_reg_search("TCIF" + str(channel), self.txt, None)[0][0]
        TCIF = self.to_address(TCIF, "")
        interrupt = 0
        for tmp in self.txt.dma_num:
            _channel = tmp['channel'][-1]
            if (channel == _channel) and (peri == tmp['peri']):
                interrupt = tmp['num']
                break
        return str(interrupt) + ';' + ';'.join(
            [CMARn, CPARn, CNDTRn, HTIF, TCIF, GIF])

    def save(self, ta_txt_file, flag_txt_file):
        f = open(ta_txt_file, 'w')
        self.signals_res = []
        repeat_res = []
        check = self.get_pairs()
        channels = []
        for prex in self.txt.prex:
            for c, end in check:
                self.construct(prex, c)
                self.signals_res.append(self.save_signals(repeat_res))
                saved = self.save_result(f, repeat_res, self.txt.result)
                tmp = [prex + end, prex]
                saved = saved | self.save_result(f, repeat_res,
                                                 self.txt.interrupt_res, tmp)
                if 'MCG' in ta_txt_file:
                    saved = saved | self.save_result(f, repeat_res,
                                                     self.txt.mode_result)
                if "DMA" in ta_txt_file:
                    channels.append(
                        self.save_dma(ta_txt_file, end, prex.strip('_')))
            f.write('--\n')

        signals = 0
        f.close()
        with open(flag_txt_file, 'w') as f:
            for r in self.signals_res:
                if len(r) > 0:
                    r = sorted(list(set(r)))
                    for l in r:
                        signals += 1
                        f.write("O,*->" + l)
                    if len(r) != 0:
                        f.write('--\n')
        with open(ta_txt_file[:-4] + '_dma.txt', 'w') as f:
            f.write('\n'.join(channels))
