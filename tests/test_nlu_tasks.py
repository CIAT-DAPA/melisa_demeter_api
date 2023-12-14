import unittest
import tempfile
import shutil
import os
from transformers import BertTokenizer
import tensorflow as tf
from your_module import NLUTasks  # replace 'your_module' with the actual name of your module

class TestNLUTasks(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()

        # Sample model and params paths
        self.model_path = "D:\\CIAT\\Code\\USAID\\melisa_demeter_api\\data\\demeter"
        self.params_path = "D:\\CIAT\\Code\\USAID\\melisa_demeter_api\\data\\vocab"
        self.model_name = "bert-base-multilingual-cased"

        # Initialize NLUTasks instance for testing
        self.nlu_tasks = NLUTasks(self.model_path, self.params_path, self.model_name)

    def tearDown(self):
        # Remove the temporary directory after testing
        shutil.rmtree(self.test_dir)

    def test_nlu(self):
        # Test the nlu method with a sample input
        text = "This is a sample text for testing."
        result = self.nlu_tasks.nlu(text)

        # Add assertions based on the expected output
        self.assertIsInstance(result, dict)
        self.assertIn("intent", result)
        self.assertIn("name", result)
        self.assertIn("slots", result)
        self.assertIsInstance(result["intent"], int)
        self.assertIsInstance(result["name"], str)
        self.assertIsInstance(result["slots"], dict)

    def test_decode_predictions(self):
        # Test the _decode_predictions method with a sample input
        text = "This is a sample text for testing."
        intent_id = 0
        slot_ids = [1, 2, 3, 0, 0, 4, 0]  # Example slot_ids, adjust based on your model output

        result = self.nlu_tasks._decode_predictions(text, intent_id, slot_ids)

        # Add assertions based on the expected output
        self.assertIsInstance(result, dict)
        self.assertIn("intent", result)
        self.assertIn("name", result)
        self.assertIn("slots", result)
        self.assertEqual(result["intent"], intent_id)
        self.assertIsInstance(result["name"], str)
        self.assertIsInstance(result["slots"], dict)

    def test_model_loading(self):
        # Test that the model and tokenizer are loaded successfully
        self.assertIsInstance(self.nlu_tasks.model, tf.saved_model.SaveableObject)
        self.assertIsInstance(self.nlu_tasks.tokenizer, BertTokenizer)

    def test_params_loading(self):
        # Test that intent and slot names are loaded successfully
        self.assertIsInstance(self.nlu_tasks.intent_names, list)
        self.assertIsInstance(self.nlu_tasks.slot_names, list)
        self.assertIsInstance(self.nlu_tasks.intent_map, dict)
        self.assertIsInstance(self.nlu_tasks.slot_map, dict)

if __name__ == '__main__':
    unittest.main()