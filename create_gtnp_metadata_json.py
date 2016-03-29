import csv
import json
import getopt
import sys

def read_metadata_csv(csv_overrides):
    csv_data = []
    field_names = None
    is_header = True
    with open(csv_overrides) as csv_values:
        reader = csv.reader(csv_values, delimiter=',', quotechar='"')
        for row in reader:
            if is_header:
                field_names = row
                is_header = False
            else:
                csv_data.append(row)

    return field_names, csv_data

def read_json_template(json_template):
    data = None
    with open(json_template) as data_file:
        data = json.load(data_file)
    return data

def traverse(obj, path=None, callback=None):
    if path is None:
        path = []

    if isinstance(obj, dict):
        value = dict((k, traverse(v, path + [k], callback))
                    for k, v in obj.items())
    elif isinstance(obj, list):
        value = obj
        if obj:
            value = [traverse(elem, path + [idx], callback)
                     for idx, elem in enumerate(obj)]
        else:
            value = [traverse('', path + [0], callback)]
    else:
        value = obj

    if callback is None:  # if a callback is provided, call it to get the new value
        return value
    else:
        return callback(path, value)

def process_column_name(entry):
    column_name = entry.strip()
    try:
        column_name = int(column_name)
    except ValueError:
        pass
    return column_name

def replace_metadata_values(json_data, replace_fields, csv_data):
    borehole_list = []
    for row in csv_data:
        borehole = {}
        split_fields = [map(process_column_name, field.split(':')) for field in replace_fields]
        def transformer(path, value):
            if path in split_fields:
                try:
                    replacement_value = row[split_fields.index(path)]
                    if replacement_value:
                        return replacement_value.strip()
                    else:
                        return value
                except IndexError:
                    return value
            else:
                return value
        borehole = traverse(json_data, callback=transformer)
        borehole_list.append(borehole)
    return {'Boreholes':borehole_list}

def create_gtnp_metadata_json(json_template, csv_overrides, out_file):
    json_metadata = None
    try:
        json_metadata = read_json_template(json_template)
        replace_fields, csv_metadata = read_metadata_csv(csv_overrides)
        borehole_dict = replace_metadata_values(json_metadata, replace_fields, csv_metadata)
        with open(out_file, 'w') as json_file:
            json.dump(borehole_dict, json_file, indent=3)
    except ValueError as valError:
        print valError

    return None

def parse_arguments(argv):
    """ Parse the command line arguments and return them. """
    json_template = None
    csv_overrides = None
    out_file = None
    try:
        opts, args = getopt.getopt(argv,"ht:c:o:",["json_template=","csv_overrides=","out_file="])
    except getopt.GetoptError:
        print 'create_gtnp_metadata_json.py -t <JSON template file> -c <CSV file with metadata values> -o <CSV output file>'
        sys.exit(2)

    found_json_template = False
    found_out_file = False
    found_csv_overrides = False
    for opt, arg in opts:
        if opt == '-h':
            print 'create_gtnp_metadata_json.py -t <JSON template file> -c <CSV file with metadata values> -o <CSV output file>'
            sys.exit()
        elif opt in ("-t", "--json_template"):
            found_json_template = True
            json_template = arg
        elif opt in ("-c", "--csv_overrides"):
            found_csv_overrides = True
            csv_overrides = arg
        elif opt in ("-o", "--out_file"):
            found_out_file = True
            out_file = arg
    if not found_json_template:
        print "JSON template with common dataset values '-t' argument required."
        sys.exit(2)
    if not found_csv_overrides:
        print "CSV file with entry specific values '-c' argument required."
        sys.exit(2)
    if not found_out_file:
        print "JSON output file '-o' argument required."
        sys.exit(2)
    return json_template, csv_overrides, out_file

if __name__ == '__main__':
    (json_template, csv_overrides, out_file) = parse_arguments(sys.argv[1:])

    create_gtnp_metadata_json(json_template, csv_overrides, out_file)