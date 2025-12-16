"""
Email dataset loader for email categorization benchmarks.
"""

import json
from typing import Dict, Any, List
from .question import Question
from .dataset import Dataset


class EmailDatasetLoader:
    """Loader for email categorization datasets."""
    
    @staticmethod
    def from_json_file(filepath: str) -> Dataset:
        """
        Load email dataset from JSON file.
        
        Expected format:
        {
            "metadata": {
                "version": "2.0",
                "created": "2025-12-07",
                "description": "...",
                "total_emails": 100,
                "categories": {...}
            },
            "emails": [
                {
                    "id": "email_001",
                    "subject": "...",
                    "body": "...",
                    "sender": "...",
                    "has_attachment": true,
                    "expected_category": "contract_submission",
                    "metadata": {...}
                }
            ]
        }
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Dataset instance with email questions
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return EmailDatasetLoader.from_dict(data)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Dataset:
        """
        Create dataset from dictionary with email data.
        
        Args:
            data: Dictionary containing metadata and emails
            
        Returns:
            Dataset instance
        """
        metadata = data.get("metadata", {})
        emails = data.get("emails", [])
        
        questions = []
        for email_data in emails:
            # Build the email text from subject and body
            email_text = f"Subject: {email_data.get('subject', '')}\n\n"
            email_text += f"From: {email_data.get('sender', '')}\n"
            if email_data.get('has_attachment', False):
                email_text += "Has attachment: Yes\n"
            email_text += f"\nBody:\n{email_data.get('body', '')}"
            
            # Create question with email data
            expected_category = email_data.get("expected_category")
            question = Question(
                id=email_data.get("id", f"email_{len(questions):03d}"),
                text=email_text,
                expected_answer=expected_category,  # Set expected_answer to the category
                metadata={
                    "email_subject": email_data.get("subject", ""),
                    "email_body": email_data.get("body", ""),
                    "email_sender": email_data.get("sender", ""),
                    "has_attachment": email_data.get("has_attachment", False),
                    "expected_category": expected_category,  # Also store in metadata for easy access
                    **email_data.get("metadata", {})
                }
            )
            questions.append(question)
        
        # Create dataset
        dataset = Dataset(
            questions=questions,
            name=metadata.get("description", "Email Categorization Dataset"),
            description=metadata.get("description", "Email categorization dataset")
        )
        dataset.metadata = metadata
        
        return dataset
    
    @staticmethod
    def from_json_string(json_str: str) -> Dataset:
        """
        Create dataset from JSON string.
        
        Args:
            json_str: JSON string containing email data
            
        Returns:
            Dataset instance
        """
        data = json.loads(json_str)
        return EmailDatasetLoader.from_dict(data)

