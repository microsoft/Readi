import argparse
from eval_utils import *
import logging
# from utils import savejson


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="choose the dataset.")
    parser.add_argument("--output_file", type=str, required=True, help="the output file name.")
    args = parser.parse_args()

    # logging.getLogger().setLevel(logging.INFO)
    # if "jsonl" in args.output_file:
    #     logging.basicConfig(filename=args.output_file.replace(".jsonl",".log"),
    #                     format='%(asctime)s %(levelname)-8s %(message)s',
    #                     level=logging.INFO,
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # else:
    #     logging.basicConfig(filename=args.output_file.replace(".json",".log"),
    #                     format='%(asctime)s %(levelname)-8s %(message)s',
    #                     level=logging.INFO,
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    # logger = logging.getLogger("time recoder")

    ground_truth_datas, question_string, output_datas = prepare_dataset_for_eval(args.dataset, args.output_file)

    num_right = 0
    num_error = 0
    # output_datas = output_datas[:1000]
    eval_result = []
    for data in output_datas:
        answers = align(args.dataset, question_string, data, ground_truth_datas)
        if 'cot' in args.output_file:
            results = data['cot_result']
        else:
            results = data['results']


        if check_string(results):
            response = clean_results(results)
            if type(response)!=str:
                response=""
            if response=="NULL":
                response = results
            else:
                if response!="" and hit1(response, answers):
                    num_right+=1
                    eval_result.append(1)
                else:
                    num_error+=1
        else:
            response = results
            if type(response)!=str:
                response=""
            if response!="" and hit1(response, answers):
                num_right+=1
                eval_result.append(1)
            else:
                num_error+=1
                eval_result.append(0)

    print("Exact Match: {}".format(float(num_right/len(output_datas))))
    print("right: {}, error: {}".format(num_right, num_error))

    save_result2json(args.dataset, num_right, num_error, len(output_datas))
