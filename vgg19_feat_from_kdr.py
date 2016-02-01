"""Perform forward pass through network and save extracted features

code is partially inspired by o_O team, see their github repo at
https://github.com/sveitser/kaggle_diabetic

Christian Leibig, 2015

"""
from __future__ import division, print_function
import time

import click
import numpy as np


@click.command()
@click.option('--source', help="Either a *.npy array (assumed to have "
                               "standard normal colour channels) or a "
                               "directory with "
                               "images (standard normalization of colour "
                               "channels is applied).")
@click.option('--filename_targets', default=None, show_default=True,
              help="Absolute filename of labels .csv file")
@click.option('--batch_size', default=2, show_default=True,
              help="Number of samples to be passed through the network at "
                   "once.")
@click.option('--outfile', default='feature_activations.npy',
              show_default=True,
              help="Filename for saving the extracted features.")
@click.option('--last_layer', default='fc7', show_default=True,
              help="Layer up to which features shall be computed.")
def main(source, filename_targets, batch_size, outfile, last_layer):
    """Perform forward pass through network and save extracted features"""
    import theano
    import theano.tensor as T
    import lasagne

    import models
    from datasets import KaggleDR

    input_var = T.tensor4('inputs')
    network = models.vgg19(batch_size=batch_size, input_var=input_var,
                           filename='vgg19.pkl')
    output_layer = network[last_layer]

    feature_activations = lasagne.layers.get_output(output_layer)
    forward_pass = theano.function([input_var], feature_activations)

    if source.endswith('.npy'):
        kdr = KaggleDR(filename_targets=filename_targets)
        idx = np.arange(kdr.n_samples)
        # Assign member variable of kdr with indices and data
        kdr.indices_in_X = idx
        n_channels, n_rows, n_columns = network['input'].shape[1:]
        kdr.X = np.memmap(source, dtype=theano.config.floatX, mode='r',
                          shape=(kdr.n_samples, n_channels, n_rows, n_columns))
    else:
        kdr = KaggleDR(path_data=source, filename_targets=filename_targets)
        idx = np.arange(kdr.n_samples)
        # No assignment of kdr.X and kdr.indices_in_X results in loading images
        # from disk

    outputs = np.empty((kdr.n_samples, output_layer.num_units))
    i = 0
    n_batches = np.ceil(kdr.n_samples/batch_size)
    print("Computing features of", kdr.n_samples, "sample(s)...")
    start_time = time.time()
    for batch in kdr.iterate_minibatches(idx, batch_size):
            print("Working on batch {}/{}".format(i, n_batches))
            inputs, _ = batch
            outputs[i*batch_size:min((i+1)*batch_size, kdr.n_samples)] = \
                forward_pass(inputs)
            i += 1

    if source.endswith('.npy'):
        del kdr.X  # close memory mapped array

    print("Forward pass of", kdr.n_samples, "took",
          np.round((time.time() - start_time), 3), "sec.")
    print("Writing features to disk...")
    np.save(outfile, outputs)
    print("Done.")


if __name__ == '__main__':
    main()