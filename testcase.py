import unittest
from unittest.mock import patch, MagicMock
from your_module import validate_spec, main

class TestSpecValidator(unittest.TestCase):

    @patch('spec_validator.SpecValidator')  # Mocking SpecValidator class
    def test_validate_spec(self, mock_spec_validator):
        mock_instance = mock_spec_validator.return_value
        mock_instance.validate.return_value = True

        result = validate_spec(file='example.yaml')

        self.assertTrue(result)  # Assuming True indicates successful validation
        mock_spec_validator.assert_called_once()  # Check if SpecValidator was instantiated
        mock_instance.validate.assert_called_once_with('example.yaml', [])  # Check validate() call

    @patch('argparse.ArgumentParser')
    def test_main(self, mock_arg_parser):
        mock_parser = MagicMock()
        mock_arg_parser.return_value = mock_parser
        mock_parser.parse_args.return_value = MagicMock(file='example.yaml', command='validate-spec')

        mock_commands = {'validate-spec': MagicMock()}
        with patch('your_module.commands', mock_commands):
            main()

        mock_arg_parser.assert_called_once()  # Check if ArgumentParser was instantiated
        mock_parser.parse_args.assert_called_once_with(sys.argv[1:])  # Check parse_args() call
        mock_commands['validate-spec'].assert_called_once()  # Check if validate_spec function was called

if __name__ == '__main__':
    unittest.main()
