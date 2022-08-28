import copy
import re
from utils import Signals, field_reg_search


class ExtractCA:

    def __init__(self, txt, signals):
        import os
        import nltk
        from nltk.tag import StanfordPOSTagger
        from nltk.parse.stanford import StanfordParser
        from nltk.parse.stanford import StanfordDependencyParser
        self.txt = txt
        self.signals = signals
        path = os.path.abspath(".") + "/"
        stanford_pos_dir = path + 'models/stanford/'
        eng_model_filename = stanford_pos_dir + 'models/english-bidirectional-distsim.tagger'
        my_path_to_jar = stanford_pos_dir + 'stanford-postagger.jar'
        self.stanford_tagger = StanfordPOSTagger(
            model_filename=eng_model_filename, path_to_jar=my_path_to_jar)

        eng_model_path = stanford_pos_dir + "stanford-parser-4.0.0-models/edu/stanford/nlp/models/lexparser/englishPCFG4.4.0.ser.gz"
        my_path_to_models_jar = stanford_pos_dir + "stanford-corenlp-4.4.0-models.jar"
        my_path_to_jar = stanford_pos_dir + "stanford-corenlp-4.4.0.jar"
        self.stanford_parser = StanfordParser(
            model_path=eng_model_path,
            path_to_models_jar=my_path_to_models_jar,
            path_to_jar=my_path_to_jar)
        self.dep_parser = StanfordDependencyParser(
            model_path=eng_model_path,
            path_to_models_jar=my_path_to_models_jar,
            path_to_jar=my_path_to_jar)

        sub_grammer = """
                        NP: {<-LRB-><NN.*><-RRB->}
                        {<DT><VB.*>?<NN.*>+}
                        {<DT>?<JJ><HYPH><NN.*>+}
                        {<NN>+<-LRB-><NN.*><-RRB->}
                        {<NNP><JJ><NN>}
                        {<\(><NNP>+<\)>}
                        {<DT>?<NN.*><\W><JJ>+<NN.*>+} 
                        {<DT>?<CD>*<JJ>*<NN.*>*}
                        {<NN.*>+}
                        NP2: {<NP><FW><FW>}
                        {<NP><VBN><IN><ADD|NP>}
                        {<NP><CD>}
                        {<NP>+(<IN|VBG|VBN><NP>)?(<VBG|IN|VBN><NP>)?}
                        {<NP|\(|\)|-LRB-|-RRB-|PRP>+}
                        CLEAR: {<TO><VB><NP2>}
                                {^<VBG><NP2><TO><NP2><VBZ><NP2>$}
                        BESTSENT: {<NP2><MD>?<VB|VBZ|VBP><RB>?<CD|VB.*|JJ|NP2>}
                                    {<NP2><VB|VBZ|VBP><JJR><TO><NP2>}
                        Relation: {<BESTSENT>(<CC><BESTSENT>)+}
                        ASKSENT: {<VBD><NP2>}
                                {<RB><VB><TO>?<NP2>}
                                {<VBG><NP2>$}
                                {<VBG><CD|NP2><IN|TO><NP2>}
        """
        self.cp_sent = nltk.RegexpParser(sub_grammer)

        self.adjust_pos_tag = [('DMA-request', 'NN'), ('reset', 'VBN'),
                               ('To', 'TO'), ('to', 'TO'), ('writing', 'VBG'),
                               ('interrupt', 'NN'),
                               ('at', 'ON'), ('read', 'VB'), ('clear', 'VB'),
                               ('equal', 'JJR'), ('greater', 'JJR'),
                               ('following', 'NN'), ('return', 'VBZ'),
                               ('returns', 'VBZ'), ('enable', 'VB'),
                               ('the', 'DT'), ('clearing', 'VBG'),
                               ('reading', 'VBG'), ('DMA', 'NP'),
                               ('set', 'VBN')]
        self.tagger_error = [('ISO7816E', 'ISO_7816E')]
        self.keyword_when = [
            'when', 'When', 'If', 'if', 'while', 'While', 'since', 'upon'
        ]
        self.keyword_indicate = [' indicates']

        self.value_pattern = re.compile("[\s](\d+)[^-\d]")

        self.transform_n_re = r'[wW]rit[eing]{1,4} (a )?(logic )?(1 )?to|read|set|valid| clear|assert|is zero|enable|disable'

        self.mapping_table = {
            'write': 'write',
            'Writing': 'write1',
            'writing': 'write1',
            'read': 'read',
            'set': '1',
            'not valid': '0',
            'cleared': '0',
            'clear': '0',
            'clears': '0',
            'deasserted': '0',
            'assert': '1',
            'prevented': '0',
            'blocked': '0',
            'enabled': '1',
            'disable': '0'
        }
        self.transform_v_tag = ['is written to', ' is ']
        self.transform_c_tag = [(' greater than', ' > '),
                                (' more than', ' > '), (' equal to', ' = '),
                                (' less than', ' < ')]

    def get_pos_tag(self, data):
        for i in range(len(data)):
            if (data[i] == '-LRB-'):
                data[i] = '('
            elif (data[i] == '-RRB-'):
                data[i] = ')'
        sent = self.stanford_tagger.tag(data)
        sent = [list(s) for s in sent]
        for idx, x in enumerate(sent):
            for word, ori in self.tagger_error:
                if x[0].find(word) != -1:
                    x[0] = x[0].replace(word, ori)
            for word, pos in self.adjust_pos_tag:
                if x[0] == word:
                    sent[idx][1] = pos
            entities = re.findall(self.txt.config.field_pattern, x[0] + '.')
            if len(entities) == 1:
                sent[idx][1] = "NN"
        sent = [tuple(s) for s in sent]
        return sent

    def get_chunk_nltk(self, data):
        data = data.replace('=', ' is ')
        data = re.split(r',|\.|:|\s', data)
        sent = self.get_pos_tag(data)
        return self.cp_sent.parse(sent)

    def get_short_sent(self, data, field_name):
        if data == "":
            return None
        res = []
        chunks = self.get_chunk_nltk(data)
        score = 1.
        relation = False
        for chunk in chunks.subtrees():
            if chunk.label() == 'Relation':
                relation = True
                for cc in chunk:
                    if type(cc) != tuple and (cc.label() == 'BESTSENT'):
                        _t = self.equation_transform(
                            ' '.join([term[0] for term in cc.leaves()]),
                            field_name)
                        if _t != None:
                            res.extend(_t[0])
                            score *= _t[1]
                        else:
                            score *= 0.3
                    else:
                        if cc[0] == 'or':
                            res.append('||')
                        elif cc[0] == 'and':
                            res.append('&&')
                break
            elif chunk.label() == 'BESTSENT':
                _t = self.equation_transform(
                    ' '.join([term[0] for term in chunk.leaves()]), field_name)
                if _t != None and len(_t[0]) != 0:
                    res.extend(_t[0])
                    score *= _t[1]
                else:
                    if 'or' not in data:
                        score *= 0.4
        if relation == False and len(res) > 1:
            score *= 0.8

        if len(res) == 0:
            return None
        return res, score

    def equation_transform(self, sent, field_name):
        sent = ' ' + sent.strip(', ') + " ."

        def equation_equ():
            for word in self.transform_v_tag:
                idx = sent.find(word)
                if idx == -1:
                    continue
                res = []
                entities, _s = field_reg_search(sent, self.txt, field_name)
                value = re.findall(self.value_pattern, sent)
                if len(entities) != len(value) or len(value) != 1:
                    continue
                #print(word, sent, len(sent.split(" ")),value)
                if (word == " is ") and (
                        re.search('more than|equal to|less than', sent) != None
                        or (len(sent.split(" ")) > 10)):
                    continue
                res.append(entities[0] + " = " + value[0])
                return res, 1.0
            return None

        def equation_non_equ():
            res = []
            tags = ""
            score = 1.
            for word, tag in self.transform_c_tag:
                if sent.find(word) == -1:
                    continue
                idx = sent.find(word)
                tags += tag
            if tags != "":
                entities1, _s1 = field_reg_search(sent[0:idx] + '.', self.txt,
                                                  field_name)
                entities2, _s2 = field_reg_search(sent[idx:] + '.', self.txt,
                                                  field_name)
                if _s2 == 0:
                    value = re.findall(self.value_pattern, sent[idx:])
                    if len(value) == 1:
                        entities2 = value[0]
                        _s2 = 1.
                score *= _s1 * _s2
                if score != 0:
                    if tags == ' = ':
                        res.extend([
                            " ".join(entities1) + " = " + " ".join(entities2)
                        ])
                    else:
                        res.extend(
                            [[tags, " ".join(entities1), " ".join(entities2)]])
                #print(sent, res, score)
                if len(res) != 0:
                    return res, score
            return None

        def get_verb(data, noun):
            data = re.split(r',|\.|:|\s', data)
            pos_sent = self.get_pos_tag(data)
            sents = self.dep_parser.tagged_parse_sents([pos_sent])
            verbs = []
            for parses in sents:
                for parse in parses:
                    for relation in list(parse.triples()):
                        if re.search('nsubj|obl|obj', relation[1]) != None:
                            if relation[2][0] in noun or relation[2][
                                    1] == 'CD' or relation[2][
                                        0] == 'bit' or relation[2][
                                            0] == 'field':
                                return relation[0][0]
            return verbs

        def equation_mapping():
            score = 1.
            if len(re.findall(self.transform_n_re, sent)) != 1:
                return None
            res = []
            entities, _s = field_reg_search(sent, self.txt, field_name)
            if len(entities) == 0:
                return None
            score *= 1. / len(entities) * _s
            value = ''

            for eid in range(0, len(entities)):
                verb = get_verb(sent, entities[eid])
                #print('verb:', sent, entities[eid], verb)
                if len(verb) == 0 or (verb not in self.mapping_table and
                                      'not ' + verb not in self.mapping_table):
                    continue
                if 'not ' + verb in self.mapping_table:
                    value = self.mapping_table['not ' + verb]
                elif 'not ' + verb in sent or 'not been' + verb in sent:
                    value = str(int(int(self.mapping_table[verb]) != 1))
                else:
                    value = self.mapping_table[verb]
                #print('result:', sent, entities[eid], value)
            if value == '':
                return None
            start = 0
            for eid in range(0, len(entities)):
                end = -1
                if (eid + 1) < len(entities):
                    end = sent.find(entities[eid + 1], start)
                res.append(entities[eid] + " = " + value)
                if eid < len(entities) - 1:
                    if sent.find(" or ", start, end) != -1:
                        res.append(" || ")
                    elif sent.find(" and ", start, end) != -1 or sent.find(
                            ",", start, end) != -1:
                        res.append(" && ")
                    else:
                        score *= 0.6
                    start = end

            if sent.find(" and ", start) != -1:
                score *= 0.55
            #print('final', sent, res, score)
            return res, score

        ans = equation_equ()
        if ans != None:
            return ans

        ans = equation_non_equ()
        if ans != None:
            return ans

        ans = equation_mapping()
        if ans != None:
            return ans
        return [], 0.0

    def identification_by_name(self, field_name):
        if field_name not in self.txt.f2r or field_name + 'F' in self.txt.f2r:
            return [], []
        tmp = field_name + 'C'
        if tmp not in self.txt.f2r:
            tmp = field_name[:-1] + 'C'
        if tmp not in self.txt.f2r:
            tmp = field_name[:-1] + 'CF'
        if tmp not in self.txt.f2r:
            tmp = field_name + 'CF'
        if tmp in self.txt.f2r and self.txt.f2r[
                tmp] in self.txt.registers and 'clear register' in self.txt.registers[
                    self.txt.f2r[tmp]]['title'].lower():
            tmp, _ = field_reg_search(tmp, self.txt, tmp)
            field_name, _ = field_reg_search(field_name, self.txt, field_name)
            return [[tmp[0] + " = write1"],
                    1.0], [[field_name[0] + ' = 0', tmp[0] + ' = 0'], 1.0]
        return [], []

    def identification_by_tag(self, data, field_name):
        when, then = [], []
        if data == "" or ' clear' not in data:
            return when, then
        if 'until' in data:
            data = data[data.find('until'):]
        chunks = self.get_chunk_nltk(data)
        clear_check = False
        for chunk in chunks.subtrees():
            if chunk.label() == 'CLEAR':
                subsent = ' '.join([term[0] for term in chunk.leaves()])
                entities, score = field_reg_search(subsent, self.txt,
                                                   field_name)
                if len(entities) == 2:
                    idx = subsent.index('clear')
                    _w = subsent[:idx]
                    _t = subsent[idx:subsent.index('flag')]
                    when.extend(self.equation_transform(_w, field_name))
                    then.extend(self.equation_transform(_t, field_name))
                    continue
                if len(entities) != 1:
                    continue
                clear_check = True
                _t = [[entities[0] + " = 0"], score]
                then.extend(_t)
                if re.search('[wW]riting', subsent) != None:
                    _w = self.equation_transform(
                        subsent[:subsent.find('clear')], field_name)
                    when.extend(_w)
            elif chunk.label() == 'ASKSENT' or chunk.label() == 'BESTSENT':
                subsent = ' '.join([term[0] for term in chunk.leaves()])
                entities, _s = field_reg_search(subsent, self.txt, field_name)
                if len(entities) == 0:
                    entities, _s = field_reg_search(data, self.txt, field_name)
                    if len(entities) != 1:
                        continue
                    subsent += " to " + entities[0]
                _w = self.equation_transform(subsent, field_name)
                if _w == None or _w[1] < 1.:
                    continue
                if ' clear' in subsent:
                    then.extend(_w)
                else:
                    if chunk.label() == 'ASKSENT' and clear_check:
                        when = _w
                    else:
                        when.extend(_w)
        if (len(when) == 2 and len(then) == 2 and len(when[0]) != 0
                and len(then[0]) != 0):
            return when, then
        return [], []

    def identification_by_model(self, sent, field_name):

        def delete_tree(chunk):
            for ind, leaf in reversed(list(enumerate(chunk.leaves()))):
                postn = chunk.leaf_treeposition(ind)
                parentpos = postn[:-1]
                while parentpos and len(chunk[parentpos]) == 1:
                    postn = parentpos
                    parentpos = postn[:-1]
                del chunk[postn]

        def get_chunk_stanford(data, field_name):
            sub_data = re.split(r'\.|:|\s', data)
            num = 0
            for keyword in self.keyword_when:
                num += sub_data.count(keyword)
            if num == 0:
                return [], []
            score = 1. / num

            pos_sent = self.get_pos_tag(sub_data)
            when = []
            then = []
            sent = self.stanford_parser.tagged_parse(pos_sent)
            for myListiterator in sent:
                for s in myListiterator:
                    for tree in s.subtrees(
                            filter=lambda x: x.label() == 'SBAR'):
                        key = tree.leaves()[0]
                        if key in self.keyword_when:
                            _t = self.get_short_sent(' '.join(tree.leaves()),
                                                     field_name)
                            if _t == None:
                                _t = self.equation_transform(
                                    ' '.join(tree.leaves()), field_name)
                            if _t != None:
                                when.extend((_t[0], _t[1] * score))
                            else:
                                break
                            delete_tree(tree)
                            _t = self.get_short_sent(' '.join(s.leaves()),
                                                     field_name)
                            if _t == None:
                                _t = self.equation_transform(
                                    ' '.join(tree.leaves()), field_name)
                            if _t != None:
                                then.extend((_t[0], _t[1] * score))
                            break
                            #continue

            return when, then

        when, then = get_chunk_stanford(sent, field_name)
        if len(when) != 0:
            return when, then
        else:
            for keyword in self.keyword_indicate:
                end = sent.find(keyword)
                if end == -1:
                    continue
                data = sent.replace(keyword, ' is equal to ')
                then = self.equation_transform(data, field_name)
                if then != None:
                    return [[], 1.0], then
            return [], []

    def extract(self,
                sequence,
                field_name,
                threshold=1.0,
                trigger_only=False,
                cur_field=None):
        sents = re.split(r'\.|:', sequence)
        data = []
        for sent in sents:
            sent = sent.strip(" ")
            if sent == "" or sent.count(',') > 3 or len(
                    re.findall('[iI]f|[Ww]hen|[Bb]efore|[Aa]fter', sent)) > 1:
                continue
            entities, _ = field_reg_search(sent, self.txt, field_name)
            if len(entities) == 0:
                continue
            if trigger_only == False:
                _when, _then = self.identification_by_tag(sent, field_name)
                if len(_when) == 0:
                    _when, _then = self.identification_by_model(
                        sent, field_name)
            else:
                if len(re.findall('|'.join(self.keyword_when), sent)) != 0:
                    return data
                _when, _then = self.equation_transform(sent, field_name), [[],
                                                                           1.0]
                if _when != None and len(_when[0]) == 1:
                    _w = _when[0]
                    if type(_w[0]) != list:
                        w, _ = field_reg_search(_w[0], self.txt, field_name)
                        if (w == cur_field and 'write' not in _w[0]
                                and 'read' not in _w[0]):
                            #print('exclude same entitie',_when, _then, _w)
                            _when = (_when[0], _when[1] * 0.6)

            if _when == []:
                continue
            if len(_when) > 1:
                _when, when_score = _when[0], _when[1]
            if len(_then) > 1:
                _then, then_score = _then[0], _then[1]
            else:
                import pdb
                pdb.set_trace()
            if min(when_score, then_score) < threshold:
                continue
            if len(_when) == 0 and len(_then) != 0:
                data.append({'trigger': ['ALL'], 'action': _then})
            elif trigger_only and len(_when) != 0 and len(_then) == 0:
                data.append(_when)
            elif len(_when) != 0 and len(_then) != 0:
                if len(_when) == 1:
                    if type(_when[0]) != list:
                        w, _ = field_reg_search(_when[0], self.txt, field_name)
                        t, _ = field_reg_search(_then[0], self.txt, field_name)
                        if (w == t and 'write' not in _when[0]
                                and 'read' not in _when[0]):
                            #print('exclude same entitie',_when, _then)
                            continue
                data.append({'trigger': _when, 'action': _then})
        return data

    def extract_TA(self):
        result = []
        extracted_registers = copy.deepcopy(self.txt.registers)
        for reg, fields in self.txt.registers.items():
            r_type = self.txt.reg_type[reg]
            if (r_type == 'C'):
                continue
            for field_name, field in fields.items():
                _when, _then = self.identification_by_name(field_name)
                if len(_when) != 0:
                    extracted_registers[reg][field_name]['EGTA'] = [{
                        'trigger':
                        _when[0],
                        'action':
                        _then[0]
                    }]
                    result.append(extracted_registers[reg][field_name]['EGTA'])
                if isinstance(field, dict) == False or re.search(
                        r'enable|disable|mask', field['title']) != None:
                    continue
                check_dr = False
                name = reg + '[' + field_name + ']'
                for k, v in field.items():
                    if k == 'GC':
                        sent = v
                    elif isinstance(v, dict) and 'C' in v.keys():
                        sent = v['C']
                    else:
                        continue
                    data = self.extract(sent, field_name)
                    if len(data) != 0:
                        if len(data[0]['trigger']) == 3:
                            check_dr = True
                        extracted_registers[reg][field_name]['EGTA'] = data
                        result.append(data)
                    elif isinstance(v, dict) and 'C' in v.keys():
                        data = self.extract(sent, field_name, 0.9, True,
                                            [name])
                        if len(data) != 0:
                            check_dr = True
                            trigger = data[0]
                            if type(trigger) != list and re.search(
                                    r'\[|\]|>|<', trigger[0]) == None:
                                _reg, _v = trigger[0].split(
                                    ' = ')[0], trigger[0].split(' = ')[1]
                                #import pdb
                                #pdb.set_trace()
                                if field_name in self.txt.registers[_reg]:
                                    trigger = [name + ' = ' + _v]
                            action = [name + ' = ' + k]
                            if 'clear' in field['title'].lower():
                                tmp = trigger
                                trigger = action
                                action = tmp
                            extracted_registers[reg][field_name][k]['ETA'] = [{
                                'trigger':
                                trigger,
                                'action':
                                action
                            }]
                            result.append([{
                                'trigger': trigger,
                                'action': action
                            }])
                if check_dr:
                    continue
                conditions = []
                if name in self.txt.read_clear:
                    conditions.append('read')
                if name in self.txt.write1_clear:
                    conditions.append('write1')
                for cond in conditions:
                    extracted_registers[reg][field_name]['EGTA'] = [{
                        "trigger": [name + ' = ' + cond],
                        "action": [name + " = 0"]
                    }]
                    result.append(extracted_registers[reg][field_name]['EGTA'])
                if 'clear' in field['title']:
                    continue
                for t in self.signals.transmit:
                    for s in self.signals.buffer_signal:
                        if field['title'].find(t) != -1 and field['title'].find(
                                s) != -1 and 'threshold' not in field['title']:
                            extracted_registers[reg][field_name]['EGTA'] = [{
                                "trigger": [["<=", "transmit-buffer", "0"]],
                                "action":
                                [reg + "[" + field_name + "]" + " = 1"]
                            }]
                            result.append(
                                extracted_registers[reg][field_name]['EGTA'])
                for r in self.signals.receive:
                    for s in self.signals.buffer_signal:
                        if field['title'].find(r) != -1 and field['title'].find(
                                s) != -1 and 'threshold' not in field['title']:
                            extracted_registers[reg][field_name]['EGTA'] = [{
                                "trigger": [[">", "receive-buffer", "0"]],
                                "action":
                                [reg + "[" + field_name + "]" + " = 1"]
                            }, {
                                "trigger": [["<=", "receive-buffer", "0"]],
                                "action":
                                [reg + "[" + field_name + "]" + " = 0"]
                            }]
                            result.append(
                                extracted_registers[reg][field_name]['EGTA'])
        self.txt.registers = extracted_registers
        self.txt.result = result

    def extract_mode(self):

        def get_relation(sent, ends):
            if sent == "":
                return None
            #print(sent)
            entities = field_reg_search(sent, self.txt, "")
            #print(sent, entities)
            word = entities[0][0]
            t_field = word[word.find('[') + 1:-1]
            field = t_field + ends
            if field in self.txt.f2r:
                return self.txt.f2r[t_field], t_field, self.txt.f2r[
                    field], field
            return None

        self.txt.mode_result = []
        for key, value in self.txt.modes.items():
            if value['req'] == "":
                return self.txt.mode_result
            data = self.extract(value['req'], "", 1., True)
            data = [d[0] for d in data]
            for d in data:
                a = get_relation(d, 'T')
                if a != None and 'EGTA' not in self.txt.registers[a[0]][
                        a[1]] and 'EGTA' not in self.txt.registers[a[2]][a[3]]:
                    self.txt.mode_result.append([{
                        'trigger': ['ALL'],
                        'action':
                        [a[2] + '[' + a[3] + '] = ' + a[0] + '[' + a[1] + ']']
                    }])
