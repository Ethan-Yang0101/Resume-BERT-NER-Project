from transformers import BertForTokenClassification, TrainingArguments, Trainer
from transformers import DataCollatorForTokenClassification, AutoTokenizer
from datasets import load_dataset, load_metric
import numpy as np


def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"], truncation=True,
        is_split_into_words=True, max_length=500)
    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            # 将特殊符号的标签设置为-100，以便在计算损失函数时自动忽略
            if word_idx is None:
                label_ids.append(-100)
            # 把标签设置到每个词的第一个token上
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            # 对于每个词的其他token也设置为当前标签
            else:
                label_ids.append(label[word_idx])
            previous_word_idx = word_idx
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs


def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    # 移除需要忽略的下标（之前记为-100）
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    results = metric.compute(
        predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', default='bert-base-chinese')
    parser.add_argument('--data_dir', default='./data')
    parser.add_argument('--output_dir', default='./proj_model')

    args = parser.parse_args()
    model_path = args.model_path
    data_dir = args.data_dir
    output_dir = args.output_dir

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    special_tokens_dict = {'additional_special_tokens': ['[span]', '[line]']}
    num_added_toks = tokenizer.add_special_tokens(special_tokens_dict)

    dataset = load_dataset('./ner_data.py', data_dir=data_dir)
    tokenized_datasets = dataset.map(
        tokenize_and_align_labels, batched=True,
        load_from_cache_file=False)

    # 获取标签列表
    label_list = dataset["train"].features["ner_tags"].feature.names

    # 加载预训练模型
    model = BertForTokenClassification.from_pretrained(
        model_path, num_labels=len(label_list))
    model.resize_token_embeddings(len(tokenizer))

    # 加载DataCollator
    data_collator = DataCollatorForTokenClassification(tokenizer)

    # 使用seqeval进行评价
    metric = load_metric("seqeval")

    # 定义训练参数TrainingArguments和Trainer
    args = TrainingArguments(
        output_dir="./project-checkpoint",
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=4,
        num_train_epochs=3,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )

    trainer.train()

    trainer.save_model(output_dir)
