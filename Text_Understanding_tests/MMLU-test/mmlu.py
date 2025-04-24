from datasets import load_dataset
import subprocess
import json
import re
import csv
from collections import defaultdict
ds = load_dataset("cais/mmlu", "all")
def query_model(question):
    url = "http://10.147.8.37:1025/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "Qwen2.5-72B-Instruct",
        "messages": [{"role": "user", "content": question}],
        "do_sample": True,
        "temperature": 0.6,
        "top_p": 0.95,
        "max_tokens": 16384,
        "stream": False
    }
    curl_command = [
        "curl",
        "-X", "POST",
        "-H", f"Content-Type: {headers['Content-Type']}",
        "-d", json.dumps(data),
        url
    ]
    try:
        result = subprocess.run(curl_command, capture_output = True, text = True, check = True)
        response = json.loads(result.stdout)
        if ("choices" not in response):
            return "Error"
        else:
            return response["choices"][0]["message"]["content"]
    except subprocess.CalledProcessError as e:
        print(f"Curl command failed with error: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse response as JSON: {e}")
        return None
def parse_choices(response):
    patterns = [r'\\boxed\{([A-D])\}', r'\(([A-D])\)']
    result = {"A" : 0, "B" : 0, "C" : 0, "D" : 0}
    for pattern in patterns:
        matches = re.findall(pattern, response)
        if (len(matches)):
            result[matches[-1]] += 1
    choice = max(result, key = result.get)
    for key in result:
        if (key != choice and result[key] == result[choice]):
            return "Invalid"
    return choice
def generate(example) -> dict:
    prompt_prefix = "Please choose the correct answer from among the following options:\n"
    prompt_suffix = "At the end of your response, provide the option you believe is most correct, i.e., one of (A), (B), (C), (D)."
    choices = "\n".join([f"({chr(i + ord('A'))}) {choice}" for i, choice in enumerate(example["choices"])])
    question = example["question"] + "\n" + prompt_prefix + choices + "\n" + prompt_suffix
    subject = example["subject"].rstrip()
    answer = chr(example["answer"] + ord('A'))
    return {
        "question": question,
        "subject": subject, 
        "answer": answer
    }
def full_test(dataset, max_times):
    overall_results = []
    subject_results = defaultdict(list)
    for idx in range(len(dataset)):
        item = generate(dataset[idx])
        question = item["question"]
        answer = item["answer"]
        subject = item["subject"]
        count = {'A' : 0, 'B' : 0, 'C' : 0, 'D' : 0, 'Invalid' : 0}
        for times in range(max_times):
            response = query_model(question)
            count[parse_choices(response)] += 1
        model_choice = 'A'
        for choice in ['B', 'C', 'D']:
            if (count[model_choice] < count[choice]):
                model_choice = choice
        iscorrect = model_choice == answer
        current = {"question index" : idx, "correct answer" : answer, "model_answer" : model_choice, "subject" : subject, "iscorrect" : iscorrect}
        subject_results[subject].append(iscorrect)
        overall_results.append(current)
        print(current)
    statistics = []
    for subject, results in subject_results.items():
        correctnum = sum(results)
        totalnum = len(results)
        statistics.append({"subject" : subject, "correctnum" : correctnum, "totalnum" : totalnum})
    return overall_results, statistics
results_detail, results = full_test(ds["test"], 15)
with open("mmlu.csv", mode = "w", newline = "", encoding = "utf-8") as file:
    fieldnames = ["subject", "correctnum", "totalnum"]
    writer = csv.DictWriter(file, fieldnames = fieldnames)
    writer.writeheader()
    for entry in results:
        writer.writerow(entry)
with open("mmlu_detail.csv", mode = 'w', newline = '', encoding = 'utf-8') as file:
    writer = csv.DictWriter(file, fieldnames = results_detail[0].keys())
    writer.writeheader()
    for row in results_detail:
        writer.writerow(row)