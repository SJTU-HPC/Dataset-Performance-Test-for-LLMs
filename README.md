# Dataset-Performance-Test-for-LLMs
本项目为上海交通大学交我算「轻量级大模型测评」项目的测试代码库，系统整合了多模态与文本大模型领域的主流评测数据集官方代码，我们对这些代码基于本地部署模型进行了适配，代码涵盖：

## 多模态大模型评估测试集
- [MME](https://github.com/BradyFU/Awesome-Multimodal-Large-Language-Models)：视觉理解综合能力评测框架

- [MM-Vet](https://github.com/yuweihao/MM-Vet)：视觉理解综合能力评测框架

- [MMMU](https://github.com/MMMU-Benchmark/MMMU)：面向大学级别的多学科多模态理解和推理能力评测框架

- [MathVista](https://github.com/lupantech/MathVista)：数学推理能力测试集

- [POPE](https://github.com/RUCAIBox/POPE)：目标检测幻觉评估工具

## 文本大模型评估测试集
- [MMLU](https://github.com/Helw150/mmlu)：英文跨学科知识评测框架

- [C-Eval](https://github.com/hkust-nlp/ceval)：中文跨学科知识评测框架

- [MATH-500](https://github.com/SorenDreano/MATH-500-subset-qwen2-answers-evaluated-by-open-PRM)：数学竞赛级问题测评

- [HumanEval](https://github.com/openai/human-eval)：代码生成能力测试

- [GPQA-Diamond](https://github.com/idavidrein/gpqa)：博士级科学问题理解和推理能力评估

# 项目目录结构

```
├── LVLM-datasets
│   ├── ...
├── LLM-datasets/
│   ├── MATH-500-test/
│   │   ├── main.py                #运行代码
│   │   └── utils/                 #原始工具代码
│   ├── C-Eval-test/
│   │   └── ...
│   ├── gpqa-test/
│   │   ├── ...
│   ├── HumanEval-test/
│   │   ├── ...
│   └── MMLU-test/
│       └── ...


```

# 项目测试环境
ARM + 昇腾NPU  
OS：openEuler 22.03 LTS  
CPU: kunpeng 920  
NPU：Ascend 910B    

# 评测工具集使用方法

## 依赖环境 
前往 [昇腾社区/开发资源](https://www.hiascend.com/developer/ascendhub/detail/af85b724a7e5469ebd7ea13c3439d48f) 下载适配目标模型的镜像包：如 1.0.0-800I-A2-py311-openeuler24.03-lts  

## 测试示例
以``MATH-500``测试集的使用为例：  
```
python ~/LLM-datasets/MATH-500-test/main.py
```
