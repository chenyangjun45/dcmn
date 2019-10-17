# !/usr/bin/env python3
import preprocess, model, train
import mxnet as mx
from mxnet import gluon, init
import logging, argparse

parser = argparse.ArgumentParser(description='Train DMCN model')
parser.add_argument('--train_sentences', type=str, default='data/train.jsonl', help='Training set \
                    observations and hypotheses')
parser.add_argument('--train_labels', type=str, default='data/train-labels', help='Training set labels')
parser.add_argument('--test_sentences', type=str, default='data/dev.jsonl', help='Test set observations and hypotheses')
parser.add_argument('--test_labels', type=str, default='data/dev-labels', help='Test set labels')

args = parser.parse_args()

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

if __name__ == '__main__':
    dataloader_train = preprocess.get_dataloader(args.train_sentences, args.train_labels)
    dataloader_test = preprocess.get_dataloader(args.test_sentences, args.test_labels)
    dmcn = model.DMCN(dp_prob=.3)
    dmcn.initialize(init=init.Uniform(.03), ctx=mx.gpu())
    loss_func = gluon.loss.SoftmaxCrossEntropyLoss()
    lr, clip = .001, 2.5
    trainer = gluon.Trainer(dmcn.collect_params(), 'adam', {'learning_rate': lr, 'clip_gradient': clip})
    train.train_valid(dataloader_train, dataloader_test, dmcn, loss_func, trainer, num_epoch=10, ctx=mx.gpu())
