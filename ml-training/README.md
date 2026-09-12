# KrushiRakshak AI — ML Training

This directory contains standalone training scripts and notebooks.
It is **not** mounted into the Docker deployment.

## Structure

```
ml-training/
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_model_training.ipynb
│   └── 03_evaluation.ipynb
├── scripts/
│   ├── train.py          # CLI training script
│   ├── evaluate.py       # Evaluation against test set
│   └── export_weights.py # Export model to backend/app/ml/weights/
├── data/
│   └── README.md         # Instructions for PlantVillage dataset download
└── requirements-train.txt
```

## Dataset

Download the [PlantVillage dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
and place it in `data/raw/`.

## Training

```bash
pip install -r requirements-train.txt
python scripts/train.py --epochs 50 --batch-size 32
```

After training, copy the best checkpoint to `../backend/app/ml/weights/disease_classifier.pth`.
