import unicodecsv as csv
import logging
import os

class OnsCodeLookup:

    NAME_SUFFIX = 'NM'
    CODE_SUFFIX = 'CD'

    # Community Safety Partnership lookup files
    # IMPORTANT: This array MUST be sorted in ascending date order, i.e. so the last file
    # in the list is the most recent
    CSP_FILES = [
        'Community_Safety_Partnerships_December_2016_Names_and_Codes_in_England.csv',
        'Community_Safety_Partnerships_July_2016_Names_and_Codes_in_England.csv',
        'Community_Safety_Partnerships_December_2017_Names_and_Codes_in_England.csv'
    ]

    # Local Authority District lookup files
    # IMPORTANT: This array MUST be sorted in ascending date order, i.e. so the last file
    # in the list is the most recent
    LAD_FILES = [
        'Local_Authority_Districts_April_1991_Names_and_Codes_in_England_and_Wales.csv',
        'Local_Authority_Districts_April_2015_Names_and_Codes_in_the_United_Kingdom.csv',
        'Local_Authority_Districts_February_2016_Names_and_Codes_in_the_United_Kingdom.csv',
        'Local_Authority_Districts_December_2016_Names_and_Codes_in_the_United_Kingdom.csv',
        'Local_Authority_Districts_December_2017_Names_and_Codes_in_the_United_Kingdom.csv',
    ]

    lookups = None

    def __init__(self, ):

        # Memoise the lookups table
        if self.lookups is None:
            self.__load_lookup_tables()

    def code_for(self, entity_type, name):
        lookup_key = entity_type.value
        return self.lookups['from_name'].get(lookup_key, {}).get(name, None)

    def name_for(self, ons_code):
        return self.lookups['from_code'].get(ons_code, None)

    @classmethod
    def __load_lookup_tables(cls):
        """
        Only load lookups once per runtime, as it's expensive
        """
        cls.lookups = {
            'from_code': {},
            'from_name': {}
        }

        for filename in (cls.CSP_FILES + cls.LAD_FILES):
            cls.__load_lookup_csv(filename)

    @classmethod
    def __load_lookup_csv(cls, filename):
        package_directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(package_directory, 'data', 'lookups', filename)

        # A fair few files include the BOM, so cater for that with the encoding
        with open(path, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, encoding='utf-8-sig')
            for row in reader:
                name_key = next(
                    (key for key in row if key.endswith(cls.NAME_SUFFIX)), {})
                code_key = next(
                    (key for key in row if key.endswith(cls.CODE_SUFFIX)), {})

                name_value = row[name_key]
                code_value = row[code_key]

                # Trim 4 characters, 2 for the year + 2 for the code suffix, e.g.
                #   LAD16CD => LAD
                entity_type_value = code_key[:-4]
                if entity_type_value not in cls.lookups['from_name']:
                    cls.lookups['from_name'][entity_type_value] = {}

                if code_value in cls.lookups['from_code']:
                    logging.debug("code {} already exists".format(code_value))

                if name_value in cls.lookups['from_name']:
                    logging.debug("code {} already exists".format(code_value))

                cls.lookups['from_code'][code_value] = name_value
                cls.lookups['from_name'][entity_type_value][name_value] = code_value
