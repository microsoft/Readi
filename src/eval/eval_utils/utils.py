import os
import json
import re
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.path.join(os.getcwd(), 'dangle_over_ground/src'))
from config import *


def prepare_dataset_for_eval(dataset, output_file):
    dataset_path = get_dataset_file(dataset)
    with open(dataset_path, 'r', encoding='utf-8') as f:
        datas = json.load(f)
    question_string = get_question_string(dataset)

    output_datas= []

    if output_file.endswith(".json"):
        with open(output_file, encoding='utf-8') as f:
            output_datas = json.load(f)

    elif output_file.endswith(".jsonl"):
        # print(output_file)
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                # print(line)
                json_obj = json.loads(line)
                output_datas.append(json_obj)

    return datas, question_string, output_datas


def align(dataset_name, question_string, data, ground_truth_datas):
    answer_list= []
    origin_data = [j for j in ground_truth_datas if j[question_string] == data['question']][0]
    if dataset_name.startswith(CWQ):
        if 'answers' in origin_data:
            answers = origin_data["answers"]
        else:
            answers = origin_data["answer"]

        if type(answers)==str:
            answer_list.append(answers)
        else:
            for answer in answers:
                if type(answer)==str:
                    alias=[answer]
                else:
                    alias = answer['label']
                    # ans = answer['answer']
                    # alias.append(ans)
                answer_list.extend(alias)

    elif dataset_name.startswith(WEBQSP):
        answer_list = origin_data['Answers'] + origin_data['Aliases']
        # answers = origin_data["Parses"]
        # for answer in answers:
        #     for name in answer['Answers']:
        #         if name['EntityName'] == None:
        #             answer_list.append(name['AnswerArgument'])
        #         else:
        #             answer_list.append(name['EntityName'])

    elif dataset_name.startswith(GRAILQA):
        answers = origin_data["answer"]
        for answer in answers:
            if "entity_name" in answer:
                answer_list.append(answer['entity_name'])
            else:
                answer_list.append(answer['answer_argument'])

    elif dataset_name == 'simpleqa':
        answers = origin_data["answer"]
        answer_list.append(answers)

    elif dataset_name == 'qald':
        answers = origin_data["answer"]
        for answer in answers:
            answer_list.append(answers[answer])

    elif dataset_name == 'webquestions':
        answer_list = origin_data["answers"]

    elif dataset_name == 'trex' or dataset_name == 'zeroshotre':
        answers = origin_data["answer"]
        answer_list.append(answers)

    elif dataset_name == 'creak':
        answer = origin_data['label']
        answer_list.append(answer)

    return list(set(answer_list))

def check_string(string):
    return "{" in string

def clean_results(string):
    if "{" in string:
        start = string.find("{") + 1
        end = string.find("}")
        content = string[start:end]
        return content
    else:
        return "NULL"


def check_refuse(string):
    refuse_words = ["however", "sorry"]
    return any(word in string.lower() for word in refuse_words)


def exact_match(response, answers):
    clean_result = response.strip().replace(" ","").lower()
    for answer in answers:
        clean_answer = answer.strip().replace(" ","").lower()
        # if clean_result == clean_answer or clean_result in clean_answer or clean_answer in clean_result:
        if clean_result == clean_answer or clean_answer in clean_result:
            return True
    return False

def save_result2json(dataset_name, num_right, num_error, total_nums, method="ToG"):
    results_data = {
        'dataset': dataset_name,
        'method': method,
        'Exact Match': float(num_right/total_nums),
        'Right Samples': num_right,
        'Error Sampels': num_error
    }
    with open(os.path.join(RESULT_PATH, dataset_name, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(results_data, f, ensure_ascii=False, indent=4)

def extract_content(s):
    matches = re.findall(r'\{(.*?)\}', s)
    if len(matches) >= 2 and matches[0].lower() == 'yes':
        return matches[1]
    elif len(matches) >= 1:
        return matches[0]
    else:
        return 'NULL'