// Declare syntax version
nextflow.enable.dsl=2

process BWA_MEM {

    container = "${projectDir}/../singularity-images/depot.galaxyproject.org-singularity-bwa-0.7.8--he4a0461_9.img"

    input:
    path  reads
    path  index

    output:
    path("*.sam")

    script:
    """
    INDEX=`find -L ./ -name "*.amb" | sed 's/.amb//'`

    bwa mem \\
        -t ${params.threads_num} \\
        \$INDEX \\
        $reads > ${params.prefix}.sam
    cp ${params.prefix}.sam ${launchDir}/${params.outdir}/
    """
}

workflow{
    reads     = Channel.of(params.fastq_1,params.fastq_2).collect()
    bwa_index = Channel.fromPath(params.bwa_index).collect()
    BWA_MEM(reads, bwa_index)
}

