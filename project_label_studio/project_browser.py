#####################################################################
# 项目浏览器，浏览项目经历数据
#####################################################################
from project_tool.project_processor import extract_txt_token_tag_cell
from project_tool.project_processor import recover_data
import json


def read_data_batch(file_name):
    '''获取前1000行数据'''
    cache_data = []
    count = 0
    with open(file_name, 'r') as fp:
        while count != 1000:
            cache_data.append(fp.readline())
            count += 1
    return cache_data


def browse_json_data(cache_data, index):
    '''通过索引浏览数据'''
    if index < 1000:
        json_string = cache_data[index]
        data = json.loads(json_string[:-1])
        txt_tag_token_list = prepare_data(data)
        data_id = data['file']
        print(f'\033[31m{data_id}\033[0m')
        print_sample_by_tag(txt_tag_token_list)
        print_sample_by_token(txt_tag_token_list)
        return
    print('无法找到对应的文件')
    return


def check_wrong_file(file_name, data_id):
    '''根据数据ID检查错误的数据'''
    with open(file_name, 'r') as fp:
        for json_string in fp:
            data = json.loads(json_string[:-1])
            if data['file'] == data_id:
                txt_tag_token_list = prepare_data(data)
                print(f'\033[31m{data_id}\033[0m')
                print_sample_by_tag(txt_tag_token_list)
                print_sample_by_token(txt_tag_token_list)
                return
        print('无法找到对应的文件')
        return


def make_data(txt_list, tag_list, token_list):
    '''生成用于查看的数据结构'''
    txt_tag_token_list = []
    txt_tag_token = []
    for txt, tag, token in zip(txt_list, tag_list, token_list):
        txt_tag_token.append([txt, tag, token])
        if txt == '[line]':
            txt_tag_token_list.append(txt_tag_token)
            txt_tag_token = []
    return txt_tag_token_list


def prepare_data(data):
    '''准备用于可视化的数据'''
    txt_list, token_list, tag_list, cell_list = extract_txt_token_tag_cell(
        data, create_index=False)
    txt_tag_token_list = make_data(txt_list, tag_list, token_list)
    return txt_tag_token_list


def print_sample_by_tag(txt_tag_token_list):
    '''可视化已标注的项目名和时间'''
    title = '\n----标注标签显示--绿色为时间--红色为项目名----\n'
    print(f"\033[34m{title}\033[0m")
    for index, txt_tag_token in enumerate(txt_tag_token_list):
        print(f'{index} ', sep='', end='')
        for data_list in txt_tag_token:
            txt = data_list[0]
            tag = data_list[1]
            if tag in ['B-timeRange', 'I-timeRange']:
                print(f"\033[0;37;42m{txt}\033[0m", sep='', end='')
            elif tag in ['B-projectName', 'I-projectName']:
                print(f"\033[0;37;41m{txt}\033[0m", sep='', end='')
            else:
                print(txt, sep='', end='')
        print('\n')
    return


def print_sample_by_token(txt_tag_token_list):
    '''可视化时间词性标签'''
    title = '\n----词性标签显示--绿色为TMR--蓝色为TMS--绿色优先级更高----\n'
    print(f"\033[34m{title}\033[0m")
    for index, txt_tag_token in enumerate(txt_tag_token_list):
        print(f'{index} ', sep='', end='')
        for data_list in txt_tag_token:
            txt = data_list[0]
            token = data_list[2]
            if '<TMR>' in token.split(','):
                print(f"\033[0;37;42m{txt}\033[0m", sep='', end='')
            elif '<TMS>' in token.split(','):
                print(f"\033[0;37;44m{txt}\033[0m", sep='', end='')
            else:
                print(txt, sep='', end='')
        print('\n')
    return
