# !/usr/bin/env python3
import logging
import mxnet as mx
from mxnet import nd, gluon
import multiprocessing as mp
import gluonnlp as nlp
import numpy as np
from collections import defaultdict
from bert.embedding import BertEmbedding
from util import load_labels, load_sentences

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s')
logger = logging.Logger(__name__)
logger.setLevel(logging.WARNING)

def to_dataset(sentences, labels, ctx=mx.gpu(), batch_size=64, max_seq_length=25):
    '''
    this function will use BertEmbedding to get each fields' embeddings
    and load the given labels, put them together into a dataset
    '''
    bertembedding = BertEmbedding(ctx=ctx, batch_size=batch_size, max_seq_length=max_seq_length)
    print('Construct bert embedding for sentences')
    
    embs = []
    for sts in sentences:
        tokens_embs = bertembedding.embedding(sts)
        embs.append([np.asarray(token_emb[1]) for token_emb in tokens_embs])
    
    dataset = [list(obs_hyp_label) for obs_hyp_label in zip(*embs, labels)]
    return dataset

def get_length(dataset):
    '''
    lengths used for batch sampler, we will use the first field of each row
    for now, i.e., obs1
    '''
    return [row[0].shape[0] for row in dataset]

def to_dataloader(dataset, batch_size=64, num_buckets=10, bucket_ratio=.5):
    '''
    this function will sample the dataset to dataloader
    '''
    pads = [nlp.data.batchify.Pad(axis=0, pad_val=0) for _ in range(len(dataset[0])-1)]
    batchify_fn = nlp.data.batchify.Tuple(
        *pads,                      # for observations and hypotheses
        nlp.data.batchify.Stack()   # for labels
    )
    lengths = get_length(dataset)

    print('Build batch_sampler')
    batch_sampler = nlp.data.sampler.FixedBucketSampler(
        lengths=lengths, batch_size=batch_size, num_buckets=num_buckets,
        ratio=bucket_ratio, shuffle=True
    )
    print(batch_sampler.stats())

    dataloader = gluon.data.DataLoader(
        dataset, batch_sampler=batch_sampler, batchify_fn=batchify_fn
    )
    
    return dataloader

def get_dataloader(sts_filepath, label_filepath, keys=['obs1', 'obs2', 'hyp1', 'hyp2'], \
                   batch_size=64, num_buckets=10, bucket_ratio=.5, \
                   ctx=mx.gpu(), max_seq_length=25, sample_num=None):
    '''
    this function will use the helpers above, take sentence file path,
    label file path, and batch_size, num_buckets, bucket_ratio, to
    get the dataloader for model to us. sample_num controls how many
    samples in dataset the model will use, defualt to None, e.g., use all
    '''
    sentences = load_sentences(sts_filepath, keys=keys)
    sentences = [sts[:sample_num] for sts in sentences]
    labels = load_labels(label_filepath)[:sample_num]
    assert(len(sentences)==4 and len(sentences[0])==len(labels))

    dataset = to_dataset(sentences, labels, ctx=ctx, batch_size=batch_size, \
                         max_seq_length=max_seq_length)

    dataloader = to_dataloader(dataset=dataset, batch_size=batch_size, \
                               num_buckets=num_buckets, bucket_ratio=bucket_ratio)
    return dataloader