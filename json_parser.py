import argparse

from utils.argparser import add_parser_args
from json_tools.keyfinder import KeyMaster
from json_tools.serializer import serialize_json_from_file


class Inspector:

    def __init__(self, log_master, out_file):
        self.master = log_master
        self.options_dict = {
            'k': self.seek_key,
        }
        self.minion_cache = []

    def main(self):
        while True:
            # Print Options
            arg = input('What would you like to do? ')
            print()

            if arg == 'quit':
                break

            try:
                self.options_dict[arg]()
            except (KeyError):
                print("Invalid input '{}'. Please try again".format(arg))
                continue

    def seek_key(self):
        while True:

            while True:
                keys = input('Enter keys (q to quit): ')
                print()
                if keys == 'q':
                    return
                if keys:
                    key_list = keys.split(' ')
                    break
                else:
                    print('Not a valid list of keys.\n')

            key_dict = self.master.seek_key(key_list=key_list)
            count = 0
            print("Overlapping results:")
            for key, value in key_dict.items():
                log_count = len(value)
                count += log_count
                print(
                    "    Key '{}' was found in {} logs"
                    "".format(key, str(log_count))
                )

            print("\nUnique model results:")
            total_unique_models = set()
            for key, value in key_dict.items():
                unique_models = set()
                for minion in value:
                    if minion.hash not in unique_models:
                        unique_models.add(minion.hash)
                        if minion.hash not in total_unique_models:
                            total_unique_models.add(minion.hash)
                model_count = len(unique_models)
                print(
                    "    Key '{}' was found in {} models"
                    "".format(key, str(model_count))
                )
            unique_model_count = str(len(total_unique_models))
            print(
                "TOTAL UNIQUE LOG MODELS: {}"
                "".format(unique_model_count)
            )
            break

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    add_parser_args(parser)
    args = parser.parse_args()

    if not args.input_file:
        exit('No input file identified. See \'-h\' for help.')
    if not args.output_file:
        exit('No output file identified. See \'-h\' for help.')

    print("Reading from file. This may take some time...")
    dict_list = serialize_json_from_file(args.input_file)
    print("Done reading from file.")

    master = KeyMaster(dict_list)
    master.generate_minions()
    
    inspector = Inspector(master, args.output_file)
    inspector.main()

    # master = KeyMaster()

    exit()
