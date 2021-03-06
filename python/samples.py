"""
METHODS for setting up workflows with multiple samples

    collect_sample_reads: find read fastq files using glob/re
"""
import re
import glob

def process_sample_data(sample_data):
    """
    sample_data is a top level config map that has two types of entries

     - samples: keyed on sample name and containing paths and other data
     - 'reads_patterns': list of patterns to find samples. These are passed to 
            collect_sample_reads() below

    This method processes the read patterns to find samples

    AND

    returns a list of sample names
    """

    # First, process the patterns
    if 'reads_patterns' in sample_data:
        if isinstance(sample_data['reads_patterns'], dict):
            reads_patterns = [sample_data['reads_patterns']]
        else:
            reads_patterns = sample_data['reads_patterns']
        for pattern_data in reads_patterns:
            if pattern_data.get('cleaned', True) in [True, 'True']:
                read_key = 'clean'
            else:
                read_key = 'raw'
            for sample, reads in collect_sample_reads(pattern_data).items():
                sample_data.setdefault(sample, {})[read_key] = reads

        # Now get rid of any patterns from config
        del sample_data['reads_patterns']

    # return sample names
    return [s for s in sample_data if s != 'reads_patterns']


def collect_sample_reads(samples_pattern_data):
    """
    Use the samples_pattern entry in config to locate read files and group into
    samples

    The samples_pattern dict should look like this:
        samples_pattern:
            glob: "../data/*.fastq"
            re: "/([^_]+)_[^/]+\\.fastq"

    The glob finds files using a
    filesystem wildcard and the re should identify (as the first matched group)
    the sample name in the found file names.

    Returns dict mapping from sample names to read files.

    In the above example, let the generated reads dict could look like:
    reads:
        sample-01: reads/sample-01/reads.corrected.bfc.fastq.gz
        sample-02: reads/sample-02/reads.corrected.bfc.fastq.gz

    or this (depending on filesystem contents):
    reads:
        sample-01:
            - reads/sample-01/reads.R1.fastq
            - reads/sample-01/reads.R2.fastq
        sample-02:
            - reads/sample-02/reads.R1.fastq
            - reads/sample-02/reads.R2.fastq

    """

    # setup
    reads = {}
    sample_pattern = samples_pattern_data.get('re', r'/([^/]+)/[^/]+$')
    sample_RE = re.compile(sample_pattern)
    read_file_glob = samples_pattern_data.get('glob',
                                              './*/reads.cleaned.fastq.gz')

    # find files
    read_files = glob.glob(read_file_glob)
    if len(read_files) == 0:
        raise Exception(
            "The sample reads wildcard '{}' did not match any files!"\
                            .format(read_file_glob)
        )

    # collect files into lists by sample
    for read_file in read_files:
        match = sample_RE.search(read_file)
        if match is None:
            raise Exception(
                ("The sample matching expression ({}) failed to find a sample "
                 "name in the path: {}").format(sample_pattern, read_file)
            )
        sample = match.group(1)
        # sanitize sample name
        sample = re.sub(r'[^A-Za-z0-9_]', '_', sample)
        reads.setdefault(sample, []).append(read_file)

    return reads
