import yaml
import logging
from yaml.resolver import Resolver


logger = logging.getLogger(__name__)

# avoid object references in pyaml
# https://stackoverflow.com/questions/13518819/avoid-references-in-pyyaml
yaml.Dumper.ignore_aliases = lambda *args : True

# override pyyaml auto conversion of key words to booleans
for ch in "OoYyNn":
    if len(Resolver.yaml_implicit_resolvers[ch]) == 1:
        del Resolver.yaml_implicit_resolvers[ch]
    else:
        Resolver.yaml_implicit_resolvers[ch] = [x for x in
                                                Resolver.yaml_implicit_resolvers[ch] if
                                                x[0] != 'tag:serialize.org,2002:bool']


def read_yaml_file(filepath):
    """Read a yaml file

    Args:
        filepath (str): path or absolute path to yaml file

    Returns:
        dict: yaml represented as a dictionary
    """

    logger.debug(f'Reading yaml file at {filepath}')

    try:
        with open(filepath, 'r') as f:
            return yaml.load(f, Loader=yaml.loader.BaseLoader)
    except FileNotFoundError:
        logger.error(f'File {filepath} does not exist!')
        raise


def read_yaml_string(yaml_str):
    """Read yaml represented as a string

    Args:
        yaml_str (str): the yaml represented as a string

    Returns:
        dict: yaml string converted to a dictionary
    """

    result = yaml.safe_load(yaml_str)

    return result


def dict_to_yaml_string(dict_):
    """Convert a dictionary to a yaml string

    Args:
        dict_ (dict): the yaml dictionary

    Returns:
        string: yaml string
    """

    return _convert_quoted_booleans(yaml.dump(dict_))


def _convert_quoted_booleans(yaml_str):
    """Convert quoted booleans to a real boolean if in a
       yaml string.

    Args:
        yaml_str (str): the yaml string

    Returns:
        string: yaml string with proper yaml booleans
    """

    new_yaml = yaml_str.replace("'true'", "true")
    new_yaml = new_yaml.replace("'false'", "false")

    return new_yaml
