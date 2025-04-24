#!/usr/bin/env python
# coding: utf-8

from utils.grader import grade_answer
import tqdm
import random
import numpy as np
import torch
import pandas as pd
import requests
import time
import logging

# 配置日志记录
logging.basicConfig(
    filename='/data/msit/math-test/test.log',
    level=logging.INFO,
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

seed = 1
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)

system_prompt = """You are a highly knowledgeable mathematics assistant.
Solve the given math problems step by step, explaining your reasoning clearly and concisely.
Ensure the final answer is provided in the requested format and is accurate.
Use the format \\boxed{answer} to present the final result for easy identification.
It is very important that you only use the \\boxed{answer} format."""
user_prompt = """Use the format \\boxed{answer}, where "answer" is the result of the problem."""


def query(input_text):
    url = "http://127.0.0.1:1040/v1/chat/completions"  # 本地 API 地址
    headers = {
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{input_text}\n{user_prompt}"},
    ]
    print("message:", messages)
    data = {
        "messages": messages,
        # "max_tokens": 2000,
        "stream": False,
        "do_sample": True,
        "repetition_penalty": 1.00,
        "temperature": 0.6,
        "top_p": 0.6,
        "top_k": 20,
        "model": "qwen2",  # 模型名称
    }
    while True:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
            
        else:
            # check if there's problem with rate limitation or sensitive word holdback when an example takes too long time
            time.sleep(5)
            continue

# dataset = load_dataset(dataset_name)
def extract_boxed_solution(text: str) -> str | None:
    """
    Extracts the content of the last `\boxed{}` in a given LaTeX-style text.

    Args:
        text (str): The input string containing LaTeX-style content.

    Returns:
        Optional[str]: The extracted content inside the last `\boxed{}` if found 
        and properly matched, otherwise `None`.

    Example:
        >>> extract_boxed_solution("The result is \\boxed{42}.")
        '42'
        >>> extract_boxed_solution("Unmatched \\boxed{42")
        None
    """
    try:
        start_index = text.rindex("\\boxed{")
        content_start = start_index + 7
        bracket_count = 1
        current_pos = content_start

        while bracket_count > 0 and current_pos < len(text):
            if text[current_pos] == "{":
                bracket_count += 1
            elif text[current_pos] == "}":
                bracket_count -= 1
            current_pos += 1

        if bracket_count == 0:
            content = text[content_start : current_pos - 1].strip()
            return content
        else:
            print("Error: Unmatched brackets in the text")
            return None

    except ValueError:
        print("No boxed solution found in the text")
        return None
    except Exception as e:
        print(f"Error processing text: {str(e)}")
        return None
    
df = pd.read_json("/data/msit/MATH-500/test.jsonl", lines=True)
dataset = df[df["level"] <= 3]
dataset = df.to_dict('records')
print(dataset)

results = []
responses = []

for sample in tqdm.tqdm(dataset):

    response = query(sample["problem"])
    print(response)
    results.append([extract_boxed_solution(response)])
    responses.append(response)


# 将多样化解码结果添加到数据集
for i, sample in enumerate(dataset):
    sample["result"] = results[i]
    sample["response"] = responses[i]

df_with_responses = pd.DataFrame(dataset)
df_with_responses.to_json("/data/msit/math-test/mt500withresponses.jsonl", orient="records", lines=True)


# 评估解码的准确性
accuracy = []
for sample in dataset:
    print("result: ", sample["result"])
    print("answer: ", sample["answer"])
    accuracy.append(grade_answer(sample["result"][0], sample["answer"]))
for i, sample in enumerate(dataset):
    sample["accuracy"] = accuracy[i]

# 计算 True 的数量
true_count = sum(accuracy)

# 计算总长度
total_count = len(accuracy)
accuracy_ratio = true_count / total_count

# 记录列表内容
logging.info(f"Accuracy list: {accuracy}")

# 计算列表长度并记录
logging.info(f"true: {true_count}")
logging.info(f"total: {total_count}")
logging.info(f"Accuracy ratio: {accuracy_ratio * 100:.2f}%")