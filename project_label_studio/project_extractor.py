####################################################################
# 项目提取器，用来生成用于标注的数据，配合项目标注工具使用
####################################################################
from project_tool.project_processor import extract_txt_token_tag_cell
from project_tool.project_processor import recover_data
from project_tool.project_processor import filter_company_data
from project_tool.project_processor import clean_title_label
from project_tool.project_processor import make_label_data
from project_tool.project_processor import write_data
###########启发式自动修正和补全调用方法##################################
from project_tool.project_auto_correcter import select_span_line_data
from project_tool.project_auto_correcter import correct_span_line_data
from project_tool.project_auto_completer import complete_span_line_data
from project_tool.project_auto_correcter import select_span_span_line_data
from project_tool.project_auto_correcter import correct_span_span_line_data
from project_tool.project_auto_completer import complete_span_span_line_data
import json


def generate_label_data(data, auto_complete, label_file_name, index):
    '''生成需要标注的数据集'''
    # 清理所有职位标签
    data = clean_title_label(data)
    # 提取文本/词性/标签/索引信息
    txt_list, token_list, tag_list, cell_list = extract_txt_token_tag_cell(
        data)
    # 过滤掉所有带公司的数据（错误数据）
    is_company_data = filter_company_data(tag_list)
    if is_company_data:
        return
    # 将数据恢复成句子形式
    txts_list, tokens_list, tags_list, cells_list = recover_data(
        txt_list, token_list, tag_list, cell_list)
    # 不使用启发式自动标签补全
    if not auto_complete:
        # 生成标注数据，保存到标注数据文件中
        label_data = make_label_data(
            data['file'], txts_list, tags_list, cells_list, index)
        write_data(label_data, label_file_name)
        return
    # 使用启发式自动标签补全
    if auto_complete:
        # 判断是不是span-line模版数据
        span_line_data, time_front = select_span_line_data(
            txts_list, tags_list)
        if span_line_data:
            # 自动修正模版数据
            tags_list = correct_span_line_data(
                txts_list, tags_list, time_front)
            # 自动补全模版数据
            tags_list = complete_span_line_data(
                txts_list, tags_list, tokens_list)
            tags_list = complete_span_span_line_data(
                txts_list, tags_list, tokens_list)
            # 生成标注数据并保存到标注数据文件中
            label_data = make_label_data(
                data['file'], txts_list, tags_list, cells_list, index)
            write_data(label_data, label_file_name)
            return
        # 判断是不是span-span-line模版数据
        span_span_line_data, time_front, time_mid, time_back = select_span_span_line_data(
            txts_list, tags_list)
        if span_span_line_data:
            # 自动修正模版数据
            tags_list = correct_span_span_line_data(
                txts_list, tags_list, time_front, time_mid, time_back)
            # 自动补全模版数据
            tags_list = complete_span_span_line_data(
                txts_list, tags_list, tokens_list)
            tags_list = complete_span_line_data(
                txts_list, tags_list, tokens_list)
            # 生成标注数据并保存到标注数据文件中
            label_data = make_label_data(
                data['file'], txts_list, tags_list, cells_list, index)
            write_data(label_data, label_file_name)
            return
    return


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    # 项目经历数据文件名
    parser.add_argument('--moka_file_name')
    # 项目经历标注数据文件名
    parser.add_argument('--label_file_name')
    # 启发式自动补全功能
    parser.add_argument('--auto_complete', default=False)
    args = parser.parse_args()
    moka_file_name = args.moka_file_name
    label_file_name = args.label_file_name
    auto_complete = args.auto_complete
    with open(moka_file_name, 'r') as fp:
        index = 0  # 给生成的标注数据保留数据的索引，方便后期修正
        for json_data in fp:
            data = json.loads(json_data[:-1])
            # 给每条数据依次生成标注数据
            generate_label_data(data, auto_complete, label_file_name, index)
            index += 1
