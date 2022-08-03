########################################################
# 项目数据处理脚本
########################################################
import json


def extract_txt_token_tag_cell(data, create_index=True):
    '''从数据结构中提取文本，词性，标签和索引，忽略空格'''
    txt_list, token_list, tag_list, cell_list = [], [], [], []
    for line_num, line in enumerate(data['objs']):
        for span_num, span in enumerate(line):
            text_tag = zip(span['text'], span['tags'])
            for cell_num, (cell_txt, cell_tag) in enumerate(text_tag):
                txt = cell_txt[0].strip()
                if txt:
                    txt_list.append(cell_txt[0])
                    token_list.append(cell_txt[1])
                    tag_list.append(cell_tag)
                    if create_index:
                        index = (line_num, span_num, cell_num)
                        cell_list.append(index)
            if span_num < len(line) - 1:
                txt_list.append('[span]')
                token_list.append('<SEPC>')
                tag_list.append('O')
                if create_index:
                    index = (line_num, span_num)
                    cell_list.append(index)
        txt_list.append('[line]')
        token_list.append('<SEPC>')
        tag_list.append('O')
        if create_index:
            index = (line_num)
            cell_list.append(index)
    return txt_list, token_list, tag_list, cell_list


def recover_data(txt_list, token_list, tag_list, cell_list):
    '''将列表还原为句子形式'''
    txts_list, txts = [], []
    tokens_list, tokens = [], []
    tags_list, tags = [], []
    cells_list, cells = [], []
    txt_token_tag_cell = zip(txt_list, token_list, tag_list, cell_list)
    for txt, token, tag, cell in txt_token_tag_cell:
        txts.append(txt)
        tokens.append(token)
        tags.append(tag)
        cells.append(cell)
        if txt == '[line]':
            txts_list.append(txts)
            tokens_list.append(tokens)
            tags_list.append(tags)
            cells_list.append(cells)
            txts, tokens, tags, cells = [], [], [], []
    return txts_list, tokens_list, tags_list, cells_list


def clean_title_label(data):
    '''清除所有职位标签，忽略空格'''
    for line in data['objs']:
        for span in line:
            txt_tag = zip(span['text'], span['tags'])
            for cell_num, (cell_txt, cell_tag) in enumerate(txt_tag):
                if cell_txt[0].strip():
                    if cell_tag in ['B-title', 'I-title']:
                        span['tags'][cell_num] = 'O'
    return data


def filter_company_data(tag_list):
    '''过滤掉含公司标签的数据'''
    is_company_data = False
    if any([tag in ['B-company', 'I-company'] for tag in tag_list]):
        is_company_data = True
    return is_company_data


def make_label_data(file_id, txts_list, tags_list, cells_list, index):
    '''给每个文件生成需要标注的数据'''
    return {'file': file_id, 'txts': txts_list, 
            'tags': tags_list, 'cells': cells_list, 
            'row_idx': index}


def write_data(data, file_name):
    '''写入数据到指定文件'''
    with open(file_name, 'a', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)
        fp.write('\n')
    return
    