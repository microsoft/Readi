from email.policy import default
import sys
import os
from collections import defaultdict
from argparse import ArgumentParser
from tqdm import tqdm
import numpy as np
from config import LLM_BASE
import json
import random
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.utils import run_llm, get_timestamp

DATA_PATH = "data/datasets/tableqa"
PROMPT_PATH = "prompt/table_qa"

MAX_REFINE_TIME = 5

def parse_args():
    parser = ArgumentParser("Tableqa wtq dataset")
    parser.add_argument("--full", action="store_true", help="full dataset.")
    parser.add_argument("--verbose", action="store_true", help="verbose.")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max_token", type=int, default=4096)
    parser.add_argument("--llm", type=str, choices=LLM_BASE.keys(), default="gpt35", help="base LLM model.")
    parser.add_argument("--prompt_retrieve", action="store_true", help="use prompt to retrieve.")
    parser.add_argument("--llm_only", type=bool, default=False, help="llm using the whole table to predict answer.", default=False)
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]
    return args


def question_process(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        data=json.load(f)
    return data


class MetaTable():
    def __init__(self, table_info) -> None:
        self.header_contents = defaultdict(list)
        self.headers = [i.replace('\\n',"").replace('\n',"").lower() for i in table_info['header']]
        self.rows = table_info['rows']
        self.header_str = ", ".join(["\"" + i.replace('\\n',"").replace('\n',"") + "\"" for i in self.headers]).lower()

        for index, fact in tqdm(enumerate(self.rows)):
            for item_index, item in enumerate(fact):
                self.header_contents[self.headers[item_index].replace('\\n',"").replace('\n',"").lower()].append(item.lower())


    def get_header_rows(self, header_name):
        header_name=str(header_name).lower()
        if header_name.lower() not in self.header_str:
            print(header_name)
            print(self.header_contents.keys())
            return []

        if header_name in self.header_contents.keys():
                return self.header_contents[header_name]

        for key in self.header_contents.keys():
            if header_name in key:
                return self.header_contents[key]
        


def get_init_reasoning(question, table):
    prompt = open(
        os.path.join(PROMPT_PATH, f"table_qa_init.md"),
        'r', encoding='utf-8'
    ).read()
    prompt += f"\n\nQuestion:{question}\n" + header_row_list_to_table(table.headers, random.sample(table.rows, 1)[0])
                # "Headers:"+ table.header_str + "\nExample Row:" + str(random.sample(table.rows, 1)[0]).strip("[").strip("]").replace("\'","\"") +"\n"
    prompt += "<Thought>\n"
    entity, headers = call_llm(prompt)
    return entity, headers


def grounding_info(entity, predict_header, table, all_table=False):
    str_predict_header =[str(i) for i in predict_header]
    predict_header = str_predict_header
    predict_header_str = ", ".join(predict_header)
    linerized_table = f"Headers: {predict_header_str}\n"
    linerized_rows = []
    
    if all_table:
        for index in range(len(table.rows)):
            row_contents = "; ".join(["(" + col+ ", " + table.get_header_rows(str(col).lower())[index] + ")" for col in table.headers])
            linerized_rows.append("item "+str(index+1)+": " + row_contents) 
        return linerized_table + "\n".join(linerized_rows)
    
    if len(entity.keys())==0:
        # linearize all rows
        for index in range(len(table.rows)):
            row_contents = "; ".join(["(" + col+ ", " + table.get_header_rows(str(col).lower())[index] + ")" for col in predict_header])
            linerized_rows.append("item "+str(index+1)+": " + row_contents) 
        return linerized_table + "\n".join(linerized_rows)
    
    else:
        for index in range(len(table.rows)):
            row_contents = "; ".join(["(" + col+ ", " + table.get_header_rows(str(col).lower())[index] + ")" for col in predict_header])
            for h, constrains in entity.items():
                for con in constrains:
                    if str(con).lower() in row_contents:
                        linerized_rows.append("item "+str(index+1)+": " + row_contents) 
                        break
                    
        return linerized_table + "\n".join(linerized_rows)

def header_item_str_to_table(input):
    lines = input.split("\n")
    headers = lines[0].split(": ")[1].split(", ")
    items = []

    for line in lines[1:]:
        # get the item values from the line
        values = line.split(": ")[1].split("; ")
        # create an empty list to store the formatted values
        formatted_values = []
        # loop through the values
        for value in values:
            # remove the parentheses and the header name
            header = value.strip("()").split(", ")[0]
            value = value.strip("()").replace(header, "").strip(",").strip()
            # capitalize the first letter of the value
            value = value.capitalize()
            # append the value to the formatted values list
            formatted_values.append(value)
        # append the formatted values list to the items list
        items.append(formatted_values)

    output = ""
    output += "| " + " | ".join(headers) + " |\n"
    output += "| " + " | ".join(["--"] * len(headers)) + " |\n"

    for item in items:
        # add the data row with pipe separators
        output += "| " + " | ".join(item) + " |\n"
    return output


def header_row_list_to_table(header_list, row_list):
    table = ""
    header_list_lower = [i.lower() for i in header_list]
    table += "| " + " | ".join(header_list_lower) + " |\n"
    table += "| " + " | ".join(["--"] * len(header_list_lower)) + " |\n"
    table += "| " + " | ".join(row_list) + " |\n"
    return table


def parse_answer(entity, predict_header, table:MetaTable):
    feedback = ""
    feedback_len = 1
    
    for i, h in enumerate(predict_header):
        predict_header[i] = str(h)
    
    if len(predict_header) < 2:
        feedback += f"{feedback_len}. You must choose at least 2 headers from {str(table.headers)}. The {str(predict_header)} is not enough to answer the question.\n"
        
    wrong_headers = []
    for pred_h in predict_header:
        if str(pred_h).lower() not in table.header_str.lower():
            wrong_headers.append(pred_h)
            feedback += f"{feedback_len}. Header {str(wrong_headers)} not in candidate Headers. You can only choose headers from {str(table.headers)}.\n"
            
    if len(wrong_headers) > 0 or len(predict_header) < 2:
        return [], feedback

    header_contents_values = []
    for i in predict_header:
        header_contents_values += table.get_header_rows(i)
        
    for header, ent in entity.items():
        header = str(header).lower()
        if header.lower() not in predict_header:
            entity={}
            feedback=""
            break
        if type(ent) == int or type(ent) == str:
            ent = [str(ent)]
            entity[header] = ent
            
        for e in ent:
            if str(e).lower() not in table.get_header_rows(header):
                entity={}
                feedback=""
                break

    if len(feedback)==0:
        return grounding_info(entity, predict_header, table), feedback
    else:
        return grounding_info({}, predict_header, table), feedback


def call_llm(prompt):
    MAX_RETRY_TIME = 5
    for _ in range(MAX_RETRY_TIME):
        try:
            response = run_llm(prompt, options.temperature, options.max_token, options.openai_api_keys ,options.LLM_type)
            entities = response.split("Constrains:")[-1]
            entities = eval(entities)
            relations = response.split("Constrains:")[0].split("Chosen Headers:")[-1].strip('\n').strip()
            headers = eval(relations)
            
            assert type(headers) == list and type(entities) == dict 
            break
        except Exception as e:
            entities={}
            headers=[]
            continue
        
    return entities, headers


def reasoning_llm(question, instantiate_path):
    MAX_RETRY_TIME = 10
    prompt = open(
        os.path.join(PROMPT_PATH, f"table_qa_reasoning_wikitq.md"),
        'r', encoding='utf-8'
    ).read()
    
    append = f"""\nQuestion: {question}\n<Table>\n{instantiate_path}\n</Table>\n<Thought>\n"""
    prompt += append
    for _ in range(MAX_RETRY_TIME):
        try:
            response = run_llm(prompt, options.temperature, options.max_token, options.openai_api_keys, options.LLM_type)
            answer = response.split("Answer:")[-1].strip('\n').strip()
            if answer[0]=="[" and answer[-1]==']' and "\'" in answer.strip("[").strip("]").strip("\"").strip("\'"):
                answer = [answer.strip("[").strip("]").strip("\"").strip("\'")]
            else:
                answer = eval(answer)
                
            assert type(answer) == list and len(answer) > 0
            break
        except Exception as e:
            print("****************************************************")
            print(answer)
            print("****************************************************")
            answer = []
            continue
    return answer

def refine_reasoning(question, entity, predict_header, feedback, table):
    prompt = open(
        os.path.join(PROMPT_PATH, f"table_qa_refine.md"),
        'r', encoding='utf-8'
    ).read()
    
    entity_str = str(entity)
    predict_header_str = str(predict_header)
    
    # header_example = "Headers:"+ table.header_str + "\nExample Row:" + str(random.sample(table.rows, 1)[0]).strip("[").strip("]").replace("\'","\"")
    header_example = header_row_list_to_table(table.headers,random.sample(table.rows, 1)[0])

    append = f"""\nQuestion:{question}\n{header_example}>>>>>Wrong Answer:\nChosen Headers: {predict_header_str}\nConstrains: {entity_str}\n<Feedback>\n{feedback}</Feedback>\n<Thought>\n"""
    prompt += append
    print(f"Question:{question}, Feedback:{feedback}")
    answer = call_llm(prompt)
    print(f"refined entity:{answer[0]},  refined header list:{answer[1]}")
    return answer


def norm_string(answer):
    res = str(answer).encode("utf-8").decode("utf-8").lower().replace("\u2013","-").replace("\u2212", "-").replace("years", "").replace("season","").replace("_", "").replace("year", "").replace("months", "").replace("$", "").replace("month", "").replace("days", "").replace("day", "").replace(",","").replace("  "," ").replace("(","").replace(")","").replace("+","").replace("-","").replace("/","").replace("\'", "").replace("\"", "").replace("*", "").replace(" ", "").lower()
    if res.endswith(".0") or res.endswith(" m"):
        res=res[:-2]
    if res.startswith("0"):
        res=res[1:]
    if res.startswith("l "):
        res=res[2:]
    if res.endswith(" mi") or res.endswith(" pb"):
        res=res[:-3]
    return res    
    
    
def evaluate(answer_list, ground_truth):
    """return hit, coverage"""
    answers = set([norm_string(ans) for ans in answer_list])
    ground_truths = set([norm_string(ans) for ans in ground_truth])
    intersect = answers.intersection(ground_truths)
    coverage = len(intersect) / len(ground_truths)
    hit = 1 if len(intersect) > 0 else 0
    return hit, coverage


def main():
    dataset = question_process(os.path.join(
        DATA_PATH,
        f'wikitq_test.json'
    ))

    if not options.full:
        dataset = dataset

    metrics = {
        'hit':[],
        'coverage':[]
    }

    f = open(f"results/tableqa/wikitqa_{get_timestamp()}_{options.llm}.jsonl", 'w+', encoding='utf-8')
    for question_dict in tqdm(dataset):
        question = question_dict["statement"].lower() if 'statement' in question_dict else question_dict['question'].lower()
        question = question + "?" if not question.endswith("?") else question
        table_info = question_dict['table']

        table = MetaTable(table_info)
        ground_truth = question_dict['answer_text']
        
        entity, predict_header = get_init_reasoning(question, table)
        if options.verbose:
            print(f"Question:{question}")
            print(f"Reasoning Path:entity - {entity}, header - {predict_header}")
        refine = 0

        instantiate_paths = []
        feedbacks = []
        answer_list = []
        
        if options.llm_only:
            instantiate_path = grounding_info(entity, predict_header, table, all_table=True)
            answer = reasoning_llm(question, instantiate_path)
            answer_list.extend(answer)
        else:
            while refine < MAX_REFINE_TIME:
                instantiate_path, feedback = parse_answer(entity, predict_header, table)
                instantiate_paths.append(str((instantiate_path, entity, predict_header)))
                feedbacks.append(feedback)
                
                if feedback=="":
                    answer = reasoning_llm(question, instantiate_path)
                    answer_list.extend(answer) 
                    break

                if options.verbose:
                    print(f"{answer_list}, {f'feedback: {feedback}' if feedback else ''}")
                    print(f"Refine:{refine}")

                entity, predict_header = refine_reasoning(question, entity, predict_header, feedback, table)
                refine += 1

        if answer_list == [] or answer_list == [""] or answer_list[0]=="" or answer_list[0]=="none" or answer_list[0]=="unknown":
            answer_list = []
            instantiate_path = grounding_info(entity, predict_header, table, all_table=True)
            answer = reasoning_llm(question, instantiate_path)
            answer_list.extend(answer) 

        hit, coverage = evaluate(answer_list, ground_truth)
        info = {
            'question':question,
            'answer':answer_list,
            'ground_truth':ground_truth,
            'history':instantiate_paths,
            'feedback':feedbacks,
            'hit':hit,
            'coverage':coverage,
        }
        d = json.dumps(info)
        f.write(d + '\n')

        metrics["hit"].append(hit)
        metrics["coverage"].append(coverage)
        print(f"hit:{np.mean(metrics['hit'])}")
        print(f"coverage:{np.mean(metrics['coverage'])}")

    f.close()
    print("\n" + "*" * 20 + "\n")
    print(f"hit:{np.mean(metrics['hit'])}")
    print(f"coverage:{np.mean(metrics['coverage'])}")

if __name__ == '__main__':
    options = parse_args()
    main()
