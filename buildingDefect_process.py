# https://towardsdatascience.com/no-labels-no-problem-30024984681d
# https://machinelearningmastery.com/expectation-maximization-em-algorithm/

import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split
import pandas as pd
from collections import Counter
import itertools
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
import spacy
import re
import time, datetime

def plot_data(keys, values, title):
    plt.figure(figsize=(8,4))
    plt.bar(keys, values)
    plt.xticks(rotation=90)
    plt.subplots_adjust(bottom=0.3)
    plt.title = title
    plt.show()

 
def open_file(file_name, hdr = 0):
    # Load data
    df = pd.read_csv(file_name, header=hdr)
    return df

def get_insight_category(df):
    #df_Category = df.groupby('Category')['Category'].nunique()

    print('Number of unique values in each column')
    print(df.nunique(axis=0))
    print('\n')

    df_category = df.Category.value_counts().to_frame().reset_index()
    df_category.columns = ['Category', 'Count']
    print('Number of records per Category')
    print(df_category)
    print('\n')

    plot_data(df_category.Category, df_category.Count, 'Category')

def get_insight_status(df):
    df_status = df.Status.value_counts().to_frame().reset_index()
    df_status.columns = ['Status', 'Count']
    print('Number of records per Category')
    print(df_status)
    print('\n')

    plot_data(df_status.Status, df_status.Count, 'Status')


def open_excel(file_name):
    column_names = ['Project', 'Location', 'Date Raised', 'Rectified Date', 'Category',
       'Subcategory', 'Root Cause', 'Cost Attribute', 'Status', 'Description']

    df = pd.DataFrame(columns=column_names)

    # Load data
    excel_file = pd.ExcelFile(file_name)
    sheet_names = excel_file.sheet_names
    print('Sheet names:', sheet_names)

    for sheet in sheet_names:
        df_excel = excel_file.parse(sheet)
        df_sheet = pd.DataFrame(columns=column_names)
        for col in column_names:
            if col in df_excel.columns:
                df_sheet[col] = df_excel[col]
        df = df.append(df_sheet, ignore_index=True)
    return df

def count_words(df):
    from sklearn.feature_extraction.text import CountVectorizer
    from collections import Counter

    categories = df['Category'].unique()

    df_count = pd.DataFrame(columns=['word','count', 'category'])
    nlp = spacy.load("en_core_web_sm")

    df = df[df['rooms'].notna()]

    for category in categories:
        print('Category:', category)
        df_category = df[df.Category == category]

        # now still include empty rooms
        room_list = df_category.rooms.tolist()

        vocabs = []
        for room in room_list:
            room_rows = room.split(',')
            vocabs.extend(room_rows)

        vocabs_common = dict(Counter(vocabs).most_common(10))
        for key, value in vocabs_common.items():
            new_row = {'word':key,'count':value,'category':category}
            df_count = df_count.append(new_row, ignore_index=True)
        
    return df_count

def count_rooms_per_category(df):
    from collections import Counter

    categories = df['Category'].unique()

    df_count = pd.DataFrame()

    df = df[df['rooms'].notna()]

    # loop through categories
    for category in categories:
        print('Category:', category)
        df_per_category = df[df.Category == category]

        # now still include empty rooms
        ws_room_list = df_per_category.rooms.tolist()

        room_per_categories = []
        for ws_room in ws_room_list:
            room_rows = ws_room.split(',')
            room_per_categories.extend(room_rows)

        rooms_common = dict(Counter(room_per_categories).most_common(10))
        for key, value in rooms_common.items():
            new_row = {'category':category,'room':key,'room_count':value}
            df_count = df_count.append(new_row, ignore_index=True)
        
    return df_count

def count_categories_per_room(df):
    df = df[df['rooms'].notna()]

    # get base rooms
    excel_file = pd.ExcelFile('building_elements.xlsx')
    df_rooms = pd.read_excel(excel_file, "rooms")
    base_rooms = df_rooms['room']

    categories = df['Category'].unique()

    # dataframe to keep result
    df_count = pd.DataFrame()

    # add categories per room
    df_temp = pd.DataFrame()
    for ws_index, ws_row in df.iterrows():
        category = ws_row['Category']
        ws_rooms = str(ws_row['rooms']).split(',')
        for ws_room in ws_rooms:
            for base_room in base_rooms:
                if ws_room == base_room:
                    new_row = {'room':base_room,'category':category}
                    df_temp = df_temp.append(new_row, ignore_index=True)

    # count categories per room
    for base_room in base_rooms:
        print(base_room)
        df_temp_room = df_temp.loc[df_temp['room'] == base_room]
        temp_categories = df_temp_room['category'].tolist()
        for category in categories:
            num_rooms = temp_categories.count(category)
            if num_rooms > 0:
                new_row = {'room':base_room,'category':category,'category_count':num_rooms}
                df_count = df_count.append(new_row, ignore_index=True)
        
    return df_count

def clean_category(df):

    df.dropna(subset=['Category'], inplace = True)

    df = df[df.Category != 'No Defect/Damage']

    df.loc[df.Category.str.contains(' / '), 'Category'] = df.Category.str.replace(' / ', '/')
    df.loc[df.Category.str.contains('/ '), 'Category'] = df.Category.str.replace('/ ', '/')

    mylist = ['Balustrades','Lifts','Shower Screens']
    pattern = '|'.join(mylist)
    df.loc[df.Category.str.contains(pattern), 'Category'] = df.Category.str.rstrip('s')

    df.loc[df.Category=='Balustrading', 'Category'] = 'Balustrade'

    df.loc[df.Category=='Windows/FaÃ§ade', 'Category'] = 'Windows/Facade'

    #print(sorted(df['Category'].unique()))

    return df

def move_categories(df, old_category, new_category):
    df.loc[df.Category == old_category, 'Category'] = new_category
    return df

def make_data_for_prediction(df):
    categories_for_prediction = ['No Category', 'Misc', 'Defect']
    df = df[df.Category.isin(categories_for_prediction)]
    df = df[['Category','Description']]
    return df

def clean_category_for_model(df):
    unused_categories = ['No Category', 'Misc', 'No Defect/Damaged', 'New Type', 'Defect', 'Inspection Defect', 'Signage', 'Cleaning']
    df = df[~df.Category.isin(unused_categories)]

    # move similar category
    move_categories(df, 'Windows', 'Windows/Facade')
    move_categories(df, 'Facade', 'Windows/Facade')
    move_categories(df, 'Fire', 'Fire Services')
    move_categories(df, 'Fire Pipe', 'Fire Services')
    move_categories(df, 'Tiling', 'Tile/Stone/Caulking')
    move_categories(df, 'Tile/Stone', 'Tile/Stone/Caulking')

    # remove records that it's category has less than 10 entities
    value_counts = df.Category.value_counts()
    to_keep = value_counts[value_counts >= 10].index
    df = df[df.Category.isin(to_keep)]

    return df

def calculate_response_days(df):
    # these are special cases to handle input errors, that changing month to day does not work
    special_date_raised = ['16/08/2019','26/08/2018', '23/01/2017','23/12/2019']
    new_rectified_date = ['16/08/2019','23/09/2018', '15/08/2017','31/01/2020']

    df.dropna(subset=['Rectified Date'], inplace = True)
    df.drop(df.loc[df['Date Raised']=='0000-00-00'].index, inplace=True)
    for index, row in df.iterrows():
        change_date = ''
        rectified_date = split_convert_date(row['Rectified Date'])
        date_raised = convert_date(row['Date Raised'])
        date_format = "%m/%d/%Y"
        date_raised_dt = datetime.date.fromtimestamp(time.mktime(time.strptime(date_raised, "%d/%m/%Y")))
        rectified_date_dt = datetime.date.fromtimestamp(time.mktime(time.strptime(rectified_date, "%d/%m/%Y")))
        response_days = (rectified_date_dt - date_raised_dt).days
        if response_days < 0:
            # rectified date is incorrect, change it month to day
            try:
                rectified_date_dt = datetime.date.fromtimestamp(time.mktime(time.strptime(rectified_date, "%m/%d/%Y")))
                change_date = 'rectified'
            except ValueError:
                # failed because month > 12, now try to change the date_raised
                try:
                    date_raised_dt = datetime.date.fromtimestamp(time.mktime(time.strptime(date_raised, "%m/%d/%Y")))
                    change_date = 'raised'
                except ValueError:
                    # both dates are failed, leave them 
                    change_date = 'special'
                    idx = special_date_raised.index(date_raised)
                    rectified_date = new_rectified_date[idx]
                    rectified_date_dt = datetime.date.fromtimestamp(time.mktime(time.strptime(rectified_date, "%d/%m/%Y")))

            response_days = (rectified_date_dt - date_raised_dt).days

        df.loc[index, 'change_date'] = change_date
        df.loc[index, 'rectified_date'] = rectified_date
        df.loc[index, 'date_raised'] = date_raised
        df.loc[index, 'response_days'] = response_days

    return df

def extract_location(df):
    import inflect
   
    df[['room_location']] = ''

    # replace mistype
    df['Location'] = df['Location'].str.replace(':evel','Level')

    # Bulk set room location
    df.loc[df.Location.str.contains('ground', case=False), 'room_location'] = 'ground'
    df.loc[df.Location.str.contains('unit g', case=False), 'room_location'] = 'ground'
    df.loc[df.Location.str.contains('common', case=False), 'room_location'] = 'common'
    df.loc[df.Location.str.contains('basement', case=False), 'room_location'] = 'basement'
    df.loc[df.Location.str.contains('TH'), 'room_location'] = 'townhouse'
    df.loc[df.Location.str.contains('townhouse', case=False), 'room_location'] = 'townhouse'
    df.loc[df.Location.str.contains('roof', case=False), 'room_location'] = 'roof'

    # extract level by ordinal numbers
    print_once = True
    for index, row in df.iterrows():
        if row['room_location'] == '':
            x = re.search(r"(level\s?)([1-9][0-9]|0?[1-9]|0)", row['Location'], re.IGNORECASE)
            if x != None:
                if x.group(2) == '0':
                    df.loc[index, 'room_location'] = 'ground'
                else:
                    df.loc[index, 'room_location'] = 'level ' + x.group(2)

        if row['room_location'] == '':
            x = re.search(r"(unit |\w*[A-Z])([1-9][0-9][0-9]|0?[1-9][0-9]|0?[1-9])", row['Location'], re.IGNORECASE)
            if x != None:
                if len(x.group(2)) == 3:
                    # example Unit 301 will be on level 3
                    lvl = x.group(2)[0:1]
                    df.loc[index, 'room_location'] = 'level ' + lvl
                else:
                    # example unit 15 will be on ground floor
                    df.loc[index, 'room_location'] = 'ground'

        # detect first, second, etc
        if row['room_location'] == '':  
            p = inflect.engine()
            for i in range(1,10):
                level_ordinal = p.number_to_words(p.ordinal(i))
                if level_ordinal in row['Location'].lower():
                    df.loc[index, 'room_location'] = 'level ' + str(i)

    return df

def clean_text(sentence, df_word_replace):
    sentence = re.sub('[^A-Za-z0-9 ]+', ' ', sentence)
    sentence = re.sub(r'log|_x000d_|_x000D_|x000d|x000D|#NAME\?|Ã¢â‚¬Â¦', ' ', sentence)

    for index, row in df_word_replace.iterrows():
        correct_word = '' if pd.isna(row['correct_word']) else row['correct_word']
        sentence = sentence.replace(row['typo_word'], correct_word)

    return sentence

def extract_status(df):
    for index, row in df.iterrows():
        status_text = row['Status']
        status_list = status_text.split(">")
        df.loc[index, 'last_status'] = status_list[-1]
    return df

def clean_description(df):

    df.dropna(subset=['Description'], inplace = True)

    df = df[~df.Description.str.contains('Testing entry|Testing email')] # remove Testing records

    # open data typo words and their replacement
    excel_file = pd.ExcelFile('building_elements.xlsx')
    df_typos = pd.read_excel(excel_file, "typos")

    # Drop description that has less than 2 words
    # Remove junk words from description
    for index, row in df.iterrows():
        description = clean_text(row['Description'], df_typos)
        df.loc[index, 'Description'] = description
        if (len(description.split(' ')) < 2): 
            df.loc[index, 'Description'] = ''

    # Drop empty description
    df = df[df.Description != '']

    return df

def augment_text(df):
    # Joinery 1466, Signage 10
    print('augment_text')
    import nltk
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    import nlpaug
    import nlpaug.augmenter.word as naw
    import math

    aug = naw.SynonymAug(aug_src='wordnet',aug_max=10) # maximum 10 words to be changed

    # get only column category and description
    df = df[['Category','Description']]

    # augment only if cases less than 100
    df_category = df.Category.value_counts().to_frame().reset_index()
    df_category.columns = ['Category', 'Count']
    df_aug = df_category[df_category.Count < 1000]

    for entry, row_aug in df_aug.iterrows():
        aug_cat = row_aug['Category']
        print(aug_cat)
        aug_num = 1000 - row_aug['Count'] #total number of text to be augmented
        data = df[df.Category == aug_cat] # collect data per category
        num_rows_per_category = len(data) # number of data per category
        aug_num_per_text = math.ceil(aug_num / num_rows_per_category) # how many augmentation needed
        print(num_rows_per_category, aug_num_per_text)
        for index, row in data.iterrows():
            new_text_list = aug.augment(row['Description'],n=aug_num_per_text)
            if type(new_text_list) is str: 
                new_text_list = [new_text_list]
            for new_text in new_text_list:
                dict = {'Category': aug_cat, 'Description': new_text}
                df = df.append(dict, ignore_index = True)

    return df

def extract_elements(df):
    
    from pattern.text.en import singularize, pluralize

    # get base data
    excel_file = pd.ExcelFile('building_elements.xlsx')
    df_elements = pd.read_excel(excel_file, 'elements')
    df_rooms = pd.read_excel(excel_file, 'rooms')
  
    building_elements = df_elements.iloc[:,0].to_list()

    # room dictionary
    rooms_list = []

    nlp = spacy.load("en_core_web_sm")
    special_words = ['oven','stove']

    for index, row in df.iterrows():
        description = row['Description']
        #print(description)
        category = row['Category'].lower()
        print(index)
        doc = nlp(description)

        noun_chunks = set()
        for np in doc.noun_chunks:
            noun_chunks.add(np.text)

        desc_elements = set()
        desc_phrases = set()
        desc_rooms = set()

        # find room based on description
        for key, row in df_rooms.iterrows():
            room_elements = str(row['room_elements']).split(',')
            room_elements = [room_element.strip() for room_element in room_elements]
            #print('elements',room_elements)
            description_lower = description.lower()
            found_keyword = any(room_element in description_lower for room_element in room_elements)

            found_exclude = False
            if not pd.isna(row['exclude']):
                room_excludes = str(row['exclude']).split(',')
                room_excludes = [room_exclude.strip() for room_exclude in room_excludes]
                found_exclude = any(room_exclude in description_lower for room_exclude in room_excludes)
            
            #print(found_keyword, found_exclude)

            if found_keyword and not found_exclude:
                #print('found')
                desc_rooms.add(row['room'])

        # find elements in description        
        for token in doc:
            word = token.text.lower()
            phrase = token.text              

            # if words are noun plural, change it to singular
            if token.tag_ == "NNS":
                word = singularize(word)
            
            # if word is noun, check against building element vocabularies
            # or eventhough word is not noun, but it's in special categories, add them it
            if (token.tag_[0:2] == "NN" or word in special_words) and (word in building_elements):
                matching = []  
                if len(noun_chunks) > 0:
                    noun_chunks_list = list(noun_chunks)
                    matching = [s for s in noun_chunks_list if token.text in s]

                desc_elements.add(word)

                # Find noun phrase
                if matching != []:
                    desc_phrases.update(matching) # extend adds list items
                else:
                    desc_phrases.add(phrase) # append adds list/item

        # save room such as bathroom, kitchen
        rooms = ''
        if len(desc_rooms) > 0:
            rooms = ','.join(desc_rooms)
        df.loc[index,'rooms'] = rooms

        # save element such as floorboard, tile
        elements = ''
        if len(desc_elements) > 0:
            elements = ','.join(desc_elements)
        
        # save element phrase such as kitchen sink
        phrases = ''
        if len(desc_phrases) > 0:
            phrases = ','.join(desc_phrases)

        # if elements is empty, use room
        if elements == '' and rooms != '':
            elements = rooms
            phrases = rooms

        df.loc[index,'elements'] = elements
        df.loc[index,'phrases'] = phrases

    return df


def main():
    process_index = 'clean' # merge, clean, select_categories, extract_elements, count_words, aug, predict

    excel_file = 'Deakin Requested Defect List (Projects 1-5).xlsx'
    csv_file = 'wiseworking.csv' # merge 3 excel sheets into 
    file_clean = 'wiseworking_clean.csv' # clean data
    file_elements = 'wiseworking_elements.csv' # contain building elements for each description
    file_ready = 'wiseworking_ready.csv' # ready for modelling
    file_train = 'wiseworking_train.csv' # data augmentation
    file_test = 'wiseworking_test.csv' # data augmentation
    file_predict = 'wiseworking_predict.csv' # after augmentation and only desc and category columns
    file_count = 'wiseworking_count.xlsx' # count occurances 

    if process_index == 'merge':
        df = open_excel(excel_file)
        df.to_csv(csv_file, index = False)
        get_insight_category(df)
        get_insight_status(df)

    if process_index == 'clean':
        df = open_file(csv_file)
        df = clean_category(df)
        df = clean_description(df)
        df = extract_location (df)
        df = extract_status(df)
        df = calculate_response_days(df)
        df.to_csv(file_clean, index = False)

    # remove low counts categories
    if process_index == 'select_categories':
        df = open_file(file_clean)
        df = clean_category_for_model(df)
        df.to_csv(file_ready, index = False)

    if process_index == 'extract_elements':
        df = open_file(file_ready)
        df = extract_elements(df)
        df.to_csv(file_elements, index = False) 

    if process_index == 'count_words':
        df = open_file(file_elements)

        writer = pd.ExcelWriter(file_count, engine='openpyxl')

        df_count = count_rooms_per_category(df)
        df_count.to_excel(writer, sheet_name = 'rooms_per_category', index = False)

        df_count = count_categories_per_room(df)
        df_count.to_excel(writer, sheet_name = 'category_per_rooms', index = False)

        writer.save()

    if process_index == 'aug':
        df = open_file(file_ready) 

        # divide data into train and test

        X = df[['Description']]
        y = df[['Category']]

        X_train, X_test, y_train, y_test = train_test_split(X,y, test_size = 0.2, random_state = 1, stratify = df['Category'])

        df_test = pd.DataFrame(columns=['Category', 'Description'])
        df_test['Category'] = y_test
        df_test['Description'] = X_test
        df_test.to_csv(file_test, index = False)

        df_train = pd.DataFrame(columns=['Category', 'Description'])
        df_train['Category'] = y_train
        df_train['Description'] = X_train

        df = augment_text(df_train)
        get_insight_category(df)
        df.to_csv(file_train, index = False)

    if process_index == 'predict':
        df = open_file(file_clean)
        df = make_data_for_prediction (df)
        df.to_csv(file_predict, index = False)

    print('Finish ', process_index)


def check_sentence(sentence):
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(sentence)

    has_noun = False
    has_verb = False
    has_adj = False
    is_sentence_ok = False

    for chunk in doc.sents:
        for tok in chunk:
            print(tok, tok.pos_)
            if tok.pos_ == "NOUN" or tok.pos_ == "PROPN":
                has_noun = True
            if tok.pos_ == "ADJ":
                has_adj = True
            if tok.pos_ == "VERB":
                has_verb = True
            if (has_noun and has_adj) or (has_noun and has_verb) or (has_adj and has_verb):
                is_sentence_ok = True
                break
        if is_sentence_ok:
            #print('hi2')
            break

    if not is_sentence_ok:
        print(sentence)

    return is_sentence_ok

def test_spacy_graph():
    from spacy import displacy 
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("Toilet flushing issue") 
    displacy.serve(doc, style="dep")

def convert_date(date_text):
    date_patterns = ["%d/%m/%Y", "%d-%m-%Y","%Y-%m-%d"]
    target_format = "%d/%m/%Y"
    date_time_string = date_text.split()
    date_string = date_time_string[0]
    
    # Find date pattern
    original_format = ''
    for date_pattern in date_patterns:
        if original_format == '':
            try:
                time.strptime(date_string, date_pattern)
                original_format = date_pattern
            except ValueError:
                pass

    # convert date to certain date format    
    converted_date = date_string
    if original_format == '':
        print('missing format for this date: ', converted_date)
    else:
        converted_date = datetime.datetime.strptime(date_string,original_format).strftime(target_format)
    #print('new date:', converted_date)
    return converted_date

def split_convert_date(date_text):
    date_list = date_text.split(">")
    new_dates = []
    for date_text in date_list:
        new_dates.append(convert_date(date_text.strip()))
    new_dates.sort(key=lambda x: time.mktime(time.strptime(x,'%d/%m/%Y')), reverse=True)
    return new_dates[0]

if __name__ == "__main__":
    main()
    





