import re


class ExtractHardwareSignals:

    def __init__(self, txt, signals):
        self.txt = txt
        self.signals = signals

    def defined_by_hardware(self, tmp, cur_field, field):
        check = True
        reg, field_name = cur_field.split('[')[0], cur_field.split(
            '[')[1].strip(']')

        if re.search('sspecific|' + '|'.join(self.signals.error_signal),
                     field['title'].lower()) != None:
            return check
        if 'set and cleared by hardware' in tmp or (
                'set by hardware' in tmp
                and 'or by hardware' in tmp) or ('cleared by hardware' in tmp
                                                 and 'or by hardware' in tmp):
            #print(field['GC'],cur_field)
            #pdb.set_trace()
            self.txt.signals.append(cur_field + " = *")
            check = False
        elif ' set by hardware' in tmp and ('reset by hardware' in tmp
                                            or 'cleared by hardware' in tmp):
            self.txt.signals.append(cur_field + " = *")
            check = False
        elif 'set and cleared by software' in tmp and 'by hardware' in tmp:
            #print(field['GC'])
            #pdb.set_trace()
            #self.txt.signals.append(cur_field + " = 0/1")
            check = True
        elif ('cleared by hardware' in tmp or 'reset by hardware' in tmp):
            #print(field['GC'])
            #pdb.set_trace()
            if 'set by software' in tmp or 'software' not in tmp:
                self.txt.signals.append(cur_field + " = 0")
            else:
                self.txt.signals.append(cur_field + " = *")
            check = False
        elif 'set by hardware' in tmp:
            #print(field['GC'])
            #pdb.set_trace()
            if 'cleared by software' in tmp or 'software' not in tmp:
                self.txt.signals.append(cur_field + " = 1")
            else:
                self.txt.signals.append(cur_field + " = *")
            check = False
        elif 'GC' in field and 'Begins the calibration' in field['GC']:
            self.txt.signals.append(cur_field + " = 0")
            check = False
        return check

    def extract_signals(self):
        for reg, fields in self.txt.registers.items():
            if re.search('|'.join(self.signals.data_reg),
                         fields['title']) != None:
                self.txt.signals.append(reg + " = *")

            for field_name, field in fields.items():
                cur_field = reg + '[' + field_name + ']'
                if ('GC' in field and 'set and cleared by software'
                        in field['GC'].lower()):
                    continue
                #if cur_field in self.txt.signals:
                #    continue
                check = True
                #print(cur_field, self.txt.signals)
                if check and 'title' in field:
                    field['title'] = field['title'].lower()
                    if 'counter' not in field['title'] and re.search(
                            '|'.join(self.signals.non_conditions +
                                     self.signals.transmit +
                                     self.signals.receive),
                            field['title']) != None:
                        check = False
                    if check and re.search('|'.join(self.signals.conditions),
                                           field['title']) != None:
                        self.txt.signals.append(cur_field)
                        check = False
                if check and 'GC' in field and field['GC'] != '':
                    tmp = field['GC'].lower()
                    check = self.defined_by_hardware(tmp, cur_field, field)
