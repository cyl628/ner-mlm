import pandas as pd
import os
import json
from transformers import AutoConfig, RobertaConfig, BertConfig, RobertaTokenizer, BertTokenizer

def load_tag_mapping(datadir):
    filepath = os.path.join(datadir, 'tag_mapping.txt')
    df = pd.read_csv(filepath, sep='\t', header=None)
    tag_mapping = dict(zip(list(df[0]), list(df[1])))
    return tag_mapping

def get_mapped_tag_list(datadir, tag_mapping):
    filepath = os.path.join(datadir, 'tags.txt')
    mapped_tag_list = []
    with open(filepath, 'r', encoding='utf-8')as f:
        lines = f.readlines()
        for line in lines:
            mapped_tag_list.append(tag_mapping[line.strip()])
    return mapped_tag_list

def get_tag2inputid(tokenizer, mapped_tag_list):
    splitted_tags = [list(set(tag.split('/'))) for tag in mapped_tag_list]
    d ={}
    for i, splitted_tag in enumerate(splitted_tags):
        d[mapped_tag_list[i]] = tokenizer.convert_tokens_to_ids(splitted_tag)
    return d

def get_tokenizer(model_name):
    tokenizer = None
    config = AutoConfig.from_pretrained(model_name)
    if isinstance(config, RobertaConfig):
        tokenizer = RobertaTokenizer.from_pretrained(model_name)
    elif isinstance(config, BertConfig):
        tokenizer = BertTokenizer.from_pretrained(model_name)
    else:
        print('unsupported model name')
    return tokenizer

class ResultLog:
    '''
    create json log
    {
        model_name:
        train_file:
        val_file:
        test_file:
        seed:
        model_save_dir:
        result: {
            0: {
                train_loss: 
                train_acc: 
                val_acc: 
            }
            ...
        }
    }
    '''
    def __init__(self, args, save_path):
        d = vars(args)
        d['result'] = {}
        with open(save_path, 'w')as f:
            f.write(json.dumps(d))
        self.save_path = save_path

    def update(self, epoch, data):
        with open(self.save_path, 'r+')as f:
            d = json.load(f)
            f.seek(0)
            f.truncate()
            d['result'][epoch] = data
            f.write(json.dumps(d))

    def delete(self):
        os.remove(self.save_path)


    

    