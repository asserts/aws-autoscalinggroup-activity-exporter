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
