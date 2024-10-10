from dataclasses import dataclass, fields, asdict
from collections import OrderedDict
from typing import Optional, List, Dict

class DictMixin:
    '''Superclass providing dict-like methods'''

    @classmethod
    def get_fields(cls):
        return [field.name for field in fields(cls)]
    
    @classmethod
    def from_dict(cls, d):
        '''Convert dictionary to an instance of the subclass'''
        field_names = (field.name for field in fields(cls))
        return cls(**{k: v for k, v in d.items() if k in field_names})

    def to_dict(self):
        '''Convert instance to dictionary'''
        return asdict(self)
    
    def __getitem__(self, key):
        '''Enable dictionary-style access'''
        return getattr(self, key)

    def __setitem__(self, key, value):
        '''Enable dictionary-style setting of values'''
        setattr(self, key, value)

    def get(self, key, default=None):
        '''Mimic dictionary get method'''
        return getattr(self, key, default)
    
@dataclass
class ArticleInfo(DictMixin):
    url: str
    title: str
    name: str

@dataclass
class ArticleSection(DictMixin):
    id: str
    title: str
    text: str
    url : str

@dataclass
class Article(DictMixin):
    info: ArticleInfo
    summary : str
    sections: Dict[str, ArticleSection]
    
@dataclass
class ArticleChunk:
    chunk_id : str
    chunk_text : str
    n_tokens : int
    article_section : ArticleSection
    article : Article
    
    @staticmethod
    def get_text_field_name():
        '''Return the name of the length field'''
        return "chunk_text"
    
    @staticmethod
    def get_length_field_name():
        '''Return the name of the length field'''
        return "n_tokens"