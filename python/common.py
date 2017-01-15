import subprocess
import glob
import re
import pandas
import os


def get_version(command, version_flag='--version', 
                cmd_prefix='',
                lines=None,
                regular_expression=None):
    """
    Gets the version string from a command

    cmd_prefix is useful if you need an interpreter (bash, python, etc)
    
    lines can be a line number (int), a slice object, or an iterable indicating which lines of the output to grab

    if regular_expression given, the first captured group is returned.
    """
    command = " ".join([cmd_prefix,
                        command,
                        version_flag,
                        "; exit 0"])
    out = subprocess.check_output(command,
                                  stderr=subprocess.STDOUT,
                                  shell=True).decode()

    # select specific lines
    if lines is not None:
        out_lines = out.split("\n")
        if isinstance(lines,slice):
            out = "\n".join(out_lines[lines])
        elif isinstance(lines, int):
            out = out_lines[lines]
        else:
            out = "\n".join(out_lines[i] for i in lines)

    # apply regular expression if given
    if regular_expression is None:
        return out.strip()
    else:
        if isinstance(regular_expression, str):
            regular_expression = re.compile(regular_expression)
        try:
            return regular_expression.search(out).group(1)
        except AttributeError:
            print("WARNING: Expression {} did not matach a group in output from `{}`: {}".format(regular_expression.pattern, command, out))



def parse_stats(stats_file):
    """
    pull out the read and base counts from a prinseq output file.
    Returns a two item dict with integer values and keys: 'reads', 'bases'
    """

    # if the file is empty, so was the fasta/fastq file
    if os.stat(stats_file).st_size==0:
        return {'reads':0,'bases':0}

    stats = pandas.read_table(stats_file,names=('module','key','value'),index_col=1)['value']
    return {k:int(stats[k]) for k in ['reads','bases']}


def collect_sample_reads(config):
    """
    If there is not already a "reads" dict in config, build it from the samples
    pattern
    """
    if 'reads' not in config:
        try:
            samples_pattern_data = config['samples_pattern']
        except:
            raise Exception("Please supply list of samples or patterns to find"
                            "them with") 
        reads = config.setdefault('reads',{})
        sample_pattern = samples_pattern_data.get('re', r'/([^/]+)/[^/]+$')
        sample_RE = re.compile(sample_pattern)
        #print(sample_RE.pattern)
        read_file_glob = samples_pattern_data.get('glob', './*/reads.cleaned.fastq.gz')
        read_files = glob.glob(read_file_glob)
        if len(read_files)==0:
            raise Exception("The sample reads wildcard '{}' did not match any files!"\
                                .format(read_file_glob))
        for read_file in read_files:
            #print(read_file)
            m = sample_RE.search(read_file)
            if m is None:
                raise Exception("The sample matching expression ({}) failed to find a sample name in the path: {}".format(sample_pattern, read_file))
            sample = m.group(1)
            # sanitize sample name
            sample = re.sub(r'[^A-Za-z0-9_]','_',sample)
            #print(sample)
            reads[sample]=read_file
#
