import hashlib
import json
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


def read_json_file(filepath):
    """Read a json file

    Args:
        filepath (str): path or absolute path to json file

    Returns:
        dict: json represented as a dictionary
    """

    logger.debug(f'Reading json file at {filepath}')

    try:
        with open(filepath, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        logger.error(f'File {filepath} does not exist!')
        raise


def remove_by_val(data, value):
    """Remove value or key/value pairs from data structure by
       value.

    Args:
        data (dict/list): the data to act on
        value (multiple int/str/list/dict etc..): the value to remove

    Returns:
        dict/list: data stripped of values equal to `value`
    """

    if isinstance(data, list):
        return [remove_by_val(x, value) for x in data if x != value]
    elif isinstance(data, dict):
        return {
            key: remove_by_val(val, value)
            for key, val in data.items()
            if val != value
        }
    else:
        return data


def merge(dict1, dict2):
    """Merge 2 python dictionaries
    Args:
        dict1 (dict): first dictionary
        dict2 (dict): second dictionary

    Returns:
        dict: dict1 and dict2 merged
    """

    dict2.update(dict1)

    return dict2


def merge_dict_list(dicts):
    """Merge list of python dictionaries
    Args:
        dicts (list): list of python dictionaries

    Returns:
        OrderedDict: list of dicts merged by list order
    """

    merged_dict = OrderedDict()

    for dict in dicts:
        merged_dict.update(dict)

    return merged_dict


def dict_hash(_dict):
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(_dict, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()
