####################################################
# 模版数据自动标签修正脚本
####################################################

def select_span_line_data(txts_list, tags_list):
    '''
    筛选满足以下模式的数据：
    时间[span]项目名[line]
    项目名[span]时间[line]
    '''
    span_line_data = True
    time_front = False
    time_label = ['B-timeRange', 'I-timeRange']
    name_label = ['B-projectName', 'I-projectName']
    all_spec_label = time_label + name_label
    for txts, tags in zip(txts_list, tags_list):
        if any([tag in all_spec_label for tag in tags]):
            if sum([txt == '[span]' for txt in txts]) != 1:
                span_line_data = False
                break
            else:
                span_index = txts.index('[span]')
                front = tags[:span_index]
                back = tags[span_index+1:-1]
                project_front = any([tag in name_label for tag in front])
                time_front = any([tag in time_label for tag in front])
                project_back = any([tag in name_label for tag in back])
                time_back = any([tag in time_label for tag in back])
                con1 = project_front and time_back
                con2 = time_front and project_back
                if not con1 and not con2:
                    span_line_data = False
                    break
                if time_front and len(front) > 10:
                    span_line_data = False
                    break
                if time_back and len(back) > 10:
                    span_line_data = False
                    break
                if time_front + time_back != 1:
                    span_line_data = False
                    break
    return span_line_data, time_front


def correct_span_line_data(txts_list, tags_list, time_front):
    '''
    修正满足以下模式的数据：
    时间[span]项目名[line]
    项目名[span]时间[line]
    '''
    time_label = ['B-timeRange', 'I-timeRange']
    for txts, tags in zip(txts_list, tags_list):
        if any([tag != 'O' for tag in tags]):
            span_index = txts.index('[span]')
            front = tags[:span_index]
            back = tags[span_index+1:-1]
            if time_front:
                tags[0] = 'B-timeRange'
                for i in range(1, span_index):
                    tags[i] = 'I-timeRange'
                tags[span_index+1] = 'B-projectName'
                for i in range(span_index+2, len(tags)-1):
                    tags[i] = 'I-projectName'
            if not time_front:
                tags[0] = 'B-projectName'
                for i in range(1, span_index):
                    tags[i] = 'I-projectName'
                tags[span_index+1] = 'B-timeRange'
                for i in range(span_index+2, len(tags)-1):
                    tags[i] = 'I-timeRange'
    return tags_list


def select_span_span_line_data(txts_list, tags_list):
    '''
    筛选满足以下模式的数据：
    时间[span]项目名[span]负责人[line]
    项目名[span]时间[span]负责人[line]
    项目名[span]负责人[span]时间[line]
    '''
    span_span_line_data = True
    time_front = False
    time_mid = False
    time_back = False
    time_label = ['B-timeRange', 'I-timeRange']
    name_label = ['B-projectName', 'I-projectName']
    all_spec_label = time_label + name_label
    for txts, tags in zip(txts_list, tags_list):
        if any([tag in all_spec_label for tag in tags]):
            if sum([txt == '[span]' for txt in txts]) != 2:
                span_span_line_data = False
                break
            else:
                span_index = [index for (index, txt) in enumerate(
                    txts) if txt == '[span]']
                front = tags[:span_index[0]]
                mid = tags[span_index[0]+1:span_index[1]]
                back = tags[span_index[1]+1:-1]
                project_front = any([tag in name_label for tag in front])
                project_mid = any([tag in name_label for tag in mid])
                project_back = any([tag in name_label for tag in back])
                time_front = any([tag in time_label for tag in front])
                time_mid = any([tag in time_label for tag in mid])
                time_back = any([tag in time_label for tag in back])
                con1 = time_front and (project_mid or project_back)
                con2 = time_mid and (project_front or project_back)
                con3 = time_back and (project_front or project_mid)
                if not con1 and not con2 and not con3:
                    span_span_line_data = False
                    break
                if time_front and len(front) > 10:
                    span_span_line_data = False
                    break
                if time_mid and len(mid) > 10:
                    span_span_line_data = False
                    break
                if time_back and len(back) > 10:
                    span_span_line_data = False
                    break
                if time_front + time_mid + time_back != 1:
                    span_span_line_data = False
                    break
    return span_span_line_data, time_front, time_mid, time_back


def correct_span_span_line_data(txts_list, tags_list, time_front, time_mid, time_back):
    '''
    修正满足以下模式的数据：
    时间[span]项目名[span]负责人[line]
    项目名[span]时间[span]负责人[line]
    项目名[span]负责人[span]时间[line]
    '''
    time_label = ['B-timeRange', 'I-timeRange']
    for txts, tags in zip(txts_list, tags_list):
        if any([tag != 'O' for tag in tags]):
            span_index = [index for (index, txt) in enumerate(
                txts) if txt == '[span]']
            front = tags[:span_index[0]]
            mid = tags[span_index[0]+1:span_index[1]]
            back = tags[span_index[1]+1:-1]
            if time_front:
                tags[0] = 'B-timeRange'
                for i in range(1, span_index[0]):
                    tags[i] = 'I-timeRange'
                tags[span_index[0]+1] = 'B-projectName'
                for i in range(span_index[0]+2, span_index[1]):
                    tags[i] = 'I-projectName'
                for i in range(span_index[1]+1, len(tags)-1):
                    tags[i] = 'O'
            if time_mid:
                tags[0] = 'B-projectName'
                for i in range(1, span_index[0]):
                    tags[i] = 'I-projectName'
                tags[span_index[0]+1] = 'B-timeRange'
                for i in range(span_index[0]+2, span_index[1]):
                    tags[i] = 'I-timeRange'
                for i in range(span_index[1]+1, len(tags)-1):
                    tags[i] = 'O'
            if time_back:
                tags[0] = 'B-projectName'
                for i in range(1, span_index[0]):
                    tags[i] = 'I-projectName'
                for i in range(span_index[0]+1, span_index[1]):
                    tags[i] = 'O'
                tags[span_index[1]+1] = 'B-timeRange'
                for i in range(span_index[1]+2, len(tags)-1):
                    tags[i] = 'I-timeRange'
    return tags_list
