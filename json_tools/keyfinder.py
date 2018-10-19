from datetime import datetime
import hashlib
import json


def minion_generator(data, tier=0):
        if isinstance(data, dict):
            return DictMinion(data, tier=tier)
        if isinstance(data, list):
            return ListMinion(data, tier=tier)
        return EdgeMinion(data, tier=tier)


def build_model(data, tier=0):
    if isinstance(data, dict):
        return {
            k: minion_generator(v, tier=tier) for k, v in data.items()
        }
    if isinstance(data, list):
        return [minion_generator(item, tier=tier) for item in data]
    return minion_generator(data, tier=tier)


class Minion:

    def __init__(self, data=None, label=None, tier=0):
        # Holds base value if a Edge minion
        if label == 'edge':
            self._data = data
            self.edge = True
        else:
            self._data = None
            self.edge = False
        self.tier = tier
        self.label = label
        # List or Dict holding child minions unless data will generate
        # an EdgeMinion
        if not self.edge:
            next_tier = self.tier + 1
            self._model = build_model(data, tier=next_tier)
        self._keys = self._recursive_keys()
    
    @property
    def data(self):
        pass

    @property
    def keys(self):
        pass

    def model(self, depth=0):
        return self._recursive_model(depth=depth)

    @data.getter
    def data(self):
        if self.edge:
            return self._data
        return self._recursive_data()

    def hash(self, depth=0):
        model = self.model(depth=depth)
        model_bytes = json.dumps(model).encode('utf-8')
        return hashlib.md5(model_bytes).hexdigest()

    @keys.getter
    def keys(self):
        return self._recursive_keys()

    def _recursive_data(self):
        return self._data

    def _recursive_model(self, depth=None):
        return self.label

    def _recursive_keys(self):
        pass

    def data_string(self):
        return str(self.data)

    def __str__(self):
        raw = self.model
        return json.dumps(raw)


class DictMinion(Minion):

    def __init__(self, dictionary, tier=0):
        super().__init__(data=dictionary, label='DICT', tier=tier)

    def _recursive_model(self, depth=0, data=False):
        return_dict = {}
        for k, v in self._model.items():
            if not depth:
                return_dict[k] = v.label
                continue
            next_depth = depth - 1
            return_dict[k] = v.model(depth=next_depth)
        return return_dict

    def _recursive_data(self):
        return_dict = {}
        for k, v in self._model.items():
            return_dict[k] = v.data
        return {k: v.data for k, v in self._model.items()}

    def _recursive_keys(self):
        temp_keys = {k for k in self._model.keys()}
        for value in self._model.values():
            if not value.edge:
                temp_keys |= value.keys
        return temp_keys


class ListMinion(Minion):

    def __init__(self, new_list, tier=0):
        super().__init__(data=new_list, label='LIST', tier=tier)

    def _recursive_model(self, depth):
        return_list = []
        for item in self._model:
            if not depth:
                return_list.append(item.label)
                continue
            next_depth = depth - 1
            return_list.append(item.model(depth=next_depth))
        return return_list

    def _recursive_data(self):
        return [item.data for item in self._model]

    def _recursive_keys(self):
        temp_keys = set()
        for list_item in self._model:
            if not list_item.edge:
                temp_keys |= list_item.keys
        return temp_keys


class EdgeMinion(Minion):

    def __init__(self, edge_item, tier=0):
        super().__init__(data=edge_item, label='edge', tier=tier)
        self.edge = True

    @property
    def data_type(self):
        pass

    @data_type.getter
    def data_type(self):
        if isinstance(self._data, int):
            return 'int'
        if isinstance(self._data, str):
            return 'str'
        if isinstance(self._data, float):
            return 'float'
        if not self._data:
            return 'none'
        return 'unsupported'


class Master:

    def __init__(self, data):
        self.minions = [minion_generator(json_dict) for json_dict in data]
        self.key_ring = self._get_unique_keys()

    def _get_unique_keys(self):
        temp_set = set()
        for minion in self.minions:
            temp_set |= minion.keys
        return temp_set


class KeyMinion(object):

    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.model = {}
        self.key_ring = set()
        self.duplicates = set()
        self.models_written = {}
        self.dup_and_heirarchy = False
        self.tiered = False
        self.hash = None

    def check_keys(self):
        self.model = self._check_keys(dictionary=self.dictionary)
        self.hash = self._get_md5()

    def _check_keys(self, dictionary=None):
        temp_dict = {}
        for k, v in dictionary.items():
            # Note duplicates
            if k in self.key_ring:
                self.duplicates.add(k)

            # Since we're using a set, the key will only appear once
            # so it's fine to add to the set regardless of it already
            # existing or not.
            self.key_ring.add(k)

            if isinstance(v, dict):
                # Recursion if value is another dictionary
                temp_dict[k] = self._check_keys(dictionary=v)
                self.tiered = True
            elif isinstance(v, list):
                temp_dict[k] = 'LIST'
                self.tiered = True
            elif isinstance(v, set):
                temp_dict[k] = 'SET'
                self.tiered = True

            else:
                # Base case
                temp_dict[k] = 'edge'

        return temp_dict

    def __eq__(self, other):
        """  Compare KeyMinion objects by comparing self.model

            We really only want to compare the format/heirarchy of the
            key/values, self.model is great to use because it is
            already standard format across each KeyMinion. Each key
            can only have one of two values: 'Edge' or another dict.
        """

        if not (self.model == other.model):
            return False
        return True

    def _get_md5(self):
        model_bytes = json.dumps(self.model).encode('utf-8')
        return hashlib.md5(model_bytes).hexdigest()


class KeyMaster(object):

    def __init__(self, dict_list):
        self.dict_list = dict_list
        self.all_keys = set()
        self.minions = []
        self.minions_w_duplicates = []
        self.minions_format_logged = []
        self.duplicate_sets = []
        self.dup_and_heirarchy_sets = []
        self.duplicate_keys = set()

    def analyze(self):
        with open('duplicate_keys.log', 'w+') as dup_file:
            with open('heirarchy.json', 'w+') as heirarchy_file:
                with open('heirarchy_raw.json', 'w+') as _raw:
                    self.write_analysis(dup_file, heirarchy_file, _raw)

    def generate_minions(self):
        print("Parsing logs. This may take some time...")
        count = 0
        start = datetime.now()
        for dictionary in self.dict_list:
            count += 1
            minion = KeyMinion(dictionary)
            minion.check_keys()
            self.minions.append(minion)
        end = datetime.now()
        delta = (end - start)
        total_seconds = str(delta.total_seconds())
        print(
            "Parsed {} logs in {} seconds.".format(str(count), total_seconds)
        )

    def write_analysis(self, dup_file, heirarchy_file, _raw):
        for minion in self.minions:
            self._write_duplicate(minion, dup_file)
            self._write_heirarchy(minion, heirarchy_file, _raw)

    def _write_duplicate(self, minion, file_):
        if minion.duplicates and (
           minion.duplicates not in self.duplicate_sets):
            file_.write("Duplicate keys: {}\n".format(minion.duplicates))
            file_.write(
                "Example:\n{}\n"
                "".format(json.dumps(minion.dictionary, indent=4))
            )
            self.minions_w_duplicates.append(minion)
            self.duplicate_sets.append(minion.duplicates)

    def _write_heirarchy(self, minion, model, raw):
        if minion not in self.minions_format_logged:
            if minion.tiered:
                model.write("{}\n".format(json.dumps(minion.model, indent=4)))
                raw.write(
                    "{}\n".format(json.dumps(minion.dictionary, indent=4))
                )
                self.minions_format_logged.append(minion)

    def seek_key(self, key_list=None):
        key_dict = {k: [] for k in key_list}
        for minion in self.minions:
            for key in key_list:
                if key in minion.key_ring:
                    key_dict[key].append(minion)
        return key_dict
