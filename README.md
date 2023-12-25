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
    1. 
    要根据这个教程 https://github.com/dki-lab/Freebase-Setup (先clone他的代码, 按照他们的readme - 下载一个freebase opensource, 并且要下载一个他们的virtuoso_db文件, 然后在一个端口上运行python命令)
    然后将对应的端口设置到freebase_func.py (e.g. SPARQLPATH = "http://127.0.0.1:3001/sparql")

    2. 运行 get_relation_path.py (生成initial plan  我已经生成了一个 这一步可以跳过)

    3. 运行predict_answer_graph.py得到子图. 目前在优化这个模块(目前recall一般 且 子图规模比较大)



