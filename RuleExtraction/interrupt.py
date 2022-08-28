import re
from utils import field_reg_search


class ExtractInterrupt:

    def __init__(self, txt):
        self.txt = txt
        self.INTERRUPT_NUM = ''
        self.INTERRUPT_DMA_NUM = 'DMA'

    def is_enable(self, f):
        reg, field = f[0].split('[')[0], f[0].split('[')[1].strip(']')
        if self.txt.registers[reg][field]['title'].lower().find(
                'enable') == -1:
            return True

    def extract_interrupt_by_name(self, checked):
        interrupt_res = []
        all_signals = checked.copy()
        if 'INTENCLR' in self.txt.f2r:
            for field_name in self.txt.registers['INTENSET'].keys():
                disfield = 'INTENCLR[' + field_name + "]"
                setfield = 'INTENSET[' + field_name + "]"
                flagfield = 'INTFLAG[' + field_name + "]"
                if 'INTENCLR+' + field_name in self.txt.f2r:
                    interrupt_res.append([{
                        'trigger': [disfield + " = write1"],
                        "action": [disfield + " = 0", setfield + " = 0"]
                    }])
                if 'INTFLAG+' + field_name in self.txt.f2r:
                    checked.append(setfield)
                    checked.append(flagfield)
                    all_signals.append(flagfield)
                    interrupt_res.append([{
                        'trigger': [setfield + " = 1", flagfield + " = 1"],
                        'action': [flagfield + " = 1"],
                        'interrupt':
                        self.INTERRUPT_NUM
                    }])
                    interrupt_res.append([{
                        'trigger': [flagfield + " = write1"],
                        "action": [flagfield + " = 0"]
                    }])

        enable_pattern = re.compile("(ER\d*$)")
        for reg, fields in self.txt.registers.items():
            ends = re.findall(enable_pattern, reg)
            if len(ends) != 1:
                continue
            ends = ends[0]
            enable = reg[0:-len(ends)] + 'E' + ends[1:]
            disable = reg[0:-len(ends)] + 'D' + ends[1:]
            status = reg[0:-len(ends)] + 'M' + ends[1:]
            if enable not in self.txt.registers:
                continue
            if enable in self.txt.registers and disable in self.txt.registers and status not in self.txt.registers:
                status = reg[0:-len(ends)] + 'S' + ends[1:]
                if status not in self.txt.registers:
                    continue
            if status in checked:
                continue
            checked.append(status)
            if enable in self.txt.registers and disable in self.txt.registers and status in self.txt.registers:
                for field_name, field in fields.items():
                    if isinstance(field, dict) == False:
                        continue
                    cur_field = status + '[' + field_name + ']'
                    interrupt_res.append([{
                        'trigger': [enable + '[' + field_name + "] = write1"],
                        "action": [cur_field + " = 1"]
                    }])
                    interrupt_res.append([{
                        'trigger': [disable + '[' + field_name + "] = write1"],
                        "action": [cur_field + " = 0"]
                    }])
                    _status = reg[0:-len(ends)] + 'S' + ends[1:]
                    mask = reg[0:-len(ends)] + 'M' + ends[1:]
                    #print('a',_status, mask)
                    if _status not in self.txt.registers:
                        _status = _status[1:]
                    if _status not in self.txt.registers:
                        _status = 'SR'
                    if _status not in self.txt.registers:
                        _status = 'CSR'
                    #print(_status, mask)

                    if _status in self.txt.registers and mask in self.txt.registers and 'interrupt' in self.txt.registers[
                            mask]['title'].lower():
                        signal = _status + '[' + field_name + ']'
                        cur_field = mask + '[' + field_name + ']'
                        checked.append(cur_field)
                        checked.append(signal)
                        checked.append(enable)
                        checked.append(mask)
                        checked.append(_status)

                        all_signals.append(signal)
                        interrupt_res.append([{
                            'trigger': [signal + " = 1", cur_field + " = 1"],
                            'action': [signal + " = 1"],
                            'interrupt':
                            self.INTERRUPT_NUM
                        }])
        return all_signals, interrupt_res

    def extract_interrupt_corner_cases(self, res, score, field_name, field,
                                       cur_field):
        if len(res) == 0:
            tmp = field_name[:-2] + 'IF'
            if tmp not in self.txt.f2r:
                tmp = field_name[:-2] + 'F'
            if tmp in self.txt.f2r:
                res.append([self.txt.f2r[tmp] + "[" + tmp + "]"])
                score = 1.
            res = self.check_cur_field(res, cur_field)
        if len(res) == 0:
            for _reg in self.txt.registers.keys():
                if 'status' not in self.txt.registers[_reg]['title'].lower():
                    continue
                tmp = _reg + "+" + field_name
                if tmp in self.txt.f2r:
                    res.append([self.txt.f2r[tmp] + "[" + field_name + "]"])
                    score = 1.
                    break
            res = self.check_cur_field(res, cur_field)
        return res, score

    def check_cur_field(self, res, cur_field):
        final_res = []
        for tmp in res:
            _tmp = tmp.copy()
            for a in _tmp:
                if a.find('[') == -1 or a == cur_field:
                    tmp.remove(a)
            if len(tmp) != 0:
                final_res.append(tmp)
        return final_res

    def extract_interrupt(self, checked=[]):
        all_signals, interrupt_res = self.extract_interrupt_by_name(checked)
        error_enables = {}
        for reg, fields in self.txt.registers.items():
            for field_name, field in fields.items():
                if isinstance(field, dict) == False:
                    continue
                field['title'] = field['title'].lower()
                cur_field = reg + '[' + field_name + ']'
                if reg in checked or cur_field in checked:
                    continue
                if (field['title'].find('interrupt') == -1
                        and ('GC' not in field
                             or field['GC'].find('interrupt request') == -1)):
                    continue
                if re.search('enable|mask', field['title']) == None:
                    continue
                if re.search('pio controller|additional interrupt',
                             self.txt.registers[reg]['title']) != None:
                    continue
                res = []
                score = 0.
                if 'GC' in field and field['GC'] != '':
                    sentences = field['GC'].split('-')
                    for s in sentences:
                        tmp, score = field_reg_search(s, self.txt, None)
                        if len(tmp) != 0:
                            res.append(tmp)
                    res = self.check_cur_field(res, cur_field)
                if len(res) == 0:
                    for k in ['0', '1']:
                        if k in field:
                            v = field[k]
                            if 'C' in v.keys():
                                tmp, score = field_reg_search(
                                    v['C'], self.txt, None)
                                if len(tmp) != 0:
                                    res.append(tmp)
                                    break
                    res = self.check_cur_field(res, cur_field)
                res, score = self.extract_interrupt_corner_cases(
                    res, score, field_name, field, cur_field)
                #print('2', res, score)
                if score < 1.:
                    #print(field['title'].replace('interrupt enable','').strip())
                    error_enables[field['title'].replace(
                        'interrupt enable', '').strip()] = field_name
                    print('unfinded, ', error_enables)
                    continue
                #print(field,'interrupt enable',res)
                #print('interrupt', res, field, cur_field)
                for pair in res:
                    if len(pair) == 1:
                        if field['title'].find('signal') != -1:
                            cur_field = pair[0]
                            pair[0] = reg + '[' + field_name + ']'
                        all_signals.append(pair[0])
                        interrupt_res.append([{
                            'trigger': [pair[0] + " = 1", cur_field + " = 1"],
                            'action': [pair[0] + " = 1"],
                            'interrupt':
                            self.INTERRUPT_NUM
                        }])
                    elif len(pair) >= 2:
                        signals = []
                        enables = []
                        dma = False
                        for idx in pair:
                            if re.search(
                                    'DMA|DIRS', idx
                            ) != None and self.txt.config.chip_name != 'Ethernet':
                                dma = idx
                            else:
                                if idx.find('EN') != -1 or idx.find(
                                        'IER') != -1:
                                    enables.append(idx)
                                else:
                                    all_signals.append(idx)
                                    signals.append(idx)
                        if not dma:
                            if cur_field.find(
                                    'DMA'
                            ) != -1 and self.txt.config.chip_name != 'Ethernet':
                                dma = cur_field
                                cur_field = ""
                        #import pdb
                        #pdb.set_trace()
                        #print(signals, dma, cur_field, enables)
                        if dma:
                            for signal in signals:
                                if cur_field != "":
                                    interrupt_res.append([{
                                        'trigger': [
                                            cur_field + " = 1",
                                            signal + " = 1", dma + " = 1"
                                        ],
                                        'action': [signal + " = 1"],
                                        'interrupt':
                                        self.INTERRUPT_DMA_NUM
                                    }])
                                    interrupt_res.append([{
                                        'trigger': [
                                            cur_field + " = 1",
                                            signal + " = 1", dma + " = 0"
                                        ],
                                        'action': [signal + " = 1"],
                                        'interrupt':
                                        self.INTERRUPT_NUM
                                    }])
                                else:
                                    interrupt_res.append([{
                                        'trigger':
                                        [signal + " = 1", dma + " = 1"],
                                        'action': [signal + " = 1"],
                                        'interrupt':
                                        self.INTERRUPT_DMA_NUM
                                    }])
                            for enable in enables:
                                #print(interrupt_res,signals,pair)
                                interrupt_res[-2][0]['trigger'].append(enable +
                                                                       " = 1")
                                interrupt_res[-1][0]['trigger'].append(enable +
                                                                       " = 1")
                        else:
                            for signal in signals:
                                interrupt_res.append([{
                                    'trigger':
                                    [cur_field + " = 1", signal + " = 1"],
                                    'action': [signal + " = 1"],
                                    'interrupt':
                                    self.INTERRUPT_NUM
                                }])
                            for enable in enables:
                                interrupt_res[-1][0]['trigger'].append(enable +
                                                                       " = 1")
                #print(interrupt_res, field)
                #print('===')
        #print(len(interrupt_res))
        return interrupt_res, all_signals

    def get_interrupt(self):
        checked = []
        interrupt_res = []
        signals = []
        if len(self.txt.interrupts) != 0:
            for interrupt in self.txt.interrupts:
                f, _ = field_reg_search(interrupt[0], self.txt, None)
                e, _ = field_reg_search(interrupt[1], self.txt, None)
                if len(e) == 0 and len(interrupt) == 4:
                    e = f
                if len(f) != 1 or len(e) != 1:
                    continue
                checked.append(e[0])
                checked.append(f[0])
                if self.is_enable(f):
                    signals.append(f[0])
                if self.is_enable(e):
                    signals.append(e[0])

                if interrupt[2].isnumeric():
                    self.INTERRUPT_NUM = interrupt[2]
                else:
                    self.INTERRUPT_NUM = ''
                if '>' in interrupt[1]:
                    a, b, c = interrupt[1].split(' ')
                    interrupt_res.append([{
                        'trigger': [[b, e[0], c], f[0] + " = 1"],
                        'action': [f[0] + " = 1"],
                        'interrupt':
                        self.INTERRUPT_NUM
                    }])
                elif len(interrupt) == 4:
                    d, _ = field_reg_search(interrupt[3], self.txt, None)
                    #interrupt_res.append({'signal':f[0], 'enable':e[0], 'dma':d[0]})
                    #print(d, interrupt[3])
                    dma = ""
                    label = self.INTERRUPT_NUM
                    local = []
                    local_without_dma = []
                    for _d in d:
                        checked.append(_d)
                        if 'DMA' in _d:
                            dma = _d
                            label = self.INTERRUPT_DMA_NUM
                        else:
                            local_without_dma.append(_d + " = 1")
                        local.append(_d + " = 1")
                    local.append(f[0] + " = 1")
                    local_without_dma.append(f[0] + " = 1")
                    if e != f:
                        local.append(e[0] + " = 1")
                        local_without_dma.append(e[0] + " = 1")
                    interrupt_res.append([{
                        'trigger': [],
                        'action': [f[0] + " = 1"],
                        'interrupt': label
                    }])
                    interrupt_res[-1][0]['trigger'].extend(local)
                    if label == self.INTERRUPT_DMA_NUM and e != f:
                        if interrupt[3].find('=') != -1:
                            interrupt_res.append([{
                                'trigger': [dma + " = 0"],
                                'action': [f[0] + " = 1"],
                                'interrupt':
                                self.INTERRUPT_NUM
                            }])
                            interrupt_res[-1][0]['trigger'].extend(
                                local_without_dma)
                        else:
                            interrupt_res.append([{
                                'trigger': [],
                                'action': [f[0] + " = 1"],
                                'interrupt':
                                self.INTERRUPT_NUM
                            }])
                            interrupt_res[-1][0]['trigger'].extend(
                                local_without_dma)
                else:
                    interrupt_res.append([{
                        'trigger': [f[0] + " = 1", e[0] + " = 1"],
                        'action': [f[0] + " = 1"],
                        'interrupt':
                        self.INTERRUPT_NUM
                    }])
        #print(interrupt_res)
        res, _signals = self.extract_interrupt(checked)
        signals.extend(_signals)
        interrupt_res.extend(res)
        self.txt.interrupt_res = interrupt_res
        self.txt.signals = signals
