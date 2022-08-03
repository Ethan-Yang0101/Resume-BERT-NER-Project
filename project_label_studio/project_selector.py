######################################################
# 启发式数据分级筛选工具，初筛数据，更好地辅助标注
######################################################
import json
import os


'''不同类型的错误数据'''
PURE_OTHER_DATA = 'data/pure_other_data.json.txt'
PROJECT_ONLY_DATA = 'data/project_only_data.json.txt'
TIME_ONLY_DATA = 'data/time_only_data.json.txt'
OVER_LONG_DATA = 'data/over_long_data.json.txt'
PATTERN_WRONG_DATA = 'data/pattern_wrong_data.json.txt'
SUSPECTED_ERRONEOUS_DATA = 'data/suspected_erroneous_data.json.txt'
GENERAL_CORRECT_DATA = 'data/general_correct_data.json.txt'


def extract_txt_tag(data, create_index=False):
    '''从数据结构中提取文本，标签和索引，忽略空格'''
    txt_list, tag_list, cell_list = [], [], []
    for line_num, line in enumerate(data['objs']):
        for span_num, span in enumerate(line):
            text_tag = zip(span['text'], span['tags'])
            for cell_num, (cell_txt, cell_tag) in enumerate(text_tag):
                txt = cell_txt[0].strip()
                if txt:
                    txt_list.append(cell_txt[0])
                    tag_list.append(cell_tag)
                    if create_index:
                        index = (line_num, span_num, cell_num)
                        cell_list.append(index)
            if span_num < len(line) - 1:
                txt_list.append('[span]')
                tag_list.append('O')
                if create_index:
                    index = (line_num, span_num, cell_num)
                    cell_list.append(index)
        txt_list.append('[line]')
        tag_list.append('O')
        if create_index:
            index = (line_num, span_num, cell_num)
            cell_list.append(index)
    return txt_list, tag_list, cell_list


def write_data(data, file_name):
    '''写入数据到指定文件'''
    with open(file_name, 'a', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)
        fp.write('\n')
    return


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


def recover_data(txt_list, tag_list):
    '''将分解的列表还原为句子形式'''
    tags_list, tags = [], []
    for token, tag in zip(txt_list, tag_list):
        if token == '[line]':
            tags.append('O')
            tags_list.append(tags)
            tags = []
            continue
        tags.append(tag)
    return tags_list


def filter_company_data(tag_list):
    '''过滤掉含公司标签的数据'''
    is_company_data = False
    if any([tag in ['B-company', 'I-company'] for tag in tag_list]):
        is_company_data = True
    return is_company_data


def filter_all_other_data(tag_list):
    '''过滤掉数据集中没有任何标注的数据'''
    is_all_other_data = False
    if all([tag == 'O' for tag in tag_list]):
        is_all_other_data = True
    return is_all_other_data


def filter_time_only_data(tag_list):
    '''过滤掉只有时间的数据'''
    is_time_only_data = False
    if all([tag in ['B-timeRange', 'I-timeRange', 'O'] for tag in tag_list]):
        is_time_only_data = True
    return is_time_only_data


def filter_project_only_data(tag_list):
    '''过滤掉只有时间的数据'''
    is_project_only_data = False
    if all([tag in ['B-projectName', 'I-projectName', 'O'] for tag in tag_list]):
        is_project_only_data = True
    return is_project_only_data


def filter_overlong_data(tags_list, ratio):
    '''检测超过有无标签行比1:ratio的数据'''
    is_overlong_data = False
    count_rows = len(tags_list)
    count_label_lines = 0
    for tags in tags_list:
        con1 = 'B-timeRange' in tags or 'B-projectName' in tags
        con2 = 'I-timeRange' in tags or 'I-projectName' in tags
        if con1 or con2:
            count_label_lines += 1
    if (count_rows - count_label_lines) > count_label_lines * ratio:
        is_overlong_data = True
    return is_overlong_data


def filter_pattern_wrong_data(tags_list):
    '''
    筛选出所有具有明显模式错误的数据
    有时间的行，上中下行有经历
    有经历的行，上中下行有时间
    '''
    is_pattern_wrong_data = False
    time_label = ['B-timeRange', 'I-timeRange']
    name_label = ['B-projectName', 'I-projectName']
    all_spec_label = time_label + name_label
    for index, tags in enumerate(tags_list):
        if index != 0 and index != len(tags_list) - 1:
            if 'B-projectName' in tags or 'I-projectName' in tags:
                in_front = any(
                    [tag in time_label for tag in tags_list[index-1]])
                in_mid = any([tag in time_label for tag in tags_list[index]])
                in_back = any(
                    [tag in time_label for tag in tags_list[index+1]])
                if not in_front and not in_mid and not in_back:
                    is_pattern_wrong_data = True
                    break
            if 'B-timeRange' in tags or 'I-timeRange' in tags:
                in_front = any(
                    [tag in name_label for tag in tags_list[index-1]])
                in_mid = any([tag in name_label for tag in tags_list[index]])
                in_back = any(
                    [tag in name_label for tag in tags_list[index+1]])
                if not in_front and not in_mid and not in_back:
                    is_pattern_wrong_data = True
                    break
    return is_pattern_wrong_data


def filter_suspected_erroneous_data(tags_list, max_name, min_name, min_time, max_span):
    '''
    认为项目名最多不会超过max_name个标签
    认为项目名最少不该低于min_name个标签
    认为标准的时间应该至少min_time个标签
    认为项目名中不应该有超过max_span个O标签存在
    认为时间中不应该有超过max_span个O标签存在
    '''
    is_erroneous_data = False
    for index, tag_data in enumerate(tags_list):
        if 'B-timeRange' in tag_data or 'I-timeRange' in tag_data:
            time_start, time_end = 0, 0
            for index, label in enumerate(tag_data):
                if label == 'B-timeRange':
                    time_start = index
                    break
            time_end = time_start
            for index, label in enumerate(tag_data):
                if label == 'I-timeRange':
                    time_end = index
            time_range = tag_data[time_start:time_end+1]
            has_short_time = len(time_range) < min_time
            if has_short_time:
                is_erroneous_data = True
                break
            if sum([tag == 'O' for tag in time_range]) > max_span:
                is_erroneous_data = True
                break
        if 'B-projectName' in tag_data or 'I-projectName' in tag_data:
            name_start, name_end = 0, 0
            for index, label in enumerate(tag_data):
                if label == 'B-projectName':
                    name_start = index
                    break
            name_end = name_start
            for index, label in enumerate(tag_data):
                if label == 'I-projectName':
                    name_end = index
            project_name = tag_data[name_start:name_end+1]
            if len(project_name) > max_name:
                is_erroneous_data = True
                break
            if len(project_name) < min_name:
                is_erroneous_data = True
                break
            if sum([tag == 'O' for tag in project_name]) > max_span:
                is_erroneous_data = True
                break
    return is_erroneous_data


def hierarchical_inspect_and_store(file_name, ratio, max_name, min_name, min_time, max_span):
    '''
    分级检查标注数据质量并分级存放检查结果
    '''
    with open(file_name, 'r') as fp:
        for json_data in fp:
            data = json.loads(json_data[:-1])
            data = clean_title_label(data)
            txt_list, tag_list, cell_list = extract_txt_tag(
                data, create_index=False)
            is_all_other_data = filter_all_other_data(tag_list)
            if is_all_other_data:
                write_data(data, PURE_OTHER_DATA)
                continue
            is_company_data = filter_company_data(tag_list)
            if is_company_data:
                continue
            is_time_only_data = filter_time_only_data(tag_list)
            if is_time_only_data:
                write_data(data, TIME_ONLY_DATA)
                continue
            is_project_only_data = filter_project_only_data(tag_list)
            if is_project_only_data:
                write_data(data, PROJECT_ONLY_DATA)
                continue
            tags_list = recover_data(txt_list, tag_list)
            is_overlong_data = filter_overlong_data(tags_list, ratio)
            if is_overlong_data:
                write_data(data, OVER_LONG_DATA)
                continue
            is_pattern_wrong_data = filter_pattern_wrong_data(tags_list)
            if is_pattern_wrong_data:
                write_data(data, PATTERN_WRONG_DATA)
                continue
            is_erroneous_data = filter_suspected_erroneous_data(
                tags_list, max_name, min_name, min_time, max_span)
            if is_erroneous_data:
                write_data(data, SUSPECTED_ERRONEOUS_DATA)
                continue
            write_data(data, GENERAL_CORRECT_DATA)
    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    # 填写project数据文件名
    parser.add_argument('--file_name')
    # ratio数字越大，项目经历越长
    parser.add_argument('--ratio', default=20)
    # 限制项目名的长度
    parser.add_argument('--max_name', default=20)
    # 限制项目名的长度
    parser.add_argument('--min_name', default=10)
    # 限制时间的长度
    parser.add_argument('--min_time', default=7)
    # 限制时间和项目名中的O标签数量
    parser.add_argument('--max_span', default=0)
    args = parser.parse_args()
    file_name = args.file_name
    ratio = int(args.ratio)
    max_name = int(args.max_name)
    min_name = int(args.min_name)
    min_time = int(args.min_time)
    max_span = int(args.max_span)
    hierarchical_inspect_and_store(
        file_name, ratio, max_name, min_name, min_time, max_span)
