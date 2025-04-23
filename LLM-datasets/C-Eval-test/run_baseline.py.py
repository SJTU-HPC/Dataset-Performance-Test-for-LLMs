import os
from datasets import load_dataset
import subprocess
import json
import re
import csv
subjects = ['accountant', 'advanced_mathematics', 'art_studies', 'basic_medicine', 'business_administration', 'chinese_language_and_literature', 'civil_servant', 'clinical_medicine', 'college_chemistry', 'college_economics', 'college_physics', 'college_programming', 'computer_architecture', 'computer_network', 'discrete_mathematics', 'education_science', 'electrical_engineer', 'environmental_impact_assessment_engineer', 'fire_engineer', 'high_school_biology', 'high_school_chemistry', 'high_school_chinese', 'high_school_geography', 'high_school_history', 'high_school_mathematics', 'high_school_physics', 'high_school_politics', 'ideological_and_moral_cultivation', 'law', 'legal_professional', 'logic', 'mao_zedong_thought', 'marxism', 'metrology_engineer', 'middle_school_biology', 'middle_school_chemistry', 'middle_school_geography', 'middle_school_history', 'middle_school_mathematics', 'middle_school_physics', 'middle_school_politics', 'modern_chinese_history', 'operating_system', 'physician', 'plant_protection', 'probability_and_statistics', 'professional_tour_guide', 'sports_science', 'tax_accountant', 'teacher_qualification', 'urban_and_rural_planner', 'veterinary_medicine']
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
def generate(item) -> dict:
    prompt_prefix = "对于下面的问题，请在给出的四个选项中选择最符合问题描述的答案：\n"
    prompt_suffix = "在解答的最后，请明确你选择的答案的序号。"
    choices = ""
    for choice in ["A", "B", "C", "D"]:
        choices += f"({choice}) {item[choice]}" + "\n"
    question = prompt_prefix + item["question"] + "\n" + choices + prompt_suffix
    return {
        "question": question,
        "answer": item["answer"]
    }
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
def full_test(dataset, max_times):
    correctnum = 0
    results = []
    for idx in range(len(dataset)):
        item = generate(dataset[idx])
        question = item["question"]
        answer = item["answer"]
        count = {'A' : 0, 'B' : 0, 'C' : 0, 'D' : 0, 'Invalid' : 0}
        for times in range(max_times):
            response = query_model(question)
            count[parse_choices(response)] += 1
        model_choice = 'A'
        for choice in ['B', 'C', 'D']:
            if (count[model_choice] < count[choice]):
                model_choice = choice
        iscorrect = model_choice == answer
        correctnum += iscorrect
        current = {"question index" : idx, "correct answer" : answer, "model_answer" : model_choice, "iscorrect" : iscorrect}
        results.append(current)
        print(current)
    return correctnum, len(dataset), results
statistics = []
verbose = []
for subject in subjects:
    ds = load_dataset("ceval/ceval-exam", subject)
    print(f"[subject: {subject}]")
    correctnum, totalnum, results = full_test(ds["val"], 15)
    verbose += results
    current = {"subject" : subject, "correctnum" : correctnum, "totalnum" : totalnum}
    print(current)
    print("")
    statistics.append(current)
with open("ceval.csv", mode = "w", newline = "", encoding = "utf-8") as file:
    fieldnames = ["subject", "correctnum", "totalnum"]
    writer = csv.DictWriter(file, fieldnames = fieldnames)
    writer.writeheader()
    for entry in statistics:
        writer.writerow(entry)
with open("ceval_detail.csv", mode = 'w', newline = '', encoding = 'utf-8') as file:
    writer = csv.DictWriter(file, fieldnames = results[0].keys())
    writer.writeheader()
    for row in results:
        writer.writerow(row)