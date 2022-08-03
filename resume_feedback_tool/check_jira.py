import json
import os
import re
import sqlite3

import pandas as pd
import requests
from jira import JIRA
import traceback

dev_url = "https://neon-test.mokahr.com/api/v2/resume_extract"


def extract_info_from_jira(user_name, password, saved_path):
    '''
    从jira上获取所有需要使用的信息\n
    user_name: jira登录用户名\n
    password: jira登录密码\n
    saved_path: 保存jira信息的文件夹路径\n 
    '''
    jira = JIRA('https://jira.mokahr.com/', basic_auth=(user_name, password))
    issues = jira.search_issues('project = INNO AND labels in (简历解析) \
                                 AND type = Bug AND status not in (DONE, 关闭)\
                                 ORDER BY priority DESC, updated DESC')
    key_list, uuid_list = [], []
    status_list, assignee_list = [], []
    creator_list = []
    for issue in issues:
        description = issue.fields.description
        matched = re.findall(r'resume_parser/standard/(\S{36})', description)
        if matched:
            key_list.append(issue.key)
            uuid_list.append(matched[0])
            creator = issue.fields.creator.displayName
            status = issue.fields.status.name
            creator_list.append(creator)
            status_list.append(status)
            assignee = issue.fields.assignee
            if assignee is None:
                assignee_list.append('未分配')
            if assignee is not None:
                assignee_list.append(assignee.displayName)
    jira_info = {'inno': key_list, 'resume_key': uuid_list,
                 'status': status_list, 'assignee': assignee_list, 'creator': creator_list}

    df = pd.DataFrame.from_dict({'inno': key_list, 'resume_key': uuid_list, })
    print('load new jira', len(key_list))
    with open(os.path.join(saved_path, 'jira_info.json'), 'w', encoding='utf-8') as fp:
        json.dump(jira_info, fp, indent=4, ensure_ascii=False)
    print(df.to_string())
    return


def extract_data_from_sqlite(jira_path, db_path, advice_path, file_path):
    '''
    从sqlite数据库中下载检查所需的文件\n
    jira_path: jira信息存储的文件夹路径\n
    db_path: 数据库路径\n
    advice_path: 准备存放advice数据的文件夹路径\n
    file_path: 准备存放简历数据的文件夹路径\n
    '''
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(os.path.join(jira_path, 'jira_info.json'), 'r') as fp:
        info_dict = json.load(fp)
    uuid_list = info_dict['resume_key']
    cursor.execute('''SELECT uuid, file, advice, file_name
                      FROM dashboard_resumeinfo
                      WHERE uuid IN ''' + str(tuple(uuid_list)) + ";")
    for data_row in cursor:
        uuid = data_row[0]
        blob_file = data_row[1]
        advice = data_row[2]
        file_name = data_row[3]
        doc_type = os.path.splitext(file_name)[1]
        abs_advice_path = os.path.join(
            advice_path, str(uuid) + doc_type + '_advice.json')
        with open(abs_advice_path, 'w', encoding='utf-8') as fp:
            json_dict = json.loads(advice)
            json.dump(json_dict, fp, indent=4, ensure_ascii=False)
        abs_file_path = os.path.join(file_path, str(uuid) + doc_type)
        with open(abs_file_path, 'wb') as fp:
            fp.write(blob_file)
    conn.close()
    return


def parse_resume(file_name, resume_path, url, saved_path=None, verbose=False):
    '''
    解析单个简历并保存解析结果\n
    file_name: 准备解析的简历名\n
    resume_path: 准备解析的简历文件夹路径\n
    url: 简历解析模型的url\n
    saved_path: 保存解析后简历的文件夹路径\n
    verbose: 查看解析结果是否成功\n
    '''
    name = os.path.join(resume_path, file_name)
    if not os.path.exists(name):
        print(file_name, 'not found')
        return
    files = {'file': open(name, 'rb')}
    trace = f'robot-{file_name}'
    params = dict()
    params['requestId'] = trace
    params['resume_key'] = file_name
    params['org_id'] = 'script'
    params['infer'] = '1'
    source_1 = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2UiOiJyZXN1bWUtcGFyc2VyIiwiZ'
    source_2 = 'GVwYXJ0bWVudCI6ImFpIiwicHJvamVjdCI6InRlc3QiLCJvd25lciI6InRlc3Q'
    source_3 = 'iLCJwcmlvcml0eSI6IjkiLCJpYXQiOjE2MjEzOTYyNjR9.w2NTwCM2kzOIs0zenL3fnQMO6gb7rSTYO_y6_9D4Tc0'
    params['source'] = source_1 + source_2 + source_3
    try:
        resp = requests.post(url=url, files=files, data=params)
        if verbose:
            print(trace, resp.status_code, file_name)
        if saved_path is not None:
            with open(os.path.join(saved_path, file_name + '.json'), 'w', encoding='utf-8') as fp:
                json.dump(resp.json(), fp, indent=4, ensure_ascii=False)
    except:
        print('failed', file_name)
        return -1
    return 0


def parse_resumes_v2(resume_path, saved_path):
    '''
    根据文件类型批量解析简历\n
    resume_path: 准备解析的简历文件夹路径\n
    saved_path: 保存解析后简历的文件夹路径\n
    '''
    url = "http://ats-tnt-resume-parser-import.mokahr.com:12345/api/v2/resume_extract"
    if is_dev:
        url = dev_url
    resume_list = os.listdir(resume_path)
    for doc_type in ['.pdf', '.doc', '.docx', '.jpg', '.html']:
        resume_sublist = [
            resume for resume in resume_list if resume.endswith(doc_type)]
        for resume in resume_sublist:
            if os.path.exists(os.path.join(saved_path, resume + '.json')) and (not force):
                continue
            parse_resume(resume, resume_path, url,
                         saved_path, verbose=True)
    return


filter_type = [0, 1]


def filter_advice_info(advice_dict):
    '''
    过滤advice数据字典，仅保留不为type1的数据\n
    advice_dict: jira的advice数据字典\n
    返回不含有type1的advice数据字典\n
    '''
    filtered_dict = {}
    for info_type in advice_dict.keys():
        info = advice_dict[info_type]
        sub_filtered_dict = {}
        if info_type == 'info':
            for key in info.keys():
                if not info[key]['type'] in filter_type:
                    sub_filtered_dict[key] = info[key]
            filtered_dict[info_type] = sub_filtered_dict
        if info_type != 'info':
            for info_number in info.keys():
                segment = info[info_number]
                if 'type' in segment and (not segment['type'] in filter_type):
                    sub_filtered_dict[info_number] = {'type': segment['type']}
                    for key in list(segment.keys())[1:]:
                        if not segment[key]['type'] in filter_type:
                            sub_filtered_dict[info_number][key] = segment[key]
            filtered_dict[info_type] = sub_filtered_dict
    return filtered_dict


def make_jira_check_list(filtered_dict):
    '''
    根据过滤后的advice数据字典创建检查列表\n
    filtered_dict: 过滤后的advice数据字典\n
    返回检查列表\n
    '''
    check_list = []
    for info_type in filtered_dict.keys():
        info_json = filtered_dict[info_type]
        check_path_list = []
        if info_type == 'info':
            for key in info_json.keys():
                check_path = []
                check_path.append(info_type)
                check_path.append(key)
                check_path.append(info_json[key])
                check_path_list.append(check_path)
        if info_type != 'info':
            for number in info_json.keys():
                segment = info_json[number]
                for key in segment.keys():
                    check_path = []
                    check_path.append(info_type)
                    check_path.append(number)
                    check_path.append(key)
                    check_path.append(segment[key])
                    check_path_list.append(check_path)
        check_list.extend(check_path_list)
    return check_list


def check_feedback_and_info(info_dict, uuid_name, parsed_file, check_list, csv_dict):
    '''
    检查简历解析结果info部分是否解决反馈的问题\n
    jira_path: jira信息存储的文件夹路径\n
    uuid_name: 解析的简历名称\n
    parsed_file: 解析的简历文件\n
    check_list: 简历检查列表\n
    csv_dict: 收集到的所有检查结果\n
    返回简历检查结果\n
    '''
    info_check_list = [check for check in check_list if check[0] == 'info']

    index = info_dict['resume_key'].index(uuid_name)
    for check in info_check_list:
        inno = info_dict['inno'][index]
        csv_dict['INNO序号'].append(inno)
        csv_dict['当前状态'].append(info_dict['status'][index])
        csv_dict['创建人'].append(info_dict['creator'][index])
        csv_dict['经办人'].append(info_dict['assignee'][index])
        csv_dict['简历ID'].append(uuid_name)
        # if inno=='INNO-427':
        #     print(check)
        #     print(parsed_file)
        if check[0] not in parsed_file.keys():
            csv_dict['检查字段'].append(f'{check[0]}')
            csv_dict['错误类型'].append('解析字段缺失')
            csv_dict['检查结果'].append('不支持')
            continue
        check_key2 = check[1]
        if check_key2 == 'birth':
            check_key2 = 'birthYear'
        if check_key2 not in parsed_file[check[0]]:
            csv_dict['检查字段'].append(f'{check[0]} - {check[1]}')
            csv_dict['错误类型'].append('解析字段缺失')
            csv_dict['检查结果'].append('不支持')
            continue
        info = parsed_file[check[0]][check_key2]

        feedback = check[2]
        feedback_type = feedback['type']
        feed_map = {'2': '无中生有', '3': '不对劲', '4': '没解析出来'}
        csv_dict['错误类型'].append(feed_map[str(feedback_type)])
        has_corrected = False
        if feedback_type == 2:
            has_corrected = info == ""
        elif feedback_type == 3:
            has_corrected = info == feedback['newValue']
        elif feedback_type == 4:
            has_corrected = info == feedback['newValue']
        if has_corrected:
            csv_dict['检查字段'].append(f'{check[0]} - {check[1]}')
            csv_dict['检查结果'].append('已解决')
        if not has_corrected:
            csv_dict['检查字段'].append(f'{check[0]} - {check[1]}')
            csv_dict['检查结果'].append('未解决')


def check_feedback_and_experience(info_dict, uuid_name, parsed_file, check_list, csv_dict):
    '''
    检查简历解析结果经历部分是否解决反馈的问题\n
    jira_path: jira信息存储的文件夹路径\n
    file_name: 解析的简历名称\n
    parsed_file: 解析的简历文件\n
    check_list: 简历检查表\n
    csv_dict: 收集到的所有检查结果\n
    返回简历检查结果\n
    '''
    expr_check_list = [check for check in check_list if check[0] != 'info']
    # with open(os.path.join(jira_path, 'jira_info.json'), 'r') as fp:
    #     info_dict = json.load(fp)
    index = info_dict['resume_key'].index(uuid_name)
    for check in expr_check_list:
        if check[2] == 'type' and check[3] == 2:
            continue
        csv_dict['INNO序号'].append(info_dict['inno'][index])
        csv_dict['当前状态'].append(info_dict['status'][index])
        csv_dict['创建人'].append(info_dict['creator'][index])
        csv_dict['经办人'].append(info_dict['assignee'][index])
        csv_dict['简历ID'].append(uuid_name)
        if (check[1] == 'self' and check[3] == 4):
            csv_dict['检查字段'].append(f'{check[0]}')
            csv_dict['错误类型'].append('有缺失问题')
            csv_dict['检查结果'].append('不支持')
        elif check[1] == 'self' and check[3] != 4:
            csv_dict['检查字段'].append(f'{check[0]}')
            csv_dict['错误类型'].append('标注方式问题')
            csv_dict['检查结果'].append('不符合规范')
        elif check[2] == 'type' and check[3] != 2:
            csv_dict['检查字段'].append(f'{check[0]}')
            csv_dict['错误类型'].append('标注方式问题')
            csv_dict['检查结果'].append('不符合规范')
        elif int(check[1]) >= len(parsed_file[check[0]]):
            csv_dict['检查字段'].append(f'{check[0]}')
            csv_dict['错误类型'].append('有缺失问题')
            csv_dict['检查结果'].append('不支持')
        elif check[2] not in parsed_file[check[0]][int(check[1])]:
            csv_dict['检查字段'].append(f'{check[0]} - {check[1]} - {check[2]}')
            csv_dict['错误类型'].append('解析字段缺失')
            csv_dict['检查结果'].append('不支持')
        else:
            info = parsed_file[check[0]][int(check[1])][check[2]]
            feedback = check[3]
            feedback_type = feedback['type']
            feed_map = {'2': '无中生有', '3': '不对劲', '4': '没解析出来'}
            csv_dict['错误类型'].append(feed_map[str(feedback_type)])
            has_corrected = False
            if feedback_type == 2:
                has_corrected = info == ""
            elif feedback_type == 3:
                has_corrected = info == feedback['newValue']
            elif feedback_type == 4:
                has_corrected = info == feedback['newValue']
            if has_corrected:
                csv_dict['检查字段'].append(
                    f'{check[0]} - {check[1]} - {check[2]}')
                csv_dict['检查结果'].append('已解决')
            if not has_corrected:
                csv_dict['检查字段'].append(
                    f'{check[0]} - {check[1]} - {check[2]}')
                csv_dict['检查结果'].append('未解决')


def jira_check_files(jira_path, advice_path, parsed_resume_path):
    '''
    检查解析结果是否修正反馈中的问题\n
    jira_path: jira信息存储的文件夹路径\n
    advice_path: advice数据的文件夹路径\n
    parsed_resume_path: 解析后的简历文件夹路径\n
    返回简历检查结果\n
    '''

    csv_dict = {'INNO序号': [], '当前状态': [], '创建人': [], '经办人': [],
                '简历ID': [], '检查字段': [], '错误类型': [], '检查结果': []}
    parsed_list = os.listdir(parsed_resume_path)
    with open(os.path.join(jira_path, 'jira_info.json'), 'r') as fp:
        info_dict = json.load(fp)
    for parsed in parsed_list:
        try:
            advice = parsed[:-5] + '_advice.json'
            uuid_name = parsed[:36]
            if uuid_name not in info_dict['resume_key']:
                continue
            index = info_dict['resume_key'].index(uuid_name)
            inno = info_dict['inno'][index]
            # print('parsed', parsed, uuid_name, inno)

            advice_filepath = os.path.join(advice_path, advice)
            with open(advice_filepath, 'r', encoding='utf-8') as fp:
                advice_dict = json.load(fp)
            parsed_filepath = os.path.join(parsed_resume_path, parsed)
            with open(parsed_filepath, 'r', encoding='utf-8') as fp:
                parsed_file = json.load(fp)
            filtered_dict = filter_advice_info(advice_dict)
            check_list = make_jira_check_list(filtered_dict)

            check_feedback_and_info(
                info_dict, uuid_name, parsed_file, check_list, csv_dict)
            check_feedback_and_experience(
                info_dict, uuid_name, parsed_file, check_list, csv_dict)
        except:
            print('failed', inno, parsed, traceback.format_exc())
            continue
    return csv_dict


if __name__ == '__main__':
    # 下载jira信息
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='')
    parser.add_argument('--password', default='')
    parser.add_argument('--basedir', default='/mnt/data1/usr/yangzhenling')
    parser.add_argument('--reload', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dev', action='store_true')
    args = parser.parse_args()

    user_name = args.username
    password = args.password
    reload = args.reload
    basedir = args.basedir
    force = args.force
    is_dev = args.dev

    jira_path = os.path.join(basedir, 'jira_info')
    advice_path = os.path.join(basedir, 'advices')
    resume_path = os.path.join(basedir, 'resumes')
    parsed_path = os.path.join(basedir, 'parsed_resumes')

    if reload:

        extract_info_from_jira(user_name, password, jira_path)
        # 下载检查数据
        db_path = '/opt/ai-labs/db.sqlite3'
        extract_data_from_sqlite(jira_path, db_path, advice_path, resume_path)
        # 解析下载简历
        parse_resumes_v2(resume_path, parsed_path)
    # 检查解析简历
    csv_dict = jira_check_files(jira_path, advice_path, parsed_path)
    # 保存和打印检查结果
    csv_path = '/mnt/data1/usr/yangzhenling/csv_folder/jira_check.csv'
    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.width', 180)
    df = pd.DataFrame(csv_dict)
    df.to_csv(csv_path, index=False)
    df = df[df['检查结果'] != '不支持']
    print(df.to_string())
