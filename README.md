# requirements.txt包含了必要的库 
# data: 数据集和中间文件(init_plan)
# results: 结果文件
# src: 主要代码
    ### get_relation_path.py  input为输入数据集 output为输出init_plan存放的位置
    ### predict_answer_graph.py  根据init_plan进行grounding 
    ### llm_reasoning_with_kb.py LLM 根据KB子图来推理答案的模块,上个月做的.目前是做了对三元组知识的推理. 后续可以考虑在refine过程中直接出答案,以及 以路径为输入"->"的格式

    下面的不用管 debug会自动跳过去,主要功能流程在下面实现

    ### build_qa_input.py   开始加工数据 根据init plan输入grounding模块 , 根据grounding的结果refine的代码都在这里

# utils: 工具
    ### freebase_func.py 查询引擎的工具


# 跑通流程    
    1. ***查询引擎搭建*** (注: 略费事,需要下载很大的文件)
    ## 根据这个教程 https://github.com/dki-lab/Freebase-Setup (先clone他的代码, 按照他们的readme - 下载一个freebase opensource, 并且要下载一个他们的virtuoso_db文件, 然后在一个指定端口上运行python命令)

    ## 将对应的端口设置到freebase_func.py (e.g. SPARQLPATH = "http://127.0.0.1:3001/sparql")

    2. 运行 get_relation_path.py (生成initial plan  我已经生成了一个 这一步可以跳过)

    在166行, 修改input_file 数据集路径 , outputfile 输出文件路径. 目前只跑前[:100]条数据 (可以根据需要修改)

    args.LLM_type是LLM的类型 GPT3.5 or GPT4,可以根据cloudgpt的模型名称修改.

    get_relation_path(input_file="/home/v-sitaocheng/demos/dangle_over_ground/data/datasets/cwq_test.json", output_file="/home/v-sitaocheng/demos/dangle_over_ground/data/initial_plan/cwq_test_1221.json")


    3. 运行predict_answer_graph.py得到子图. (主要的refine流程在这里,  因为是在RoG的基础上修改的  代码写的也比较杂乱 请见谅 )
        目前在优化这个模块(目标是recall越高越好 且 子图规模越低越好)

    注意两个地方
        修改 args.init_plan_path(initial Plan的位置, 这个文件在get_relation_path时已经存了必要的信息(topic entity 和initial plan))
        修改 args.output_file_name(输出文件的名字)
        修改 args.llm_engine(指定用gpt3.5还是gpt4来refine)

        具体流程介绍:
            ` main是直接用缓存的图跑的版本
            `main_engine是我自己实现的用引擎跑的版本,这个文件主要做数据集的读取,把每一个是数据传到 处理函数prediction_graph_engine中
                prediction_graph_engine则是对单个数据进行前处理, 然后调用 input_builder.get_graph_knowledge_LLM_revised_engine(reasoning_path_LLM) 来进行grounding ,最后后处理保存结果

            input_builder.get_graph_knowledge_LLM_revised_engine这个函数主体在build_qa_input.py文件中,这个文件是整个项目最重要的文件,处理了grounding 和refine的交互过程(也是我写的比较杂的地方)
                get_graph_knowledge_LLM_revised_engine:
                    a. 对每一个entity的plan, 首先grounding每一个关系(召回top 5),然后将这些输入grounding引擎(apply_rules_LLM_one_path_engine),这个引擎会返回reasoning path(如果整条路都grounding成功), grounded_knowledge(整个过程中成功grounding的知识),ungrounded_knowledge_dict(grounding失败的点周围的关系)
                    
                    b. 开始进行refine(这里可以选择硬性判定停止还是继续refine 硬性的意思的如果这条路成功了,并且末尾不是cvt,那就停止refine)
                        
                        LLM_refine_and_stop_condition函数拼接LLM的prompt并进行refine以及繁琐的后处理工作 (如果硬性停止的话,我另外实现了一个函数LLM_refine,可以直接用这个, 看效果说话)
                            
                            这个函数会对返回的reasoning path, grounded konwledge 和 ungrounded knowledge dict进行处理,拼接prompt的输入
                                ` 这里注意,如果grounding的知识太多了(比如法国的地区),我会进行采样(合理性:只要LLM知道这个relation能grounding到他想要的东西就行了, e.g.他想要地区,返回一些地区就行了).
                                ` 对于cvt,目前的方案是全部替换成<cvt><cvy/>中间啥也不加.然后对知识进行去重操作
                                ` 对于候选关系列表,我不会给LLM传一个dict,而是传一个list,并且做了top 35相似度的筛选.(dict太大了,很多同类型实体的关系列表是相似的)
                            
                            对于返回的结果,会根据情况进行后处理,包括几种不同的实现方案:
                                对于函数形式, 会对函数调用情况和执行结果进行检查和判别,不满足条件的会重新生成
                                对于字符串形式 (e.g.如果要修改,改后不能和改之前完全一样 )
                                对于LLM自己决定是否停止 (e.g. cvt结尾的不能停止)

                    c. 结果拼接 (包括merge操作)
                        `如果LLM或硬性条件判定这条路结束了(or refine超过某次数),那么进行这条路的知识整合
                            ` 如果reasoning path非空,说明grounding成功,加入该实体的路径
                                同时会把grounded knowledge当中最长的也加进去(防止reasoning path为空,没有任何知识的情况) 只要最长的是greedy的操作
                        ` 当所有topic entity都结束了, 会进行merge操作
                            如果只有一个topic entity  直接返回 存储结果
                            如果有多个 那么答案会被多条路限制,需要merge操作

                                ` merge的实现: 先判断多个topic entity 对应的路径是否有entity的交集
                                    
                                    如果有交集,直接对有交集的"两个"集合取交集,然后继续和第三个进行类似的操作

                                    如果没有交集,会进行一次判断(很用可能其中一个实体的知识爆炸了):
                                        如果有某个topic entity中路径超过了50条,那么我会把这个实体开头的知识全丢了(我认为对答题无用)
                                        剩下的知识我会留下来取并集


    4. llm_reasoning_with_kb.py 根据得到的子图进行问答的模块
    
    三个要注意的地方:
    ## args.LLM_type是LLM的类型 GPT3.5 or GPT4,可以根据cloudgpt的模型名称修改. 
    ## file_index 文件后缀,注意每次根据需要记得改一下,不然可能会覆盖原来的文件哈  (也可以直接换成时间戳)
    ##     reasoning_with_ROG(file_name='/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/RoG/test/_home_v-sitaocheng_demos_llm_hallu_reasoning-on-graphs_results_gen_rule_path_RoG-cwq_RoG_test_predictions_3_False_jsonl/predictions_kg_with_input_llm_cwq100_path_onePath_gpt35_1228_llm_stop_longest_only_multi_merge_function_cvt.jsonl', file_index) 这个函数的file_name参数记得换成上一步之前生成的子图文件.

    其他: 目前的做法是根据三元组来回答(知识表示成triple形式),尝试过path的形式(->连接实体和关系)效果不如这个. 可以根据需要在reasoning_with_ROG中修改prompt.

    5. sub_graph_evaluation.py 评估子图规模\答案召回率

    两个要注意的地方:
        修改子图路径
        file_path="/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/RoG-cwq/RoG/test/_home_v-sitaocheng_demos_llm_hallu_reasoning-on-graphs_results_gen_rule_path_RoG-cwq_RoG_test_predictions_3_False_jsonl/predictions_kg_with_input_llm_cwq100_path_onePath_initial_path.jsonl"
    
        如果换数据集的话记得修改golden文件 (注意: 不同数据集答案的dict字段可能不同,要到calculate_answer_coverage_rate函数 268行修改相应字段名字)
        golden_path="/home/v-sitaocheng/demos/llm_hallu/ToG/data/cwq.json"  

        直接运行会输出 over\one path\multi path的子图召回情况(覆盖率+子图大小)




