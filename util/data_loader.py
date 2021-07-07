# %%
import torch
import torch.utils.data as data
import os
import numpy as np
# from word_encoder import BERTWordEncoder

import random
random.seed(0)

def sample_by_ratio(datalist, ratio):
    sample_num = max(1, int(len(datalist)*ratio+0.5)) # at least one
    return list(random.sample(datalist, sample_num))

class Sample:
    def __init__(self, words, tag, label, pos):
        self.words = words
        self.tag = tag
        self.label = label
        self.pos = list(pos)
    
    def highlight(self, highlight_tokens):
        self.words.insert(self.pos[0], highlight_tokens[0])
        self.words.insert(self.pos[1]+1, highlight_tokens[1])
        # update pos
        self.pos = [self.pos[0]+1, self.pos[1]+1]

    def valid(self, max_length):
        return self.pos[1] <= max_length and len(self.words) <= max_length


class EntityTypingDataset(data.Dataset):
    """
    Fewshot NER Dataset
    """
    def __init__(self, datadir, mode, max_length, tag2idx, tag_mapping, highlight_entity=None, sample_rate=None):
        filepath = os.path.join(datadir, f'{mode}.txt')
        if not os.path.exists(filepath):
            print(f"[ERROR] Data file {filepath} does not exist!")
            assert(0)
        self.samples = []
        self.max_length = max_length
        self.tag2id = tag2idx
        self.tag_mapping = tag_mapping
        self.highlight_entity = highlight_entity
        self.sample_rate = sample_rate
        self.__load_data_from_file__(filepath)
        self.__sample_data__()


    def __sample_data__(self):
        if self.sample_rate is None or self.sample_rate == 1:
            return

        assert self.sample_rate > 0 and self.sample_rate < 1, print(f'expected rample rate in (0,1], invalid sample rate {self.sample_rate}')
        # for each type of entity, sample by sample_rate
        sample_group = {}
        for sample in self.samples:
            if sample.tag in sample_group:
                sample_group[sample.tag].append(sample)
            else:
                sample_group[sample.tag] = [sample]
        for tag in sample_group:
            sample_group[tag] = sample_by_ratio(sample_group[tag], self.sample_rate)
        self.samples = [sample for sample_list in list(sample_group.values()) for sample in sample_list]
    
    def __load_data_from_file__(self, filepath):
        with open(filepath, 'r', encoding='utf-8')as f:
            lines = f.readlines()
        for line in lines:
            linelist = line.strip().split('\t')
            start = int(linelist[0])
            end = int(linelist[1])
            tag = linelist[3]
            # map tags
            tag = self.tag_mapping[tag]
            label = self.tag2id[tag]
            words = linelist[2].split(' ')
            sample = Sample(words, tag, label, (start, end))
            if sample.valid(self.max_length):
                self.samples.append(sample)
            
            # add <ENTITY> </ENTITY> 
        if self.highlight_entity:
            for sample in self.samples:
                sample.highlight(self.highlight_entity)
    
    def __getitem__(self, index):
        # get raw data
        return self.samples[index]

    def __len__(self):
        return len(self.samples)

def collate_fn(samples):
    batch_data = {'words':[], 'labels':[], 'entity_pos':[]}
    for sample in samples:
        batch_data['words'].append(sample.words)
        batch_data['labels'].append(sample.label)
        batch_data['entity_pos'].append(sample.pos)
    batch_data['labels'] = torch.LongTensor(batch_data['labels'])
    batch_data['entity_pos'] = torch.LongTensor(batch_data['entity_pos'])
    return batch_data

def get_loader(dataset, batch_size, num_workers=8, collate_fn=collate_fn):
    data_loader = data.DataLoader(dataset=dataset,
            batch_size=batch_size,
            shuffle=True,
            pin_memory=True,
            num_workers=num_workers,
            collate_fn=collate_fn, drop_last=True)
    return data_loader
# %%
