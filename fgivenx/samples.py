import numpy
import tqdm
from fgivenx.parallel import openmp_apply, mpi_apply


def trim_samples(samples, weights, ntrim=0):
    """ Make samples equally weighted, and trim if desired.

    Parameters
    ----------
    samples: numpy.array
        See argument of fgivenx.compute_contours for more detail.

    weights: numpy.array
        See argument of fgivenx.compute_contours for more detail.

    Keywords
    --------
    ntrim: int
        Number of samples to trim to. If <=0 do nothing.
    """

    n = len(weights)
    weights /= weights.max()
    choices = numpy.random.rand(n) < weights

    new_samples = samples[choices]

    if ntrim > 0:
        new_samples = numpy.random.choice(new_samples)

    return new_samples


def compute_samples(f, x, samples, **kwargs):
    """ Apply f(x,theta) to x array and theta in samples.

    Parameters
    ----------
    See arguments of fgivenx.compute_contours

    Keywords
    --------
    parallel: str
        See arguments of fgivenx.compute_contours

    Returns
    -------
    An array of samples at each x. shape=(len(x),len(samples),)
    """

    parallel = kwargs.pop('parallel', '')
    nprocs = kwargs.pop('nprocs', None)
    comm = kwargs.pop('comm', None)

    if parallel is 'openmp':
        array = openmp_apply(f, samples, precurry=(x,), nprocs=nprocs)
    elif parallel is 'mpi':
        array = mpi_apply(lambda theta: f(x, theta), samples, comm=comm)
    elif parallel is '':
        array = [f(x, theta) for theta in tqdm.tqdm(samples)]
    else:
        raise ValueError("keyword parallel=%s not recognised,"
                         "options are 'openmp' or 'mpi'" % parallel)

    return numpy.array(array).transpose()


def samples_from_getdist_chains(file_root, params):
    """ Extract samples and weights from getdist chains.

    Parameters
    ----------
    file_root: str
        Root name for getdist chains files. This script requires
        - file_root.txt
        - file_root.paramnames

    params: list(str)
        Names of parameters to be supplied to second argument of f(x|theta).

    Returns
    -------
    samples: numpy.array
        2D Array of samples. samples.shape=(# of samples, len(params),)

    weights: numpy.array
        Array of weights. samples.shape = (len(params),)
    """

    # Get the full data
    data = numpy.loadtxt(file_root + '.txt')
    weights = data[:, 0]

    # Get the paramnames
    paramnames = numpy.loadtxt(file_root + '.paramnames', dtype=str)
    if len(paramnames.shape) is 2:
        paramnames = paramnames[:, 0]

    # Get the relevant samples
    indices = [2+list(paramnames).index(p) for p in params]
    samples = data[:, indices]

    return samples, weights