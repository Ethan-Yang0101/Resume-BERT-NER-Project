##############################################################
# 启发式自动标签补全脚本
##############################################################

def complete_span_line_data(txts_list, tags_list, tokens_list):
    '''
    填补满足以下模式的数据：
    时间[span]项目名[line]
    项目名[span]时间[line]
    '''
    for txts, tags, tokens in zip(txts_list, tags_list, tokens_list):
        if all([tag == 'O' for tag in tags]):
            if sum([txt == '[span]' for txt in txts]) == 1:
                span_index = txts.index('[span]')
                front = tokens[:span_index]
                back = tokens[span_index+1:-1]
                if sum(['<TMR>' in token.split(',') for token in front]) >= 3:
                    if len(front) <= 10:
                        tags[0] = 'B-timeRange'
                        for i in range(1, span_index):
                            tags[i] = 'I-timeRange'
                        tags[span_index+1] = 'B-projectName'
                        for i in range(span_index+2, len(tags)-1):
                            tags[i] = 'I-projectName'
                        continue
                if sum(['<TMR>' in token.split(',') for token in back]) >= 3:
                    if len(back) <= 10:
                        tags[0] = 'B-projectName'
                        for i in range(1, span_index):
                            tags[i] = 'I-projectName'
                        tags[span_index+1] = 'B-timeRange'
                        for i in range(span_index+2, len(tags)-1):
                            tags[i] = 'I-timeRange'
                        continue
                if sum(['<TMS>' in token.split(',') for token in back]) >= 3:
                    if len(back) <= 10:
                        tags[0] = 'B-projectName'
                        for i in range(1, span_index):
                            tags[i] = 'I-projectName'
                        tags[span_index+1] = 'B-timeRange'
                        for i in range(span_index+2, len(tags)-1):
                            tags[i] = 'I-timeRange'
                        continue
                if all(['<TMS>' in token.split(',') for token in front]) >= 3:
                    if len(front) <= 10:
                        tags[0] = 'B-timeRange'
                        for i in range(1, span_index):
                            tags[i] = 'I-timeRange'
                        tags[span_index+1] = 'B-projectName'
                        for i in range(span_index+2, len(tags)-1):
                            tags[i] = 'I-projectName'
                        continue
    return tags_list


def complete_span_span_line_data(txts_list, tags_list, tokens_list):
    '''
    填补满足以下模式的数据：
    时间[span]项目名[span]负责人[line]
    项目名[span]时间[span]负责人[line]
    项目名[span]负责人[span]时间[line]
    '''
    for txts, tags, tokens in zip(txts_list, tags_list, tokens_list):
        if all([tag == 'O' for tag in tags]):
            if sum([txt == '[span]' for txt in txts]) == 2:
                span_index = [index for (index, txt) in enumerate(
                    txts) if txt == '[span]']
                front = tokens[:span_index[0]]
                mid = tokens[span_index[0]+1:span_index[1]]
                back = tokens[span_index[1]+1:-1]
                max_front = len(front) <= 10
                three_tmr = sum(['<TMR>' in token.split(',')
                                 for token in front]) >= 3
                three_tms = sum(['<TMS>' in token.split(',')
                                 for token in front]) >= 3
                if max_front and (three_tmr or three_tms):
                    tags[0] = 'B-timeRange'
                    for i in range(1, span_index[0]):
                        tags[i] = 'I-timeRange'
                    tags[span_index[0]+1] = 'B-projectName'
                    for i in range(span_index[0]+2, span_index[1]):
                        tags[i] = 'I-projectName'
                    for i in range(span_index[1]+1, len(tags)-1):
                        tags[i] = 'O'
                    continue
                max_mid = len(mid) <= 10
                three_tmr = sum(['<TMR>' in token.split(',')
                                 for token in mid]) >= 3
                three_tms = sum(['<TMS>' in token.split(',')
                                 for token in mid]) >= 3
                if max_mid and (three_tmr or three_tms):
                    tags[0] = 'B-projectName'
                    for i in range(1, span_index[0]):
                        tags[i] = 'I-projectName'
                    tags[span_index[0]+1] = 'B-timeRange'
                    for i in range(span_index[0]+2, span_index[1]):
                        tags[i] = 'I-timeRange'
                    for i in range(span_index[1]+1, len(tags)-1):
                        tags[i] = 'O'
                    continue
                max_back = len(back) <= 10
                three_tmr = sum(['<TMR>' in token.split(',')
                                 for token in back]) >= 3
                three_tms = sum(['<TMS>' in token.split(',')
                                 for token in back]) >= 3
                if max_back and (three_tmr or three_tms):
                    tags[0] = 'B-projectName'
                    for i in range(1, span_index[0]):
                        tags[i] = 'I-projectName'
                    for i in range(span_index[0]+1, span_index[1]):
                        tags[i] = 'O'
                    tags[span_index[1]+1] = 'B-timeRange'
                    for i in range(span_index[1]+2, len(tags)-1):
                        tags[i] = 'I-timeRange'
                    continue
    return tags_list
