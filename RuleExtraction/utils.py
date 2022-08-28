import re


class Config:

    def __init__(self):
        self.register_pattern = re.compile(
            "^([A-Za-z0-9\_]+)\s[fF]ield\s[dD]escriptions?")
        self.name_pattern = re.compile("\(([A-Za-z0-9\_]+)\)")
        self.field_bit_pattern = re.compile("^([0-9-]{1,7})\s")
        self.field_pattern = re.compile(
            "([A-Z]{1,10}n?x?[0-9]{0,6}[\[A-Z0-9\_\]]{0,}|transmit[\-]buffer|shift[\s\-]register|receive[\-]buffer)[\s,\.\/\)]"
        )

        self.merge_pos_tag = [('ISO7816E', 'ISO_7816E'),
                              ('a software', 'software'),
                              ('receiver data register', 'receive buffer'),
                              ('DMA transfer', 'DMA-transfer'),
                              ('The assertion', 'the result'),
                              ('Receive buffer', 'receive buffer'),
                              ('the built in', 'the build-in'),
                              ('the UART data register', 'D'),
                              ('FIFO/buffer', 'buffer'),
                              ('FIFO/Buffer', 'buffer'), ('zero', '0'),
                              ('In case', 'In-case'),
                              ('read only', 'read-only'),
                              ('the transmit buffer', 'the transmit-buffer'),
                              ('the receive buffer', 'the receive-buffer'),
                              (' 7816E ', ' ISO_7816E '),
                              ('ISO-7816', 'ISO_7816E'),
                              ('datawords that are in', 'datawords in')]
        self.remove_key = [
            'FIFO', 'UART', 'NACKS', 'DMA', 'LIN', 'USART', 'A', 'An', 'NACK',
            'I', 'IN', 'The', 'T', 'PLL', 'PLL2'
        ]

        self.delete_tag = [
            'preamble ,', 'and then doing one of the following',
            'regardless of', 'some point in time since', 'Assuming',
            'Alternatively', 'Even if', 'Additionally', 'Determines',
            'for example', 'since', 'with no'
        ]
        self.channel_pattern = re.compile("[Cc]hannel (\d{1,2})[^-]")
        self.chip_name = ""


class Signals:

    def __init__(self):
        self.transmit = [
            'transmit data register', 'transmit', 'tx', 'transmission buffer',
            'transmission registers', 'transfer'
        ]
        self.receive = ['read data register', 'receive', 'rx', 'conversion']
        self.data_reg = ['data status register']
        self.flag_signal = [
            'matched', 'counter', 'increment', ' lock', 'sspecific'
        ]
        self.signal_certain_1_signal = [
            'end', 'start', 'ready', 'complete', 'finished', 'stabilized',
            'acknowledge flag'
        ]
        self.signal_certain_0_signal = ['stop', ' busy', ' reset']
        self.buffer_signal = ['full', 'empty', 'ready', 'end of conversion'
                              ]  #,'receive status','transmit status']
        self.error_signal = [
            'underflow', 'overflow', 'error', 'missed', 'failure', 'security',
            'lost', 'overrun', 'alarm', 'noise', 'underrun', 'break',
            'invalid', 'busy', 'fault', 'timeout', 'idle', 'overflow',
            'polarity'
        ]
        self.conditions = [
            'start', 'stop', 'fifo counter', 'counter value', 'ready',
            'reset signal', 'finish', 'acknowledge flag', 'busy', ' reset'
        ]
        self.non_conditions = [
            'graceful', 'delimiter', 'stopen', 'clock ready', 'repeat',
            'select', 'timer start', 'enable', 'stop mode', 'start mode',
            'abort', 'startup', 'disable', 'mask'
        ]


def cal_ED(s1, f2r):
    import Levenshtein as ED
    _min = 100
    for s2 in f2r:
        _min = min(_min, ED.distance(s1, s2))
        #print(s1, s2, ED.distance(s1, s2), 1. - _min * 1. / len(s1))
    return 1. - min(1., _min * 1. / len(s1))


def field_reg_search(sent, txt, add_field):
    entities = re.findall(txt.config.field_pattern, sent + ' ')
    entities = [key for key in entities if key not in txt.config.remove_key]
    entities = list(set(entities))
    if len(entities) != 1 and 'D' in entities:
        entities.remove('D')
    if len(entities) == 0:
        return [], 0.
    res = []
    score = 1.
    for word in entities:
        if word.find('_') != -1 and word not in txt.f2r and word.find(
                '[') == -1:
            word = word.split('_')[-1]
        if word.find('[') != -1:
            # field name
            word_field = word.split('[')[1].strip(']')
            # combine register name and field name
            word_all = word.split('[')[0] + '+' + word_field
            if word_all in txt.f2r:
                res.append(word)
            elif word_field in txt.f2r:
                res.append(txt.f2r[word_field] + "[" + word_field + "]")
        elif word in txt.f2r:
            if txt.f2r[word] != '':
                res.append(txt.f2r[word] + "[" + word + "]")
            else:
                if add_field != None and txt.f2r[add_field] == word:
                    res.append(word + "[" + add_field + "]")
                else:
                    res.append(word)
        else:
            score *= 0.6 * cal_ED(word, txt.f2r)
    return res, score


def get_register_type(r1, r2):
    r1 = r1.lower()
    if r1.find('linkk') != -1:
        return 'L'
    elif r2.find('MUST CHECK') != -1:
        return 'S'
    elif r1.find('status') != -1:
        return 'O'
    elif r1.find('control') != -1 or r1.find('enable') != -1 or r1.find(
            'disable') != -1 or r1.find('mask') != -1 or r1.find(
                'configuration') != -1 or r2.find('configuration') != -1:
        return 'C'
    elif r1.find('extended data') != -1:
        return 'ED'
    elif r1.find('current timer value') != -1:
        return 'P'
    elif r1.find('rx fifo register') != -1 or r1.find(
            'receiver holding') != -1 or r1.find(
                'receive holding') != -1 or r1.find('receive data') != -1:
        return 'R'
    elif r1.find('tx fifo register') != -1 or r1.find(
            'transmit holding') != -1 or r1.find('transmit data') != -1:
        return 'T'
    elif r1.find('offset') != -1 or r1.find('injected') != -1:
        return 'O'
    elif r1.find('data') != -1:
        return 'D'
    else:
        return 'O'


def replacement(config, data, field=None):
    for k, v in config.merge_pos_tag:
        data = data.replace(k, v)

    for delete in config.delete_tag:
        idx = data.find(delete)
        if idx != -1:
            res = re.search(r'\.|,', data[idx:])
            end = -1
            if res != None:
                end = res.start()
            data = data[:idx] + data[end:]
            data = data.strip('. ,')

    data = data.replace(',', ' , ')
    data = data.replace('(', ' ( ')
    data = data.replace(')', ' ) ')
    if field != None:
        data = re.sub(
            r'([Tt]his|[Tt]he) (interrupt|field |bit |signal|register field |value in the register|register)',
            field + " ", data)
        data = re.sub(r'([Ii]t is|until) cleared by', field + " is cleared by",
                      data)
        data = data.replace('1 to it', '1 to ' + field)
        data = data.replace('is zero', 'is 0')
        data = data.replace('is one', 'is 1')
    return data.replace("=", " is ")