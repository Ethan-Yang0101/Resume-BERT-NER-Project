from tqdm import tqdm
import json


def extract_token_pos_tag_index(data, create_index=False):
    '''
    从一条简历数据结构中提取文本，词性，标签和索引，忽略空token
    在每个间隔和句子之间添加特殊token-[span]和[line]
    '''
    token_list, pos_list, tag_list, index_list = [], [], [], []
    for line_num, line in enumerate(data['objs']):
        for span_num, span in enumerate(line):
            token_pos_tag = zip(span['text'], span['tags'])
            for cell_num, (token_pos, tag) in enumerate(token_pos_tag):
                token = token_pos[0].strip()
                if token:
                    token_list.append(token_pos[0])
                    pos_list.append(token_pos[1])
                    tag_list.append(tag)
                    if create_index:
                        index = (line_num, span_num, cell_num)
                        index_list.append(index)
            if span_num < len(line) - 1:
                token_list.append('[span]')
                pos_list.append('<SEPC>')
                tag_list.append('O')
                if create_index:
                    index = (line_num, span_num)
                    index_list.append(index)
        token_list.append('[line]')
        pos_list.append('<SEPC>')
        tag_list.append('O')
        if create_index:
            index = (line_num)
            index_list.append(index)
    return token_list, pos_list, tag_list, index_list


def load_data(file):
    '''每次读取一条JSON数据的生成器'''
    with open(file) as f:
        for line in f:
            yield json.loads(line)


def create_target_data(source_file, target_file):
    '''
    把每一条JSON数据中的token和tag提取出来，
    写入txt文件，\n用来区分每一条JSON数据
    '''
    with open(target_file, 'w') as f:
        f.write('\n')
        for data in tqdm(load_data(source_file)):
            token_list, _, tag_list, _ = extract_token_pos_tag_index(data)
            if len(token_list) != len(tag_list):
                print('failed')
                break
            for token, tag in zip(token_list, tag_list):
                token = token.strip()
                if token:
                    f.write(f'{token} {tag}\n')
            f.write('\n')


if __name__ == '__main__':
    import argparse

    # target_file: 预处理后的文件
    parser = argparse.ArgumentParser()
    parser.add_argument('--target_file', default='./data/proj.txt')
    # source file: 需处理的JSON文件
    parser.add_argument('--source_file', default='./data/proj.json.txt')

    args = parser.parse_args()
    target_file = args.target_file
    source_file = args.source_file

    print('args', args)
    create_target_data(source_file, target_file)
