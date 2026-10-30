"""
Vocabulary Builder for Custom BiLSTM Emotion Classifier (Milestone 2B).
Constructed strictly from the training split to eliminate data leakage.
"""

import json
from collections import Counter
from typing import List, Dict, Iterable, Optional


class Vocabulary:
    def __init__(self, min_freq: int = 2, max_size: int = 20000):
        self.min_freq = min_freq
        self.max_size = max_size
        self.pad_token = "<PAD>"
        self.unk_token = "<UNK>"
        self.pad_idx = 0
        self.unk_idx = 1
        
        self.token_to_idx: Dict[str, int] = {self.pad_token: self.pad_idx, self.unk_token: self.unk_idx}
        self.idx_to_token: Dict[int, str] = {self.pad_idx: self.pad_token, self.unk_idx: self.unk_token}

    def build_from_texts(self, texts: Iterable[str]):
        """Construct vocabulary strictly from training split."""
        counter = Counter()
        for text in texts:
            tokens = text.lower().split()
            counter.update(tokens)

        # Retain tokens meeting minimum frequency
        sorted_tokens = [tok for tok, count in counter.most_common() if count >= self.min_freq]
        for tok in sorted_tokens[:self.max_size - 2]:
            idx = len(self.token_to_idx)
            self.token_to_idx[tok] = idx
            self.idx_to_token[idx] = tok

    def encode(self, text: str, max_length: int = 128) -> List[int]:
        """Convert string to token index array with truncation and padding."""
        tokens = text.lower().split()[:max_length]
        indices = [self.token_to_idx.get(t, self.unk_idx) for t in tokens]
        if len(indices) < max_length:
            indices += [self.pad_idx] * (max_length - len(indices))
        return indices

    def decode(self, indices: List[int]) -> List[str]:
        """Decode token index array back to tokens."""
        return [self.idx_to_token.get(idx, self.unk_token) for idx in indices if idx != self.pad_idx]

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"token_to_idx": self.token_to_idx, "min_freq": self.min_freq, "max_size": self.max_size}, f)

    @classmethod
    def load(cls, filepath: str) -> "Vocabulary":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        vocab = cls(min_freq=data["min_freq"], max_size=data["max_size"])
        vocab.token_to_idx = data["token_to_idx"]
        vocab.idx_to_token = {int(idx): tok for tok, idx in vocab.token_to_idx.items()}
        return vocab

    def __len__(self) -> int:
        return len(self.token_to_idx)
