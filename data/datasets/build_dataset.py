import os
import json

def readjson(file_name):
    with open(file_name, encoding='utf-8') as f:
        data=json.load(f)
    return data

def savejson(file_name, new_data):
    with open(file_name, mode='w',encoding='utf-8') as fp:
        json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)


def filter_grail(dataset):
    # filter empty topic entity
    filtered = []
    for data in dataset:
        if len(data['topic_entity']) == 0:
            continue
        filtered.append(data)
    return filtered

def main():
    dataset = readjson("grailqa_dev_pyql_topic_entities.json")
    filtered = filter_grail(dataset)
    savejson(os.path.join("grailqa_dev_filter_empty_topic_entity.json"), filtered)



if __name__=='__main__':
    main()