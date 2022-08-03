########################################################
# 可视化项目标注工具，需要配合项目提取器使用
########################################################
import json


def print_sample_by_tag(label_data_list, label_only, batch_index):
    '''可视化已标注的项目名和时间'''
    title = '\n--标注标签显示--绿色为时间--红色为项目名--batch_index: ' + \
        str(batch_index) + '\n'
    print(f"\033[31m{title}\033[0m")
    for label_data in label_data_list:
        file_id = label_data['file']
        data_idx = label_data['data_idx']
        # 这个打印的是这条数据在文件的第几行以及简历id，用来定位数据
        print(f'\033[34m{data_idx} - {file_id}\n\033[0m')
        for index, (txts, tags) in enumerate(zip(label_data['txts'], label_data['tags'])):
            if label_only and all([tag == 'O' for tag in tags]):
                continue
            index = str(index) + ' '
            # 这个打印的是这条数据中某排的索引，用来定位数据
            print(f'\033[34m{index}\033[0m', sep='', end='')
            for txt, tag in zip(txts, tags):
                # 下面的就是逐字打印内容了，有标签的会显示颜色
                if tag in ['B-timeRange', 'I-timeRange']:
                    print(f"\033[0;37;42m{txt}\033[0m", sep='', end='')
                    print(f"\033[0;37;42m{'|'}\033[0m", sep='', end='')
                elif tag in ['B-projectName', 'I-projectName']:
                    print(f"\033[0;37;41m{txt}\033[0m", sep='', end='')
                    print(f"\033[0;37;41m{'|'}\033[0m", sep='', end='')
                else:
                    print(txt, sep='', end='')
                    print('|', sep='', end='')
            print('\n')
    return


def prepare_label_data_list(file_name):
    '''准备需要检查和标注的数据集'''
    label_data_list = []
    data_idx = 0  # 标注数据集的索引，方便定位修正数据的位置
    with open(file_name, 'r') as fp:
        for json_data in fp:
            data = json.loads(json_data[:-1])
            data['data_idx'] = data_idx
            label_data_list.append(data)
            data_idx += 1
    return label_data_list


def browse_label_data(label_data_list, label_only, batch_index):
    '''通过批索引浏览需要检查和标注的数据集'''
    # 批索引是为了在可视化翻页的时候知道数据在第几页
    if (batch_index+1) * 5 < len(label_data_list):
        label_data_list = label_data_list[batch_index * 5:(batch_index+1) * 5]
        print_sample_by_tag(label_data_list, label_only, batch_index)
    else:
        label_data_list = label_data_list[batch_index * 5:]
        print_sample_by_tag(label_data_list, label_only, batch_index)
    return


def clean_label(data_idx, row_num, text, label_data_list):
    '''清除指定位置的标签'''
    label_data = label_data_list[data_idx]
    # 如果只有一个分词部分需要清理标签
    if '|' not in text:
        for index in range(len(label_data['txts'][row_num])):
            if label_data['txts'][row_num][index] == text:
                label_data['tags'][row_num][index] = 'O'
                break
        return label_data_list
    # 如果有多个分词部分需要清理标签
    text = text.split('|')
    for index in range(len(label_data['txts'][row_num])):
        head_index = index
        next_index = index+1
        tail_index = index + len(text) - 1
        head_correct = text[0] == label_data['txts'][row_num][head_index]
        next_correct = text[1] == label_data['txts'][row_num][next_index]
        tail_correct = text[-1] == label_data['txts'][row_num][tail_index]
        if head_correct and next_correct and tail_correct:
            for index in range(head_index, tail_index+1):
                label_data['tags'][row_num][index] = 'O'
            break
    return label_data_list


def label_data(data_idx, row_num, text, label_type, label_data_list):
    '''根据标签类型标注数据'''
    label_data = label_data_list[data_idx]
    # 如果只有一个分词部分需要标注标签
    if '|' not in text:
        for index in range(len(label_data['txts'][row_num])):
            if label_data['txts'][row_num][index] == text:
                if label_type == 'name':
                    label_data['tags'][row_num][index] = 'B-projectName'
                    break
                if label_type == 'time':
                    label_data['tags'][row_num][index] = 'B-timeRange'
                    break
        return label_data_list
    # 如果有多个分词部分需要标注标签
    text = text.split('|')
    for index in range(len(label_data['txts'][row_num])):
        head_index = index
        next_index = index+1
        tail_index = index + len(text) - 1
        head_correct = text[0] == label_data['txts'][row_num][head_index]
        next_correct = text[1] == label_data['txts'][row_num][next_index]
        tail_correct = text[-1] == label_data['txts'][row_num][tail_index]
        if head_correct and next_correct and tail_correct:
            if label_type == 'name':
                # 这里采用先删掉这行的项目名标签，再重新标注正确的标签
                for index in range(len(label_data['tags'][row_num])):
                    if label_data['tags'][row_num][index] in ['B-projectName', 'I-projectName']:
                        label_data['tags'][row_num][index] = 'O'
                label_data['tags'][row_num][head_index] = 'B-projectName'
                for index in range(head_index+1, tail_index+1):
                    label_data['tags'][row_num][index] = 'I-projectName'
                break
            if label_type == 'time':
                # 这里采用先删掉这行的时间标签，再重新标注正确的标签
                for index in range(len(label_data['tags'][row_num])):
                    if label_data['tags'][row_num][index] in ['B-timeRange', 'I-timeRange']:
                        label_data['tags'][row_num][index] = 'O'
                label_data['tags'][row_num][head_index] = 'B-timeRange'
                for index in range(head_index+1, tail_index+1):
                    label_data['tags'][row_num][index] = 'I-timeRange'
                break
    return label_data_list


def create_new_label_data_file(label_data_list, new_data_file_name):
    '''将修改好的标注数据写入新文件'''
    with open(new_data_file_name, 'w', encoding='utf-8') as fp:
        for label_data in label_data_list:
            json.dump(label_data, fp, ensure_ascii=False)
            fp.write('\n')
    return


def reconstruct_data(fixed_data_file, origin_data_file, new_data_file):
    '''根据修正文件修改原来的数据'''
    origin_data_list = []
    # 读取还未修正的数据
    with open(origin_data_file, 'r') as fp:
        for origin_data in fp:
            origin_data = json.loads(origin_data[:-1])
            origin_data_list.append(origin_data)
    # 根据修正好的标注数据修正数据
    with open(fixed_data_file, 'r') as fp:
        for json_data in fp:
            data = json.loads(json_data[:-1])
            row_idx, txts_list = data['row_idx'], data['txts']
            tags_list, cells_list = data['tags'], data['cells']
            origin_data = origin_data_list[row_idx]
            for txts, tags, cells in zip(txts_list, tags_list, cells_list):
                for txt, tag, cell in zip(txts, tags, cells):
                    if txt.strip() and txt not in ['[span]', '[line]']:
                        line, span, num = cell[0], cell[1], cell[2]
                        origin_data['objs'][line][span]['tags'][num] = tag
    # 将修正好的数据写入新文件
    with open(new_data_file, 'w', encoding='utf-8') as fp:
        for origin_data in origin_data_list:
            json.dump(origin_data, fp, ensure_ascii=False)
            fp.write('\n')
    return
