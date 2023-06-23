import yaml, json, re, os
from openapi_spec_validator.validation import openapi_v30_spec_validator, openapi_v2_spec_validator
from sys import platform


S = ' -> '
url_pattern = "^http(s)?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9(" \
              ")@:%_\\+.~#?&\\/=]*)$"


def extract_text_between_quotes(text):
    # Extracts text between single quotes
    if isinstance(text, str):
        matches = re.findall(r"'(.*?)'", text)
        return ('%s' % S).join([str(v) for v in matches])
        # if len(matches) >= 1:
        # return matches[0]
    return None


# This method will take OAS element as input and check if the all element are present and
# for the leaf element (if list then for all the leaf elements of the list) it will check
# the following
# 1. Presence of a value and not empty or None/null
# 2. Presence of special characters as per spl_char
# 3. Url format is correct or not
def check_for_spl_char(field_name, spec_dict, spl_char):
    field_value = ''  # This will take care of dict type in OAS
    field_list = []   # This will take care of list type in OAS
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

    # Find issues in the list
    if field_list:
        error_list = []
        for value in field_list:
            if None == value or len(value) == 0:
                msg = '%s' % S.join([str(v) for v in field_name])
                error_list.append(f'{msg} : {value} : must not be empty.')

            elif value:
                # Check for valid URL format for fields with 'URL' in name
                if 'url' in field_name:

                    if None == re.match(url_pattern, value):
                        msg = '%s' % S.join([str(v) for v in field_name])
                        error_list.append(f'{msg} : {value} : is not in URL format.')
                # Check for special characters in any non url field
                else:
                    for char in spl_char:
                        if char in value:
                            msg = '%s' % S.join([str(v) for v in field_name])
                            error_list.append(f'{msg} : {value} : contains special characters.')
        return error_list

    # Find issues in the dict
    else:
        if None == field_value or len(field_value) == 0:
            msg = '%s' % S.join([str(v) for v in field_name])
            return f'{msg} : {field_value} : must not be empty.'

        if field_value:
            # Check for valid URL format for fields with 'URL' in name
            if 'url' in field_name:
                if None == re.match(url_pattern, field_value):
                    msg = '%s' % S.join([str(v) for v in field_name])
                    return f'{msg} : {field_value} : is not in URL format.'
            # Check for special characters in any non url field
            else:
                for char in spl_char:
                    if char in field_value:
                        msg = '%s' % S.join([str(v) for v in field_name])
                        return f'{msg} : {field_value} : contains special characters.'


def validate_path(spec_dict, param, spl_char):
    err_path = []
    keys = spec_dict[param].keys()
    for key in keys:
        for char in spl_char:
            if char in key:
                err_path.append(key)
                break
    msg = ','.join([str(v) for v in err_path])
    return f'Paths : {msg} : contains spl characters'


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

    # Custom validation starts here -
    custom_check_attr = [['info', 'title'], ['servers', 'description'], ['servers', 'url']]
    spl_char = [',', '$', '#', '@', '!', '^', '*', ';', '(', ')', '+', '=', '?', '>', '<', '[', ']', '|', '`', '~']
    for attr in custom_check_attr:
        spl_char_errors_list = check_for_spl_char(attr, spec_dict, spl_char)
        if spl_char_errors_list:
            validation_errors.append(spl_char_errors_list)

    path_err_msg = validate_path(spec_dict, 'paths', spl_char)
    if path_err_msg:
        validation_errors.append(path_err_msg)

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
    main('resources/oas_/spec.json')
