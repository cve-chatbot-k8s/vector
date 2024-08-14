from transformers import AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling
import torch
from torch.utils.data import Dataset

class EmbeddingDataset(Dataset):
    def __init__(self, embeddings):
        self.embeddings = list(embeddings.values())

    def __len__(self):
        return len(self.embeddings)

    def __getitem__(self, idx):
        return torch.tensor(self.embeddings[idx], dtype=torch.float)

def train_llm(embeddings):
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    dataset = EmbeddingDataset(embeddings)
    data_collator = DataCollatorForLanguageModeling(tokenizer=None, mlm=False)

    training_args = TrainingArguments(
        output_dir="./results",
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        save_steps=10_000,
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=dataset,
    )

    trainer.train()
    return model