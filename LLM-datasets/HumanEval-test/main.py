from utils.data import write_jsonl, read_problems
import requests
import json
import time
from utils.evaluate_functional_correctness import entry_point



def generate_one_completion(prompt):
    url = "http://127.0.0.1:1339/v1/chat/completions"  # 本地 API 地址
    headers = {
        "Content-Type": "application/json"
    }

    messages =  [
        {"role": "system", "content": "You are a coding assistant, The sample code output is: ```python [code] ``` "},
        {"role": "user", "content": prompt}
    ]

    print("message:", messages)
    data = {
        "messages": messages,
        "max_tokens": 40960,
        "stream": False,
        "do_sample": True,
        "repetition_penalty": 1.00,
        "temperature": 0.6,
        "top_p": 0.6,
        "top_k": 20,
        "model": "llama",  # 模型名称
    }
    while True:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            response_content = response.json()['choices'][0]['message']['content'].strip()
            return response_content
            
        else:
            # check if there's problem with rate limitation or sensitive word holdback when an example takes too long time
            time.sleep(5)
            continue
    


def main():
    # 1. 读取问题集（也可使用自定义的 problem_file）
    problems = read_problems()

    # 2. 针对每个 task_id，生成对应数量的样本
    num_samples_per_task = 2
    samples = []
    for task_id in problems:
        print("task_id: ", task_id)
        prompt = problems[task_id]["prompt"]
        for _ in range(num_samples_per_task):
            completion = generate_one_completion(prompt)
            samples.append(dict(task_id=task_id, completion=completion))
            print('completion: ',completion)
        # break

        # 3. 将生成的样本保存为 JSON Lines 文件
        write_jsonl("samples.jsonl", samples)

    # 4. 评估示例（如需真实执行评估，请先在 execution.py 中启用执行）
    #    命令行运行: evaluate_functional_correctness samples.jsonl
    entry_point("samples.jsonl")
    print("生成完毕！请使用 evaluate_functional_correctness 命令评估样本。")

if __name__ == "__main__":
    main()
