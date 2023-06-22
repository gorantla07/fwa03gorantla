import yaml, json, re, os
from openapi_spec_validator.validation import openapi_v30_spec_validator, openapi_v2_spec_validator
from sys import platform

S = ' -> '

spl_char = [',', '$', '#', '@', '!', '^', '*', ';', '(', ')', '+', '=', '?', '>', '<', '[', ']', '{',
            '}', '|', '`', '~']


def extract_text_between_quotes(text):
    # Extracts text between single quotes
    if isinstance(text, str):
        matches = re.findall(r"'(.*?)'", text)
        return ('%s' % S).join([str(v) for v in matches])
        # if len(matches) >= 1:
        # return matches[0]
    return None


def check_for_spl_char(field_name, spec_dict, spl_char):
    field_value = ''
    field_list = []
    try:
        for index, name in enumerate(field_name):
            if index != 0:
                spec_dict = field_value
            if type(spec_dict) == dict:
                field_value = spec_dict[name]
            else:
                for v in spec_dict:
                    field_list.append(v[name])

    except KeyError:
        msg = '%s' % S.join([str(v) for v in field_name])
        return f'{msg} must is missing.'

    if field_list:
        error_list = []
        for f in field_list:
            if len(f) == 0:
                msg = '%s' % S.join([str(v) for v in field_name])
                error_list.append(f'{msg} must not be empty.')

            if f:
                for char in spl_char:
                    if char in f:
                        msg = '%s' % S.join([str(v) for v in field_name])
                        error_list.append(f'{msg} contains special characters.')
        return error_list

    if len(field_value) == 0:
        msg = '%s' % S.join([str(v) for v in field_name])
        return f'{msg} must not be empty.'

    if field_value:
        for char in spl_char:
            if char in field_value:
                msg = '%s' % S.join([str(v) for v in field_name])
                return f'{msg} contains special characters.'


def validate_local_spec(spec_file_path, validation_errors, show_detailed_messages):
    # Validate the local OpenAPI specification file
    file_extension = os.path.splitext(spec_file_path)[1]
    if file_extension not in ['.yaml', '.yml', '.json']:
        print(f"Invalid file extension: {file_extension}. Skipping file: {spec_file_path}")
        return True


    if file_extension == '.json':
        with open(spec_file_path, 'r', encoding='utf-8') as f:
            spec_dict = json.load(f)
            try:
                _spec_version = spec_dict['openapi']
            except KeyError:
                try:
                    _spec_version = spec_dict['swagger']
                except KeyError:
                    print(f"Invalid OpenAPI specification: {spec_file_path}. Skipping file.")
                    return False
    else:
        with open(spec_file_path, 'r', encoding='utf-8') as f:
            spec_dict = yaml.safe_load(f)
            try:
                _spec_version = spec_dict['openapi']
            except KeyError:
                try:
                    _spec_version = spec_dict['swagger']
                except KeyError:
                    print(f"Invalid OpenAPI specification: {spec_file_path}. Skipping file.")
                    return False

    print(f"Validating open API Specification: {spec_file_path} with version {_spec_version}")

    version_pattern = r"^(3\.0\.[0-3]|2\.0)$"
    _v3_version_pattern = r"^(3\.0\.[0-3])$"
    _v2_version_pattern = r"^(2\.0)$"
    errors = None

    if not re.match(version_pattern, _spec_version):
        print(f"{_spec_version} is not a valid version. Skipping file.")
        return False
    if re.match(_v3_version_pattern, _spec_version):
        errors = openapi_v30_spec_validator.iter_errors(spec_dict)
    elif re.match(_v2_version_pattern, _spec_version):
        errors = openapi_v2_spec_validator.iter_errors(spec_dict)

    errors_list = []
    try:
        errors_list = list(errors)
    except Exception as e1:
        validation_errors.append(f'Error at keyword {e1}, please rerun the validation after fixing this error')

    print(f'Number of errors found in spec: {len(errors_list)}')
    for x, error in enumerate(errors_list, start=1):
        issue_with = extract_text_between_quotes(str(error.path))
        message = f'Error found in {issue_with} object.\n' if issue_with else ''
        if show_detailed_messages:
            validation_errors.append(f'{message}{str(error)}')
        else:
            validation_errors.append(f'{message}{error.message}')

    custom_check_attr = [['info', 'title'], ['servers', 'description'], ['servers', 'url']]
    for attr in custom_check_attr:
        spl_char_errors_list = check_for_spl_char(attr, spec_dict, spl_char)
        if spl_char_errors_list:
            validation_errors.append(spl_char_errors_list)

    if validation_errors:
        print('OAS validation failed due to the following reasons - ')
        for count, error in enumerate(validation_errors, start=1):
            print(f"{count}: {error}")
        return False
    return True


def print_usage():
    # Print usage information
    print("OpenAPI Specification Validator")
    print("Supported versions: 3.0.0 - 3.0.3, 2.0")
    print("Usage: python script_name.py <spec_file_or_directory>")
    print("Description: This program validates OpenAPI specification files.")
    print("             It supports OpenAPI versions 3.0.0 - 3.0.3 and 2.0.")
    print("             You can provide a single file or a directory containing multiple files.")
    print("             The program will validate each file and display any validation errors.")


def main(local_spec_file, show_detailed_messages=False):
    _separator = '/'
    if platform == "win32":
        _separator = '\\'
    mypath = local_spec_file
    if os.path.isdir(mypath):
        print("Validating open API Specifications in the directory:")
        print(mypath)
        print("------------------------------")

        for entry in os.scandir(mypath):
            if entry.is_file():
                validate_local_spec(entry.path, [], show_detailed_messages)
    else:
        validate_local_spec(mypath, [], show_detailed_messages)


if __name__ == "__main__":
    print_usage()
    main('resources/oas_/spec_testerror.yaml')
