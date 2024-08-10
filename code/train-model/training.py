# sources: 
# - https://github.com/unslothai/unsloth
# - https://colab.research.google.com/drive/1Ys44kVvmeZtnICzWz0xgpRnrIOjZAuxp?usp=sharing
# - https://huggingface.co/blog/mlabonne/sft-llama3

from unsloth import FastLanguageModel, is_bfloat16_supported
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

print("### SETUP ###")
max_seq_length = 2048
dtype = None
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Meta-Llama-3.1-8B",
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
    use_rslora=False,
    loftq_config=None,
)

alpaca_prompt = """You are given an IT Incident Problem along with additional context. Your task is to provide a detailed response that addresses the incident. Include steps for troubleshooting and resolution, and provide clear, actionable guidance to the user. Ensure your response is well-organized and addresses all aspects of the incident.


### Instruction:
{}

### Input:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token

def formatting_prompts_func(examples):
    instructions = examples["question"]
    inputs = inputs = examples.get("input", [""] * len(instructions))
    outputs = examples["answer"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
        texts.append(text)
    return { "text": texts }

print("### DATASET ###")
dataset = load_dataset('json', data_files='tickets_summary.json', split='train')
dataset = dataset.map(formatting_prompts_func, batched=True)
dataset = dataset.shuffle(seed=42)
print(dataset[0])

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=3,
        max_steps=80,
        learning_rate=1e-4,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

print("### REPORT ###")
gpu_stats = torch.cuda.get_device_properties(0)
start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
print(f"{start_gpu_memory} GB of memory reserved.")

print("### TRAIN ###")
trainer_stats = trainer.train()

print("### REPORT ###")
used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
used_percentage = round(used_memory / max_memory * 100, 3)
lora_percentage = round(used_memory_for_lora / max_memory * 100, 3)
print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
print(f"{round(trainer_stats.metrics['train_runtime']/60, 2)} minutes used for training.")
print(f"Peak reserved memory = {used_memory} GB.")
print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
print(f"Peak reserved memory % of max memory = {used_percentage} %.")
print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")

print("### DEMO ###")
FastLanguageModel.for_inference(model)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

inputs = tokenizer(
    [
        alpaca_prompt.format(
            "What steps should be taken if a user reports that their access to a shared network drive is denied?",
            "User 'john.doe' reports 'Access Denied' error when trying to access the shared network drive 'FILE-SRV-XX\\SharedDocs'.",
            "",
        )
    ], return_tensors="pt"
).to(device)

model.eval()

outputs = model.generate(**inputs, max_new_tokens=64, use_cache=True)

print("Raw output tensor:", outputs)

decoded_output = tokenizer.batch_decode(outputs, skip_special_tokens=True)

print("Decoded output:", decoded_output)

print("### SAVE ###")
model.save_pretrained("lora_model")
tokenizer.save_pretrained("lora_model")

model.save_pretrained_gguf("model", tokenizer, quantization_method="f16")
