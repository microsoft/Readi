import argparse
from eval_utils import *
import logging


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="choose the dataset.")
    parser.add_argument("--output_file", type=str, required=True, help="the output file name.")
    parser.add_argument("--constraints_refuse", type=bool, default=True, help="LLM may have refuse erorr, enable this option to skip current sample.")
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.INFO)
    if "jsonl" in args.output_file:
        logging.basicConfig(filename=args.output_file.replace(".jsonl",".log"),
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(filename=args.output_file.replace(".json",".log"),
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("time recoder")

    ground_truth_datas, question_string, output_datas = prepare_dataset_for_eval(args.dataset, args.output_file)

    num_right = 0
    num_error = 0
    # output_datas = output_datas[:1000]
    for data in output_datas:
        answers = align(args.dataset, question_string, data, ground_truth_datas)
        if 'cot' in args.output_file:
            results = data['cot_result']
        else:
            results = data['results']

        if check_string(results):
            response = clean_results(results)
            if response=="NULL":
                response = results
            else:
                if response!="" and exact_match(response, answers):
                    num_right+=1
                else:
                    if 'cot' in args.output_file:
                        print(data['question'])
                        print(data['cot_result'])
                        logger.info("question: {}".format(data['question']))
                        logger.info("cot_result: {}".format(data['cot_result']))
                    else:
                        print(data['question'])
                        # print(data['reasoning_chains'])
                        print(data['results'])
                        logger.info("question: {}".format(data['question']))
                        # logger.info("reasoning_chains: {}".format(data['reasoning_chains']))
                        logger.info("results: {}".format(data['results']))
                    num_error+=1
        else:
            response = results
            if type(response)!=str:
                response=""
            if args.constraints_refuse and check_string(response):
                continue
            if response!="" and exact_match(response, answers):
                num_right+=1
            else:
                if 'cot' in args.output_file:
                    print(data['question'])
                    print(data['cot_result'])
                    logger.info("question: {}".format(data['question']))
                    logger.info("cot_result: {}".format(data['cot_result']))
                else:
                    print(data['question'])
                    # print(data['reasoning_chains'])
                    print(data['results'])
                    logger.info("question: {}".format(data['question']))
                    # logger.info("reasoning_chains: {}".format(data['reasoning_chains']))
                    logger.info("results: {}".format(data['results']))
                print()
                num_error+=1

    print("Exact Match: {}".format(float(num_right/len(output_datas))))
    print("right: {}, error: {}".format(num_right, num_error))

    save_result2json(args.dataset, num_right, num_error, len(output_datas))
