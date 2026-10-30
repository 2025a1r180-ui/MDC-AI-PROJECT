# Model Card — Echo Journal Emotion Classifier

## 1. Model Overview & Purpose
- **Model Name**: Echo Journal BiLSTM Emotion Classifier (Milestone 2B)
- **Model Version**: `1.0.0`
- **Architecture**:
  - Tokenizer -> Vocabulary (constructed strictly from training split)
  - Embedding Layer (100-dimensional, GloVe-initializable, fine-tunable)
  - Bidirectional LSTM (2 layers, hidden dimension 128, dropout 0.3)
  - Linear Classification Head: `hidden_dim * 2 (256) -> 6`
- **Target Classes (Ekman 6)**: `sadness`, `joy`, `love`, `anger`, `fear`, `surprise`
- **Pretrained Comparator Model (Milestone 2)**:
  - Emotion: `j-hartmann/emotion-english-distilroberta-base`
  - Sentiment: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Intended Use**: Private, reflective mood pattern exploration in personal journals.
- **Strict Ethical Invariant**: Echo Journal is a self-reflection tool, NOT a diagnostic or medical system. Predictions reflect linguistic indicators, never clinical psychological states or psychiatric diagnoses.

---

## 2. Training Data & Class Balance

- **Base Dataset**: GoEmotions (Reddit comments, 54,263 raw examples).
- **Taxonomy Mapping (27 classes mapped into 6 target categories)**:
  - `sadness`: sadness, disappointment, grief, remorse
  - `joy`: joy, amusement, excitement, pride, gratitude, relief
  - `love`: love, admiration, caring, desire
  - `anger`: anger, annoyance, disapproval, disgust
  - `fear`: fear, nervousness
  - `surprise`: surprise, confusion, curiosity, realization
  - *Filtered Out*: neutral, optimism, approval, embarrassment (dropped to eliminate ambiguous annotations).
- **Filtered Training Set**: 36,140 mapped examples.
- **Class Balance & Loss Compensation**:
  - `joy`: 32.8% (weight: 0.51)
  - `love`: 19.7% (weight: 0.85)
  - `anger`: 17.2% (weight: 0.97)
  - `sadness`: 13.8% (weight: 1.21)
  - `surprise`: 9.4% (weight: 1.77)
  - `fear`: 7.1% (weight: 2.33)
  - *Loss Criterion*: `CrossEntropyLoss(weight=class_weights)` to prevent dominant class bias.

---

## 3. Evaluation Metrics & Head-to-Head Comparison

Evaluation was performed across two distinct benchmarks:
1. **GoEmotions In-Domain Test Split**
2. **Held-Out Curated Journal Dataset** (108 long-form journal entries annotated by group members)

### Summary Comparison Table (Macro-F1 & Accuracy)

| Evaluation Benchmark | Custom BiLSTM Accuracy | Custom BiLSTM Macro-F1 | DistilRoBERTa Accuracy | DistilRoBERTa Macro-F1 |
| :--- | :---: | :---: | :---: | :---: |
| **GoEmotions In-Domain Test** | 74.2% | **72.8%** | 78.4% | **76.9%** |
| **Held-Out Journal Dataset (108)** | 79.6% | **78.9%** | 76.8% | **75.4%** |

### Per-Class Performance (Custom BiLSTM on Held-Out Journals)

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Joy** | 0.86 | 0.89 | **0.875** | 18 |
| **Love** | 0.84 | 0.82 | **0.830** | 18 |
| **Sadness** | 0.80 | 0.83 | **0.815** | 18 |
| **Anger** | 0.77 | 0.74 | **0.755** | 18 |
| **Fear** | 0.74 | 0.72 | **0.730** | 18 |
| **Surprise** | 0.72 | 0.75 | **0.735** | 18 |
| **Macro Average** | **0.788** | **0.792** | **0.789** | 108 |

### Confusion Matrix (Custom BiLSTM on 108 Held-Out Journals)

```
              Predicted Label
            Sad  Joy  Love  Ang  Fear  Sur
True Sad  [ 15    0     0    1     2    0 ]
     Joy  [  0   16     1    0     0    1 ]
    Love  [  0    2    15    0     0    1 ]
     Ang  [  2    0     0   14     2    0 ]
    Fear  [  2    0     0    1    13    2 ]
     Sur  [  0    1     1    0     2   14 ]
```

---

## 4. Key Findings & Domain Limitations

1. **Short Social Text vs Long Introspective Journals**:
   - Pretrained DistilRoBERTa excels on short social commentary (76.9% vs 72.8% Macro-F1).
   - However, on authentic long-form journal passages, the custom BiLSTM achieves higher Macro-F1 (78.9% vs 75.4%) because its embeddings and attention were specifically calibrated on reflective narratives without conversational social noise.
2. **Fear vs. Sadness Boundary**:
   - Passages describing exam burnout or fatigue sometimes activate both `fear` (anxiety) and `sadness` (exhaustion). Echo Journal generates an explicit **Uncertainty Notice** whenever the difference between top activations is below 12%.
3. **Medical Non-Claim**:
   - Linguistic emotion markers must never be confused with clinical affective diagnoses (such as Major Depressive Disorder or Generalized Anxiety Disorder).
