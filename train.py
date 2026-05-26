from __future__ import annotations

import argparse
from dataclasses import dataclass

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForLanguageModeling, Trainer, TrainingArguments

SYSTEM_PROMPT = "You are 'J. AI Corporate Assistant', the definitive customer service ambassador for J. (Junaid Jamshed) Retail Pakistan."


@dataclass
class TrainConfig:
    base_model: str
    dataset_path: str
    output_dir: str
    epochs: int
    lr: float
    batch_size: int
    grad_accum: int
    max_length: int


def build_prompt(example: dict) -> dict:
    text = f"<bos><start_of_turn>system\n{SYSTEM_PROMPT}<end_of_turn>\n<start_of_turn>user\n{example['instruction']}<end_of_turn>\n<start_of_turn>model\n{example['response']}<end_of_turn>"
    return {"text": text}


def train(cfg: TrainConfig) -> None:
    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        device_map="auto",
    )

    lora = LoraConfig(r=64, lora_alpha=128, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"], lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)

    ds = load_dataset("json", data_files=cfg.dataset_path)["train"].map(build_prompt)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=cfg.max_length)

    tokenized = ds.map(tokenize, batched=True, remove_columns=ds.column_names)
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    args = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.epochs,
        learning_rate=cfg.lr,
        per_device_train_batch_size=cfg.batch_size,
        gradient_accumulation_steps=cfg.grad_accum,
        warmup_ratio=0.03,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        bf16=True,
        gradient_checkpointing=True,
        lr_scheduler_type="cosine",
        optim="adamw_torch_fused",
        weight_decay=0.01,
        report_to="none",
    )

    trainer = Trainer(model=model, args=args, train_dataset=tokenized, data_collator=collator)
    trainer.train()
    model.save_pretrained(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="High-power fine-tuning for J. support assistant")
    parser.add_argument("--base-model", default="google/gemma-2-2b-it")
    parser.add_argument("--dataset-path", default="data/j_support_train.jsonl")
    parser.add_argument("--output-dir", default="artifacts/j_support_lora")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=4096)
    a = parser.parse_args()
    train(TrainConfig(a.base_model, a.dataset_path, a.output_dir, a.epochs, a.lr, a.batch_size, a.grad_accum, a.max_length))
