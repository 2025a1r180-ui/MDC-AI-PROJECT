"""
PyTorch BiLSTM Architecture for 6-Class Emotion Classification (Milestone 2B).
Target classes: sadness, joy, love, anger, fear, surprise.
Supports:
- Pre-trained GloVe embedding initialization (fine-tunable)
- Random-init ablation
- Class weighting for imbalanced loss handling
- Hardware detection: NVIDIA CUDA GPU with CPU fallback
"""

import os
from typing import Optional, Dict

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    nn = object


if HAS_TORCH:
    class BiLSTMEmotionClassifier(nn.Module):
        def __init__(
            self,
            vocab_size: int,
            embedding_dim: int = 100,
            hidden_dim: int = 128,
            num_layers: int = 2,
            output_dim: int = 6,
            dropout: float = 0.3,
            pad_idx: int = 0,
            pretrained_embeddings: Optional[torch.Tensor] = None
        ):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_idx)
            
            # GloVe initialization vs random-init ablation
            if pretrained_embeddings is not None:
                self.embedding.weight.data.copy_(pretrained_embeddings)
                self.embedding.weight.requires_grad = True  # Fine-tunable
            else:
                nn.init.uniform_(self.embedding.weight, -0.05, 0.05)
                self.embedding.weight.data[pad_idx].fill_(0)

            self.lstm = nn.LSTM(
                embedding_dim,
                hidden_dim,
                num_layers=num_layers,
                bidirectional=True,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0
            )
            self.dropout = nn.Dropout(dropout)
            self.fc = nn.Linear(hidden_dim * 2, output_dim)

        def forward(self, text_indices: torch.Tensor) -> torch.Tensor:
            # text_indices shape: [batch_size, seq_len]
            embedded = self.dropout(self.embedding(text_indices))
            # embedded shape: [batch_size, seq_len, emb_dim]
            lstm_out, (hidden, cell) = self.lstm(embedded)
            # Concatenate the final forward and backward hidden representations
            hidden_forward = hidden[-2, :, :]
            hidden_backward = hidden[-1, :, :]
            combined = torch.cat((hidden_forward, hidden_backward), dim=1)
            dropped = self.dropout(combined)
            logits = self.fc(dropped)
            return logits

    def get_weighted_loss_criterion(class_weights: Dict[str, float], device: torch.device):
        """Builds CrossEntropyLoss with class weights to compensate for imbalance."""
        from .data_prep import SIX_LABELS
        weights_tensor = torch.tensor([class_weights.get(lbl, 1.0) for lbl in SIX_LABELS], dtype=torch.float32).to(device)
        return nn.CrossEntropyLoss(weight=weights_tensor)
else:
    class BiLSTMEmotionClassifier:
        def __init__(self, *args, **kwargs):
            pass
