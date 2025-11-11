"""
Train the intent classification model using SetFit
"""
import argparse
import logging
from pathlib import Path
from typing import List, Tuple
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from setfit import SetFitModel, SetFitTrainer
    from datasets import Dataset
    import torch
    from sklearn.metrics import classification_report, confusion_matrix
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    logger.error(f"Required dependencies not available: {e}")
    logger.error("Install with: pip install setfit datasets scikit-learn torch")

from training_data import (
    get_training_data,
    get_balanced_dataset,
    print_training_data_stats,
    TRAINING_EXAMPLES
)


def prepare_dataset(training_data: List[Tuple[str, str]], test_split: float = 0.2):
    """
    Prepare train and test datasets

    Args:
        training_data: List of (text, label) tuples
        test_split: Fraction of data to use for testing

    Returns:
        (train_dataset, test_dataset)
    """
    # Shuffle data
    import random
    random.seed(42)
    shuffled_data = training_data.copy()
    random.shuffle(shuffled_data)

    # Split into train/test
    split_idx = int(len(shuffled_data) * (1 - test_split))
    train_data = shuffled_data[:split_idx]
    test_data = shuffled_data[split_idx:]

    # Convert to datasets
    train_dict = {
        "text": [item[0] for item in train_data],
        "label": [item[1] for item in train_data]
    }
    test_dict = {
        "text": [item[0] for item in test_data],
        "label": [item[1] for item in test_data]
    }

    train_dataset = Dataset.from_dict(train_dict)
    test_dataset = Dataset.from_dict(test_dict)

    logger.info(f"Train set: {len(train_dataset)} examples")
    logger.info(f"Test set: {len(test_dataset)} examples")

    return train_dataset, test_dataset


def train_model(
    train_dataset,
    test_dataset,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    num_epochs: int = 1,
    batch_size: int = 16,
    output_path: str = "./data/models/intent_classifier"
):
    """
    Train the SetFit model

    Args:
        train_dataset: Training dataset
        test_dataset: Test dataset
        model_name: Base model to use
        num_epochs: Number of training epochs
        batch_size: Training batch size
        output_path: Where to save the trained model

    Returns:
        Trained model
    """
    logger.info(f"Initializing SetFit model from {model_name}")

    # Initialize model
    model = SetFitModel.from_pretrained(
        model_name,
        multi_target_strategy="one-vs-rest"  # Good for multi-class classification
    )

    # Create trainer
    trainer = SetFitTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        metric="accuracy",
        batch_size=batch_size,
        num_epochs=num_epochs,
        num_iterations=20,  # Number of text pairs to generate
    )

    # Train the model
    logger.info("Starting training...")
    trainer.train()

    # Evaluate
    logger.info("Evaluating model...")
    metrics = trainer.evaluate()
    logger.info(f"Evaluation metrics: {metrics}")

    # Save the model
    Path(output_path).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path)
    logger.info(f"✅ Model saved to {output_path}")

    return model


def evaluate_model(model, test_dataset):
    """
    Detailed evaluation of the trained model

    Args:
        model: Trained SetFit model
        test_dataset: Test dataset

    Returns:
        Evaluation metrics
    """
    logger.info("Running detailed evaluation...")

    # Get predictions
    test_texts = test_dataset["text"]
    true_labels = test_dataset["label"]

    predictions = model.predict(test_texts)

    # Convert to numpy arrays
    predictions = np.array(predictions)
    true_labels = np.array(true_labels)

    # Print classification report
    print("\n" + "="*80)
    print("CLASSIFICATION REPORT")
    print("="*80)
    print(classification_report(true_labels, predictions, zero_division=0))

    # Print confusion matrix
    print("\n" + "="*80)
    print("CONFUSION MATRIX")
    print("="*80)
    cm = confusion_matrix(true_labels, predictions)

    # Get unique labels
    unique_labels = sorted(set(list(true_labels) + list(predictions)))

    # Print header
    print(f"{'':15s} | " + " | ".join([f"{label:12s}" for label in unique_labels]))
    print("-" * (15 + (15 * len(unique_labels))))

    # Print rows
    for i, label in enumerate(unique_labels):
        row_values = " | ".join([f"{cm[i][j]:12d}" for j in range(len(unique_labels))])
        print(f"{label:15s} | {row_values}")

    print("="*80 + "\n")

    # Calculate accuracy
    accuracy = (predictions == true_labels).mean()
    logger.info(f"Overall Accuracy: {accuracy:.2%}")

    return {
        "accuracy": accuracy,
        "classification_report": classification_report(true_labels, predictions, output_dict=True, zero_division=0),
        "confusion_matrix": cm.tolist()
    }


def test_predictions(model):
    """
    Test the model with some example queries

    Args:
        model: Trained model
    """
    test_queries = [
        "which files have msisdn 123456",
        "find duplicate customer_ids",
        "list unique segments",
        "average revenue by region",
        "how many files do we have",
        "which column has most duplicates",
        "what trends do you see in the data",
        "show me errors for msisdn 99999",
        "count orders by status",
        "what files are uploaded"
    ]

    print("\n" + "="*80)
    print("SAMPLE PREDICTIONS")
    print("="*80 + "\n")

    for query in test_queries:
        prediction = model.predict([query])[0]
        try:
            probs = model.predict_proba([query])[0]
            confidence = max(probs)
            print(f"Query: {query}")
            print(f"  → Intent: {prediction} (confidence: {confidence:.2%})")
            print()
        except:
            print(f"Query: {query}")
            print(f"  → Intent: {prediction}")
            print()


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Train intent classification model")
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Base model to use (default: all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Number of training epochs (default: 1)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Training batch size (default: 16)"
    )
    parser.add_argument(
        "--output",
        default="./data/models/intent_classifier",
        help="Output path for trained model"
    )
    parser.add_argument(
        "--balanced",
        action="store_true",
        help="Use balanced dataset (equal examples per intent)"
    )
    parser.add_argument(
        "--examples-per-intent",
        type=int,
        default=25,
        help="Examples per intent for balanced dataset (default: 25)"
    )

    args = parser.parse_args()

    # Check dependencies
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing required dependencies. Install with:")
        logger.error("pip install setfit datasets scikit-learn torch")
        sys.exit(1)

    print("\n" + "="*80)
    print("VOYAGER INTENT CLASSIFIER TRAINING")
    print("="*80 + "\n")

    # Print training data stats
    print_training_data_stats()

    # Get training data
    if args.balanced:
        logger.info(f"Using balanced dataset with {args.examples_per_intent} examples per intent")
        training_data = get_balanced_dataset(args.examples_per_intent)
    else:
        logger.info("Using full dataset (unbalanced)")
        training_data = get_training_data()

    # Prepare datasets
    train_dataset, test_dataset = prepare_dataset(training_data)

    # Train model
    model = train_model(
        train_dataset,
        test_dataset,
        model_name=args.model,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        output_path=args.output
    )

    # Evaluate
    evaluate_model(model, test_dataset)

    # Test with examples
    test_predictions(model)

    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    print(f"\nModel saved to: {args.output}")
    print("\nYou can now use the trained model in the QueryRouter!")
    print("The system will automatically load it on startup.\n")


if __name__ == "__main__":
    main()
