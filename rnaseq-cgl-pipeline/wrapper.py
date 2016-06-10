import argparse
import os
import shutil
import subprocess
import json
import logging
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


def call_pipeline(mount, args):
    work_dir = os.path.join(mount, 'Toil-RNAseq-' + str(uuid4()))
    os.makedirs(work_dir)
    log.info('Temporary directory created: {}'.format(work_dir))
    config_path = os.path.join(work_dir, 'toil-rnaseq.config')
    job_store = os.path.join(args.resume, 'jobStore') if args.resume else os.path.join(work_dir, 'jobStore')
    with open(config_path, 'w') as f:
        f.write(generate_config(args.star, args.rsem, args.kallisto, mount))
    command = ['toil-rnaseq', 'run',
               job_store,
               '--config', config_path,
               '--workDir', work_dir,
               '--retryCount', '1']
    if args.resume:
        command.append('--restart')
    if args.cores:
        command.append('--maxCores={}'.format(args.cores))
    command.append('--samples')
    command.extend('file://' + x for x in args.samples)
    try:
        subprocess.check_call(command)
    finally:
        stat = os.stat(mount)
        subprocess.check_call(['chown', '-R', '{}:{}'.format(stat.st_uid, stat.st_gid), mount])
        shutil.rmtree(os.path.join(mount, uuid))
def generate_config(star_path, rsem_path, kallisto_path, output_dir):
    return textwrap.dedent("""
        star-index: file://{0}
        rsem-ref: file://{1}
        kallisto-index: file://{2}
        output-dir: {3}
        s3-dir:
        cutadapt: true
        ssec:
        gtkey:
        wiggle:
        save-bam:
        fwd-3pr-adapter: AGATCGGAAGAG
        rev-3pr-adapter: AGATCGGAAGAG
        ci-test:
    """[1:].format(star_path, rsem_path, kallisto_path, output_dir))


def main():
    """
    Computational Genomics Lab, Genomics Institute, UC Santa Cruz
    Dockerized Toil RNA-seq pipeline

    RNA-seq fastqs are combined, aligned, and quantified with 2 different methods (RSEM and Kallisto)

    General Usage:
    docker run -v $(pwd):$(pwd) -v /var/run/docker.sock:/var/run/docker.sock \
    quay.io/ucsc_cgl/rnaseq-cgl-pipeline --samples sample1.tar

    Please see the complete documentation located at:
    https://github.com/BD2KGenomics/cgl-docker-lib/tree/master/rnaseq-cgl-pipeline
    or inside the container at: /opt/rnaseq-pipeline/README.md


    Structure of RNA-Seq Pipeline (per sample)

                  3 -- 4 -- 5
                 /          |
      0 -- 1 -- 2 ---- 6 -- 8
                 \          |
                  7 ---------

    0 = Download sample
    1 = Unpack/Merge fastqs
    2 = CutAdapt (adapter trimming)
    3 = STAR Alignment
    4 = RSEM Quantification
    5 = RSEM Post-processing
    6 = Kallisto
    7 = FastQC
    8 = Consoliate output and upload to S3
    =======================================
    Dependencies
    Docker: 1.9.1
    """
    # Define argument parser for
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--star', type=str, required=True,
                        help='Absolute path to STAR index tarball.')
    parser.add_argument('--rsem', type=str, required=True,
                        help='Absolute path to rsem reference tarball.')
    parser.add_argument('--kallisto', type=str, required=True,
                        help='Absolute path to kallisto index (.idx) file.')
    parser.add_argument('--samples', nargs='+', required=True,
                        help='Absolute path(s) to sample tarballs.')
    parser.add_argument('--restart', action='store_true', default=False,
                        help='Add this flag to restart the pipeline. Requires existing job store.')
    parser.add_argument('--cores', type=int, default=None,
                        help='Will set a cap on number of cores to use, default is all available cores.')
    args = parser.parse_args()
    # Get name of most recent running container (should be this one)
    name = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}']).split('\n')[0]
    # Get name of mounted volume
    blob = json.loads(subprocess.check_output(['docker', 'inspect', name]))
    mounts = blob[0]['Mounts']
    # Ensure docker.sock is mounted correctly
    sock_mount = [x['Source'] == x['Destination'] for x in mounts if 'docker.sock' in x['Source']]
    if len(sock_mount) != 1:
        raise IllegalArgumentException('Missing socket mount. Requires the following:'
                                       'docker run -v /var/run/docker.sock:/var/run/docker.sock')
    # Ensure formatting of command for 2 mount points
    if len(mounts) == 2:
        if not all(x['Source'] == x['Destination'] for x in mounts):
            raise IllegalArgumentException('Docker Src/Dst mount points, invoked with the -v argument,'
                                           'must be the same if only using one mount point aside from the '
                                           'docker socket.')
        work_mount = [x['Source'] for x in mounts if 'docker.sock' not in x['Source']]
    else:
        # Ensure only one mirror mount exists aside from docker.sock
        mirror_mounts = [x['Source'] for x in mounts if x['Source'] == x['Destination']]
        work_mount = [x for x in mirror_mounts if 'docker.sock' not in x]
        if len(work_mount) > 1:
            raise IllegalArgumentException('Too many mirror mount points provided, see documentation.')
        if len(work_mount) == 0:
            raise IllegalArgumentException('No required mirror mount point provided, see documentation.')
    # Enforce file input standards
    if not all(x.startswith('/') for x in args.samples):
        raise IllegalArgumentException("Sample inputs must point to a file's full path, e.g. "
                                       "'/full/path/to/sample1.tar'. You provided {}.".format(args.samples))
    if not all(x.startswith('/') for x in [args.star, args.kallisto, args.rsem]):
        raise IllegalArgumentException("Sample inputs must point to a file's full path, e.g. "
                                       "'/full/path/to/sample1.tar'. You  provided {}.".format(args.samples))
    call_pipeline(work_mount[0], args)


class IllegalArgumentException(Exception):
    pass


if __name__ == '__main__':
    main()
