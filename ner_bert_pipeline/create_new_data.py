from transformers import AutoTokenizer
import pandas as pd
import copy
import json
import os


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


def create_pred_table(token, pred, tags):
    tokenized_inputs = tokenizer(
        token, truncation=True,
        is_split_into_words=True, max_length=500)
    index = tokenized_inputs.word_ids(batch_index=0)
    index = [x for x in index if x is not None]
    pred_map = {k: v for k, v in zip(index, pred)}
    result = []
    for i, (x, y) in enumerate(zip(token, tags)):
        result.append((i, x, y, pred_map.get(i, 'O')))
    df = pd.DataFrame(result, columns=['index', 'text', 'label', 'pred'])
    return pred_map, df


def load_data(file):
    with open(file) as f:
        for line in f:
            yield json.loads(line)


def create_new_data(input_data, pred_data):
    new_data, old_data = [], []
    for i, data in enumerate(load_data(input_data)):
        token_list, _, tag_list, _ = extract_token_pos_tag_index(data)
        pred = pred_data[i]
        pred_map, df = create_pred_table(token_list, pred, tag_list)
        df = df[df['label'] != df['pred']]
        if len(df) > 0 and df['index'].max() < 500:
            print('found different: ', i)
            old = copy.deepcopy(data)
            index = 0
            for line_num, line in enumerate(data['objs']):
                for span_num, span in enumerate(line):
                    new_cell_tag = []
                    for cell_num, (token_pos, tag) in enumerate(zip(span['text'], span['tags'])):
                        token = token_pos[0].strip()
                        if token:
                            pred = pred_map.get(index, 'O')
                            new_cell_tag.append(pred)
                            index += 1
                        else:  # 空格
                            new_cell_tag.append('O')
                    # 一个span结束，最后一个[span]不算
                    if span_num < len(line) - 1:
                        index += 1
                    span['tags'] = new_cell_tag
                # 一个line结束，最后一个[line]不算
                index += 1
            new_data.append(data)
            old_data.append(old)
    save_data(new_data, 'new_result.json')
    save_data(old_data, 'old_result.json')


def save_data(json_list, file):
    with open(os.path.join(output_dir, file), 'w') as f:
        for data in json_list:
            f.write(json.dumps(data, ensure_ascii=False))
            f.write('\n')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', default='./proj_model')
    parser.add_argument('--input_data', default='./data/proj.json.txt')
    parser.add_argument('--output_dir', default='./prediction')

    args = parser.parse_args()
    model_path = args.model_path
    input_data = args.input_data
    output_dir = args.output_dir

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    special_tokens_dict = {'additional_special_tokens': ['[span]', '[line]']}
    num_added_toks = tokenizer.add_special_tokens(special_tokens_dict)

    output_test_predictions_file = os.path.join(
        output_dir, "test_predictions.txt")
    pred_labels = []
    with open(output_test_predictions_file) as f:
        for line in f:
            if line.strip():
                pred_labels.append(line.split())

    create_new_data(input_data, pred_labels)
