import json, os, uuid

DEFAULT_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".my_python_dueros.json")

def load(client_id=None, client_secret=None):
	if os.path.isfile(DEFAULT_CONFIG_FILE):
		configfile = DEFAULT_CONFIG_FILE
	else:
		product_id = "xhl-" + uuid.uuid4().hex
		return {
			"dueros-device-id": product_id,
			"client_id": client_id,
			"client_secret": client_secret
		}
	with open(configfile, 'r') as f:
		config = json.load(f)
		require_keys = ['dueros-device-id', 'client_id', 'client_secret']
		for key in require_keys:
			if not ((key in config) and config[key]):
				raise KeyError("{} should include {}".format(configfile, key))

	return config

def save(config, configfile=None):
	if configfile is None:
		configfile = DEFAULT_CONFIG_FILE
	with open(configfile, "w") as f:
		json.dump(config, f, indent=4)
		
	