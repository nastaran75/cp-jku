#!/usr/bin/env python
import numpy as np

import theano.tensor as T

import lasagne
from lasagne.layers.dnn import Conv2DDNNLayer as Conv2DLayer
from lasagne.layers.dnn import batch_norm_dnn as batch_norm
from lasagne.layers.dnn import MaxPool2DDNNLayer as MaxPool2DLayer
from lasagne.layers import DropoutLayer, FlattenLayer, GlobalPoolLayer, NonlinearityLayer

from lasagne_wrapper.training_strategy import TrainingStrategy
from lasagne_wrapper.learn_rate_shedules import get_constant
from lasagne_wrapper.parameter_updates import get_update_adam
from lasagne_wrapper.batch_iterators import BatchIterator
from lasagne_wrapper.optimization_objectives import mean_pixel_binary_crossentropy

from asc.utils.data_jamendo import SPEC_BINS, SPEC_CONTEXT

INI_LEARNING_RATE = np.float32(0.001)

BATCH_SIZE = 10
MAX_EPOCHS = 1000
PATIENCE = 20
L2 = None

INPUT_SHAPE = [1, SPEC_CONTEXT, SPEC_BINS]

init_conv = lasagne.init.HeNormal


def prepare(X, y):
    """ Prepare data for network processing """
    shape = X.shape
    X = X.reshape((shape[0], 1, shape[1], shape[2]))

    return X, y


def get_batch_iterator():
    """
    Get batch iterator
    """

    def batch_iterator(batch_size, k_samples, shuffle):
        return BatchIterator(batch_size=batch_size, prepare=prepare, k_samples=1000, shuffle=shuffle)

    return batch_iterator


def build_model(batch_size=BATCH_SIZE):
    """ Compile net architecture """
    nonlin = lasagne.nonlinearities.rectify

    # --- input layers ---
    l_in = lasagne.layers.InputLayer(shape=(batch_size, INPUT_SHAPE[0], INPUT_SHAPE[1], INPUT_SHAPE[2]), name='Input')

    # --- conv layers ---
    net = Conv2DLayer(l_in, num_filters=32, filter_size=5, stride=2, pad=2, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = Conv2DLayer(net, num_filters=32, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = MaxPool2DLayer(net, pool_size=2)
    net = DropoutLayer(net, p=0.0)

    net = Conv2DLayer(net, num_filters=64, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = Conv2DLayer(net, num_filters=64, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = MaxPool2DLayer(net, pool_size=2)
    net = DropoutLayer(net, p=0.0)

    net = Conv2DLayer(net, num_filters=256, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = Conv2DLayer(net, num_filters=256, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = Conv2DLayer(net, num_filters=256, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = Conv2DLayer(net, num_filters=256, filter_size=3, stride=1, pad=1, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = MaxPool2DLayer(net, pool_size=2)
    net = DropoutLayer(net, p=0.3)

    net = Conv2DLayer(net, num_filters=512, filter_size=3, pad=0, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = DropoutLayer(net, p=0.0)
    net = Conv2DLayer(net, num_filters=512, filter_size=1, pad=0, W=init_conv(), nonlinearity=nonlin)
    net = batch_norm(net)
    net = DropoutLayer(net, p=0.0)

    # --- feed forward part ---
    net = Conv2DLayer(net, num_filters=156, filter_size=1, W=init_conv(), nonlinearity=lasagne.nonlinearities.identity)
    net = batch_norm(net, name='l1')
    net = GlobalPoolLayer(net)
    net = FlattenLayer(net, name='l0')
    net = NonlinearityLayer(net, nonlinearity=lasagne.nonlinearities.sigmoid)

    return net

train_strategy = TrainingStrategy(
    batch_size=BATCH_SIZE,
    ini_learning_rate=INI_LEARNING_RATE,
    max_epochs=MAX_EPOCHS,
    patience=PATIENCE,
    L2=L2,
    samples_per_epoch=1000,
    y_tensor_type=T.matrix,
    objective=mean_pixel_binary_crossentropy,
    adapt_learn_rate=get_constant(),
    update_function=get_update_adam(),
    valid_batch_iter=get_batch_iterator(),
    train_batch_iter=get_batch_iterator()
)
