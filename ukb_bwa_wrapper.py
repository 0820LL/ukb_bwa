#!/usr/bin/env python3

import argparse
import os
import json
import sys
import time
import logging

def send_json_message(analysis_path:str, send_message_script: str, message: dict, step_file_name:str) -> None:
    # single quotation marks are the must
    os.system('bash {} \'{}\' 1>>final_message.log 2>&1'.format(send_message_script, json.dumps(message, ensure_ascii=False, indent=2)))
    logging.info('bash {} \'{}\' 1>>final_message.log 2>&1'.format(send_message_script, json.dumps(message, ensure_ascii=False, indent=2)))
    with open('{}/{}'.format(analysis_path, step_file_name), 'w') as step_f:
        json.dump(message, fp=step_f, ensure_ascii=False, indent=4)

def steward(config_file_path:str, ukb_bwa_path:str, send_message_script:str) -> None:
    analysis_path = os.path.dirname(config_file_path)
    os.chdir(analysis_path)
    # get paramters from the config.json
    with open(config_file_path, 'r') as config_f:
        config_d = json.load(config_f)
    params_d = {
        'fastq_1'    : config_d['ukbParams']['fastq1'],
        'fastq_2'    : config_d['ukbParams']['fastq2'],
        'bwa_index'  : config_d['ukbParams']['BWA-MEN'],
        'threads_num': config_d['ukbParams']['numberOfThreads']
    }
    if params_d['threads_num'] == '':
        params_d['threads_num'] = 1
    # make the params.json file
    params_file_path = '{}/params.json'.format(analysis_path)
    with open(params_file_path, 'w') as params_f:
        json.dump(params_d, params_f, ensure_ascii=False, indent=4)
    ukb_bwa_command = 'nextflow run -offline -profile singularity -bg -params-file {} {} >> run_log.txt'.format(params_file_path, ukb_bwa_path)
    return_value = os.system(ukb_bwa_command)
    logging.info(ukb_bwa_command)
    logging.info('return value:{}\n'.format(str(return_value)))
    time.sleep(20)
    # send the result files 
    feedback_dict = {
        'uuid'          : config_d['uuid'],
        'ukbId'         : config_d['ukbId'],
        'ukbToolsCode'  : config_d['ukbToolCode'],
        'ukbToolName'   : config_d['ukbToolName'],
        'pipeline'      : 'ukb',
        'analysisStatus': '',
        'startDate'     : time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        'endDate'       : '',
        'error'         : 0,
        'taskName'      : 'Step'
    }
    if return_value == 0 and os.path.exists('{}/results'.format(analysis_path)):
        feedback_dict['analysisStatus'] = '分析开始'
        feedback_dict['endDate']        = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        feedback_dict['error']          = 0
        send_json_message(analysis_path, send_message_script, feedback_dict, 'start.json')
    else:
        feedback_dict['analysisStatus'] = '分析开始'
        feedback_dict['endDate']        = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        feedback_dict['error']          = 1
        send_json_message(analysis_path, send_message_script, feedback_dict, 'start.json')
        sys.exit()
    flag = 0
    while True:
        execution_trace_file = '{}/results'.format(analysis_path)
        if 'pipeline_info' in os.listdir(execution_trace_file):
            execution_trace_file += '/pipeline_info'
            for file in os.listdir(execution_trace_file):
                if file.startswith('execution_trace'):
                    execution_trace_file += '/{}'.format(file)
                    flag = 1
                    break
            if flag == 1 :
                break
        time.sleep(5)
    feedback_dict['analysisStatus'] = '分析结果'
    feedback_dict['endDate']        = ''
    feedback_dict['taskName']       = 'Result'
    feedback_dict['error']          = 0
    feedback_dict['data']           = []
    flag = 0
    while True:
        with open(execution_trace_file, encoding = 'UTF-8') as trace_f:
            for line in trace_f:
                if 'BWA_MEM' in line:
                    if 'COMPLETED' in line:
                        feedback_dict['endDate'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        feedback_dict['error'] = 0
                        for file in os.listdir('{}/results'.format(analysis_path)):
                            if file.endswith('sam'):
                                bwa_res_sam = '{}/results/{}'.format(analysis_path, file)
                        report_download_dict = {
                            'sort' : 1,
                            'title': '分析结果文件',
                            'text' : [
                                {
                                    'sort'   : 1,
                                    'title'  : '分析结果sam文件',
                                    'content': '分析结果sam文件：#&{}'.format(bwa_res_sam),
                                    'postDes': '',
                                    'memo'   : '',
                                    'preDes' : ''
                                }
                            ], 
                            'memo'     : '',
                            'subtitle1': '',
                            'subtitle2': ''
                        }
                        feedback_dict['data'].append(report_download_dict)
                    else:
                        feedback_dict['endDate'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        feedback_dict['error'] = 1
                    send_json_message(analysis_path, send_message_script, feedback_dict, 'result.json')
                    flag = 1 
                    break
                else:
                    time.sleep(5)
            if flag == 1:
                break


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument('--cfp', required=True, help='the full path of the config.json')
    parser.add_argument('--ukb_bwa_path', required=True, help='the full path of the ukb_bwa')
    parser.add_argument('--send_message_script', required=True, help='the full path for the shell script: sendMessage.sh')
    args = parser.parse_args()
    config_file_path=args.cfp
    if os.path.isabs(config_file_path):
        pass
    else:
        config_file_path = os.path.abspath(os.path.basename(config_file_path))
    ukb_bwa_path = args.ukb_bwa_path
    send_message_script = args.send_message_script
    # logging
    log_file = '{}/ukb_bwa.log'.format(os.path.dirname(config_file_path))
    logging.basicConfig(
        filename=log_file, 
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    steward(config_file_path, ukb_bwa_path, send_message_script)


if __name__ == '__main__':
    main()