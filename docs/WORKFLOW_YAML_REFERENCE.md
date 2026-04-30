# Cloudgene Workflow YAML Reference

This document provides a comprehensive guide for creating and configuring workflow definitions in Cloudgene using YAML format.

## Table of Contents

1. [Workflow Structure Overview](#workflow-structure-overview)
2. [Basic Workflow Definition](#basic-workflow-definition)
3. [Workflow Metadata](#workflow-metadata)
4. [Input Parameters](#input-parameters)
5. [Output Parameters](#output-parameters)
6. [Workflow Steps](#workflow-steps)
7. [Access Control](#access-control)
8. [Advanced Configuration](#advanced-configuration)
9. [Parameter Types Reference](#parameter-types-reference)
10. [Validation Rules](#validation-rules)
11. [Best Practices](#best-practices)
12. [Example Workflows](#example-workflows)
13. [Migration from Cloudgene 1.x](#migration-from-cloudgene-1x)
14. [Troubleshooting](#troubleshooting)

---

## Workflow Structure Overview

A Cloudgene workflow is defined in YAML format and consists of several key sections:

```yaml
# Workflow metadata
id: workflow-identifier
name: Display Name
description: Workflow description
version: 1.0.0
website: https://example.com
category: bioinformatics

# Access control
public: false
groups:
  - bioinformatics
  - genomics

# Workflow definition
workflow:
  steps:
    - name: StepName
      classname: path.to.StepClass
  
  inputs:
    - id: input_param
      type: text
      description: Parameter description
  
  outputs:
    - id: output_file
      type: file
      description: Output file description
```

---

## Basic Workflow Definition

### Minimal Workflow

The simplest workflow requires only essential metadata and step definitions:

```yaml
id: hello-world
name: Hello World
description: A simple hello world workflow
version: 1.0.0

workflow:
  steps:
    - name: HelloStep
      classname: workflows.steps.HelloWorldStep
  
  inputs:
    - id: message
      type: text
      description: Message to display
      value: "Hello World"
  
  outputs:
    - id: result
      type: text
      description: Result message
```

### Complete Basic Example

```yaml
id: basic-analysis
name: Basic Data Analysis
description: Performs basic statistical analysis on input data
version: 1.2.0
website: https://example.com/docs/basic-analysis
category: statistics

workflow:
  steps:
    - name: DataLoader
      classname: workflows.steps.DataLoaderStep
    - name: StatAnalysis
      classname: workflows.steps.StatisticalAnalysisStep
    - name: ReportGenerator  
      classname: workflows.steps.ReportGeneratorStep
  
  inputs:
    - id: input_file
      type: file
      description: Input data file (CSV format)
      required: true
    
    - id: analysis_type
      type: list
      description: Type of analysis to perform
      value: "descriptive"
      values:
        descriptive: "Descriptive Statistics"
        correlation: "Correlation Analysis"
        regression: "Regression Analysis"
  
  outputs:
    - id: report
      type: file
      description: Analysis report (HTML)
      download: true
    
    - id: summary
      type: file
      description: Summary statistics (CSV)
      download: true
```

---

## Workflow Metadata

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique workflow identifier (alphanumeric, hyphens allowed) | `quality-control-v2` |
| `name` | string | Human-readable workflow name | `Quality Control Pipeline` |
| `workflow` | object | Workflow definition containing steps, inputs, outputs | See sections below |

### Optional Metadata Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `description` | string | Detailed workflow description | `Performs comprehensive QC...` |
| `version` | string | Workflow version (semantic versioning recommended) | `1.2.0` |
| `website` | string | URL for documentation or project page | `https://github.com/user/workflow` |
| `category` | string | Workflow category for organization | `bioinformatics` |
| `author` | string | Workflow author(s) | `John Doe <john@example.com>` |
| `citation` | string | Publication citation | `Doe et al. Nature 2024` |
| `license` | string | Software license | `MIT` |
| `tags` | array | Keywords for searchability | `[qc, fastq, genomics]` |

### Extended Metadata Example

```yaml
id: rnaseq-pipeline
name: RNA-Seq Analysis Pipeline
description: |
  Comprehensive RNA-Seq analysis pipeline including quality control,
  alignment, quantification, and differential expression analysis.
  
  Features:
  - FastQ quality control with FastQC
  - Adapter trimming with Trimmomatic
  - Alignment with STAR or HISAT2
  - Quantification with featureCounts
  - Differential expression with DESeq2

version: 2.1.0
website: https://github.com/lab/rnaseq-pipeline
category: bioinformatics
author: Jane Smith <jane.smith@university.edu>
citation: "Smith et al. RNA-Seq Pipeline. Bioinformatics 2024"
license: GPL-3.0
tags:
  - rna-seq
  - differential-expression
  - genomics
  - transcriptomics

created: 2024-01-15
updated: 2024-03-20
```

---

## Input Parameters

Input parameters define the data and options users can provide to the workflow.

### Basic Input Syntax

```yaml
workflow:
  inputs:
    - id: parameter_name          # Unique parameter identifier
      type: text                  # Parameter type
      description: Description    # User-friendly description
      required: true             # Whether parameter is required
      value: default_value       # Default value (optional)
```

### Parameter Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique parameter identifier (alphanumeric, underscores) |
| `type` | string | Yes | Parameter type (see types reference) |
| `description` | string | Yes | User-friendly description |
| `required` | boolean | No | Whether parameter is required (default: true) |
| `value` | various | No | Default value |
| `values` | object | No | Options for list/checkbox types |
| `visible` | boolean | No | Whether to show in UI (default: true) |
| `admin` | boolean | No | Admin-only parameter (default: false) |

### Text Input

```yaml
inputs:
  - id: sample_name
    type: text
    description: Sample identifier
    required: true
    value: "sample_001"
  
  - id: optional_prefix
    type: text
    description: Optional filename prefix
    required: false
    value: ""
```

### Number Input

```yaml
inputs:
  - id: threads
    type: number
    description: Number of CPU threads to use
    value: 4
    min: 1
    max: 32
  
  - id: quality_threshold
    type: number
    description: Quality score threshold
    value: 30.0
    min: 0.0
    max: 50.0
    step: 0.1
```

### File Input

```yaml
inputs:
  - id: input_fastq
    type: file
    description: Input FASTQ file
    required: true
    accept: ".fastq,.fastq.gz,.fq,.fq.gz"
  
  - id: reference_genome
    type: file
    description: Reference genome (FASTA)
    required: true
    accept: ".fa,.fasta,.fa.gz,.fasta.gz"
```

### Folder Input

```yaml
inputs:
  - id: input_directory
    type: folder
    description: Directory containing input files
    required: true
  
  - id: output_directory
    type: folder
    description: Output directory (optional)
    required: false
```

### Checkbox Input

```yaml
inputs:
  - id: enable_trimming
    type: checkbox
    description: Enable adapter trimming
    value: true
    values:
      true: "Enable trimming"
      false: "Skip trimming"
  
  - id: generate_plots
    type: checkbox
    description: Generate quality control plots
    value: false
```

### List/Dropdown Input

```yaml
inputs:
  - id: aligner
    type: list
    description: Alignment algorithm
    value: "star"
    values:
      star: "STAR (spliced aligner)"
      hisat2: "HISAT2 (hierarchical indexing)"
      bwa: "BWA (Burrows-Wheeler)"
  
  - id: organism
    type: list
    description: Reference organism
    value: "human"
    values:
      human: "Homo sapiens (hg38)"
      mouse: "Mus musculus (mm10)"
      fly: "Drosophila melanogaster (dm6)"
      yeast: "Saccharomyces cerevisiae (sacCer3)"
```

### Textarea Input

```yaml
inputs:
  - id: sample_sheet
    type: textarea
    description: Sample sheet (CSV format)
    required: false
    rows: 10
    placeholder: |
      sample_id,condition,batch
      sample1,treated,1
      sample2,control,1
  
  - id: custom_parameters
    type: textarea
    description: Custom command-line parameters
    required: false
    rows: 5
    placeholder: "--param1 value1 --param2 value2"
```

---

## Output Parameters

Output parameters define the files and data produced by the workflow.

### Basic Output Syntax

```yaml
workflow:
  outputs:
    - id: output_name
      type: file
      description: Output description
      download: true
```

### Output Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | Yes | Unique output identifier |
| `type` | string | Yes | Output type (file, folder, text) |
| `description` | string | Yes | User-friendly description |
| `download` | boolean | No | Whether file can be downloaded (default: true) |
| `temp` | boolean | No | Temporary file (auto-cleanup) (default: false) |
| `zip` | boolean | No | Compress before download (default: false) |

### File Outputs

```yaml
outputs:
  - id: aligned_reads
    type: file
    description: Aligned reads (BAM format)
    download: true
  
  - id: quality_report
    type: file
    description: Quality control report (HTML)
    download: true
  
  - id: log_file
    type: file
    description: Pipeline execution log
    download: false
    temp: true
```

### Folder Outputs

```yaml
outputs:
  - id: results_directory
    type: folder
    description: Complete analysis results
    download: true
    zip: true
  
  - id: intermediate_files
    type: folder
    description: Intermediate processing files
    download: false
    temp: true
```

### Text Outputs

```yaml
outputs:
  - id: summary_stats
    type: text
    description: Analysis summary statistics
    download: false
  
  - id: job_status
    type: text
    description: Job completion status
    download: false
```

---

## Workflow Steps

Steps define the computational tasks that make up the workflow.

### Step Definition

```yaml
workflow:
  steps:
    - name: StepName
      classname: python.module.path.StepClass
      params:
        param1: value1
        param2: ${input_parameter}
```

### Step Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Human-readable step name |
| `classname` | string | Yes | Python class implementing the step |
| `params` | object | No | Step-specific parameters |

### Parameter Substitution

Use `${parameter_id}` syntax to reference input parameters:

```yaml
steps:
  - name: QualityControl
    classname: workflows.steps.FastQCStep
    params:
      input_file: ${input_fastq}
      threads: ${cpu_threads}
      output_dir: ${output_directory}
  
  - name: Trimming
    classname: workflows.steps.TrimmomaticStep
    params:
      input_file: ${input_fastq}
      output_file: ${trimmed_fastq}
      adapter_file: ${adapter_sequences}
      min_length: ${min_read_length}
```

### Conditional Steps

Steps can be conditionally executed based on parameter values:

```yaml
steps:
  - name: AdapterTrimming
    classname: workflows.steps.TrimmomaticStep
    condition: ${enable_trimming}
    params:
      input_file: ${input_fastq}
      output_file: ${trimmed_fastq}
  
  - name: QualityFiltering
    classname: workflows.steps.QualityFilterStep
    condition: ${quality_threshold} > 20
    params:
      input_file: ${input_fastq}
      threshold: ${quality_threshold}
```

### Step Dependencies

Define execution order and dependencies:

```yaml
steps:
  - name: QualityControl
    classname: workflows.steps.FastQCStep
    depends_on: []
  
  - name: Trimming
    classname: workflows.steps.TrimmomaticStep
    depends_on: [QualityControl]
  
  - name: Alignment
    classname: workflows.steps.STARStep
    depends_on: [Trimming]
  
  - name: Quantification
    classname: workflows.steps.FeatureCountsStep
    depends_on: [Alignment]
```

---

## Access Control

Control who can access and execute workflows.

### Public vs Private Workflows

```yaml
# Public workflow (accessible to all authenticated users)
id: public-analysis
name: Public Analysis Tool
public: true

# Private workflow (group-restricted)
id: restricted-analysis
name: Restricted Analysis Tool
public: false
groups:
  - bioinformatics
  - lab_members
```

### Group-Based Access

```yaml
# Multiple groups allowed
id: multi-group-workflow
name: Multi-Group Workflow
public: false
groups:
  - bioinformatics
  - genomics
  - proteomics

# Single group
id: admin-workflow
name: Admin-Only Workflow
public: false
groups:
  - admin
```

### Admin-Only Parameters

Hide sensitive parameters from regular users:

```yaml
inputs:
  - id: regular_param
    type: text
    description: Regular parameter visible to all users
  
  - id: admin_param
    type: text
    description: Admin-only parameter
    admin: true
    value: "admin_default"
  
  - id: database_password
    type: text
    description: Database password
    admin: true
    visible: false  # Hide completely from UI
```

---

## Advanced Configuration

### Environment Variables

Set environment variables for workflow execution:

```yaml
workflow:
  environment:
    PATH: "/opt/tools/bin:$PATH"
    JAVA_OPTS: "-Xmx8g"
    TMPDIR: "/scratch/tmp"
    
  steps:
    - name: ToolExecution
      classname: workflows.steps.CustomToolStep
      environment:
        TOOL_CONFIG: "/etc/tool.conf"
        TOOL_THREADS: ${cpu_threads}
```

### Resource Requirements

Specify computational resource requirements:

```yaml
workflow:
  resources:
    min_memory: "8GB"
    min_cpus: 2
    max_memory: "64GB"
    max_cpus: 16
    max_time: "24:00:00"
    
  steps:
    - name: MemoryIntensiveStep
      classname: workflows.steps.BigDataStep
      resources:
        memory: "32GB"
        cpus: 8
        time: "12:00:00"
```

### Custom Validation

Add custom validation rules:

```yaml
workflow:
  validation:
    - rule: "${cpu_threads} <= 32"
      message: "CPU threads cannot exceed 32"
    
    - rule: "${memory_size} >= 4"
      message: "Minimum memory requirement is 4GB"
    
    - rule: "file_exists(${reference_genome})"
      message: "Reference genome file must exist"
  
  inputs:
    - id: cpu_threads
      type: number
      value: 4
      validation:
        min: 1
        max: 32
    
    - id: email
      type: text
      description: Notification email
      validation:
        pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.[\\w]+$"
        message: "Please enter a valid email address"
```

### Workflow Hooks

Execute custom code at specific workflow stages:

```yaml
workflow:
  hooks:
    pre_execution:
      - classname: workflows.hooks.SetupEnvironment
      - classname: workflows.hooks.ValidateInputs
    
    post_execution:
      - classname: workflows.hooks.CleanupFiles
      - classname: workflows.hooks.SendNotification
    
    on_error:
      - classname: workflows.hooks.ErrorHandler
      - classname: workflows.hooks.NotifyAdmin
```

---

## Parameter Types Reference

### Complete Type Reference

| Type | Description | Properties | Example Value |
|------|-------------|------------|---------------|
| `text` | Single-line text input | `value`, `placeholder`, `pattern` | `"sample_001"` |
| `textarea` | Multi-line text input | `value`, `rows`, `cols`, `placeholder` | `"line1\\nline2"` |
| `number` | Numeric input | `value`, `min`, `max`, `step` | `42`, `3.14` |
| `file` | File upload | `accept`, `max_size` | User uploads file |
| `folder` | Folder selection | `path` | User selects folder |
| `checkbox` | Boolean checkbox | `value`, `values` | `true`, `false` |
| `list` | Dropdown selection | `value`, `values` | `"option1"` |
| `radio` | Radio button group | `value`, `values` | `"choice_a"` |
| `date` | Date picker | `value`, `min_date`, `max_date` | `"2024-01-01"` |
| `time` | Time picker | `value`, `min_time`, `max_time` | `"14:30"` |
| `email` | Email input | `value`, `validation` | `"user@example.com"` |
| `url` | URL input | `value`, `validation` | `"https://example.com"` |
| `color` | Color picker | `value` | `"#FF0000"` |
| `range` | Range slider | `value`, `min`, `max`, `step` | `50` |

### Advanced Type Examples

**File with Validation**:
```yaml
inputs:
  - id: genome_file
    type: file
    description: Reference genome (FASTA format)
    required: true
    accept: ".fa,.fasta,.fa.gz,.fasta.gz"
    max_size: "10GB"
    validation:
      file_extension: [".fa", ".fasta", ".fa.gz", ".fasta.gz"]
      min_size: "1MB"
      max_size: "10GB"
```

**Number with Range**:
```yaml
inputs:
  - id: quality_score
    type: number
    description: Minimum quality score (0-40)
    value: 20
    min: 0
    max: 40
    step: 1
    validation:
      range: [0, 40]
      integer: true
```

**Conditional List**:
```yaml
inputs:
  - id: analysis_type
    type: list
    description: Analysis type
    value: "basic"
    values:
      basic: "Basic Analysis"
      advanced: "Advanced Analysis (requires license)"
    
  - id: license_key
    type: text
    description: License key
    required: true
    visible: "${analysis_type} == 'advanced'"
    validation:
      pattern: "^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
```

**Date Range**:
```yaml
inputs:
  - id: start_date
    type: date
    description: Analysis start date
    value: "2024-01-01"
    min_date: "2020-01-01"
    max_date: "today"
  
  - id: end_date
    type: date
    description: Analysis end date
    value: "today"
    min_date: "${start_date}"
    max_date: "today"
```

---

## Validation Rules

### Built-in Validators

**String Validation**:
```yaml
inputs:
  - id: sample_id
    type: text
    validation:
      min_length: 3
      max_length: 50
      pattern: "^[a-zA-Z0-9_-]+$"
      message: "Sample ID must be 3-50 alphanumeric characters"
```

**Number Validation**:
```yaml
inputs:
  - id: threads
    type: number
    validation:
      min: 1
      max: 32
      integer: true
      message: "Threads must be between 1 and 32"
```

**File Validation**:
```yaml
inputs:
  - id: data_file
    type: file
    validation:
      required: true
      file_extension: [".csv", ".tsv", ".txt"]
      min_size: "1KB"
      max_size: "100MB"
      mime_types: ["text/csv", "text/plain"]
```

**Custom Validation Functions**:
```yaml
inputs:
  - id: gene_list
    type: textarea
    validation:
      custom: "validate_gene_list"
      message: "Invalid gene list format"
  
  - id: file_pair
    type: file
    validation:
      custom: "validate_paired_files"
      depends_on: [file1, file2]
```

### Cross-Parameter Validation

```yaml
workflow:
  validation:
    # Ensure end date is after start date
    - rule: "date(${end_date}) > date(${start_date})"
      message: "End date must be after start date"
    
    # Memory requirement based on file size
    - rule: "file_size(${input_file}) < 1GB or ${memory} >= 16"
      message: "Large files (>1GB) require at least 16GB memory"
    
    # Conditional requirement
    - rule: "${enable_advanced} == false or ${license_key} != ''"
      message: "License key required for advanced features"
```

---

## Best Practices

### Workflow Organization

**1. Use Descriptive IDs and Names**:
```yaml
# Good
id: rnaseq-differential-expression
name: RNA-Seq Differential Expression Analysis

# Avoid
id: analysis1
name: Analysis
```

**2. Provide Comprehensive Documentation**:
```yaml
description: |
  This workflow performs comprehensive RNA-Seq analysis including:
  
  1. Quality control with FastQC
  2. Adapter trimming with Trimmomatic (optional)
  3. Alignment with STAR or HISAT2
  4. Quantification with featureCounts
  5. Differential expression with DESeq2
  
  Input Requirements:
  - FASTQ files (single or paired-end)
  - Reference genome (FASTA)
  - Gene annotation (GTF/GFF)
  
  Output Files:
  - Quality control reports
  - Aligned reads (BAM)
  - Gene expression matrix
  - Differential expression results
```

**3. Use Semantic Versioning**:
```yaml
version: 2.1.0  # Major.Minor.Patch
```

### Parameter Design

**1. Provide Sensible Defaults**:
```yaml
inputs:
  - id: cpu_threads
    type: number
    description: Number of CPU threads
    value: 4              # Good default for most systems
    min: 1
    max: 32
```

**2. Use Clear Descriptions**:
```yaml
inputs:
  - id: quality_threshold
    type: number
    description: |
      Minimum quality score for read filtering (Phred scale).
      Reads with average quality below this threshold will be discarded.
      Recommended: 20 for relaxed filtering, 30 for strict filtering.
    value: 20
```

**3. Group Related Parameters**:
```yaml
inputs:
  # Input files
  - id: input_fastq_r1
    type: file
    description: "Input FASTQ file (Read 1)"
  
  - id: input_fastq_r2
    type: file
    description: "Input FASTQ file (Read 2, for paired-end)"
    required: false
  
  # Quality control parameters
  - id: enable_trimming
    type: checkbox
    description: "Enable adapter trimming"
    value: true
  
  - id: min_read_length
    type: number
    description: "Minimum read length after trimming"
    value: 30
```

### Error Handling

**1. Validate Critical Inputs**:
```yaml
inputs:
  - id: reference_genome
    type: file
    description: Reference genome (FASTA format)
    required: true
    validation:
      file_extension: [".fa", ".fasta", ".fa.gz", ".fasta.gz"]
      min_size: "1MB"
      custom: "validate_fasta_format"
```

**2. Provide Clear Error Messages**:
```yaml
validation:
  - rule: "file_exists(${reference_genome})"
    message: |
      Reference genome file not found. Please ensure the file exists and is accessible.
      Supported formats: FASTA (.fa, .fasta, .fa.gz, .fasta.gz)
```

### Performance Optimization

**1. Set Appropriate Resource Limits**:
```yaml
workflow:
  resources:
    min_memory: "8GB"
    min_cpus: 2
    recommended_memory: "16GB"
    recommended_cpus: 4
    max_time: "24:00:00"
```

**2. Use Temporary Files Appropriately**:
```yaml
outputs:
  - id: final_results
    type: file
    description: Final analysis results
    download: true
  
  - id: intermediate_files
    type: folder
    description: Intermediate processing files
    download: false
    temp: true        # Auto-cleanup
```

---

## Example Workflows

### Simple Quality Control Workflow

```yaml
id: fastq-qc
name: FASTQ Quality Control
description: Basic quality control for FASTQ files using FastQC
version: 1.0.0
category: quality-control

workflow:
  steps:
    - name: QualityControl
      classname: workflows.steps.FastQCStep
  
  inputs:
    - id: input_fastq
      type: file
      description: Input FASTQ file
      required: true
      accept: ".fastq,.fastq.gz,.fq,.fq.gz"
    
    - id: threads
      type: number
      description: Number of CPU threads
      value: 2
      min: 1
      max: 16
  
  outputs:
    - id: qc_report
      type: file
      description: Quality control report (HTML)
      download: true
    
    - id: qc_data
      type: file
      description: Quality control data (ZIP)
      download: true
```

### RNA-Seq Analysis Pipeline

```yaml
id: rnaseq-pipeline-v2
name: RNA-Seq Analysis Pipeline v2
description: |
  Comprehensive RNA-Seq analysis pipeline for differential expression analysis.
  
  Pipeline steps:
  1. Quality control (FastQC)
  2. Adapter trimming (Trimmomatic)
  3. Alignment (STAR)
  4. Quantification (featureCounts)
  5. Differential expression (DESeq2)

version: 2.0.0
website: https://github.com/lab/rnaseq-pipeline
category: rna-seq
author: Lab Bioinformatics Team

workflow:
  steps:
    - name: QualityControl
      classname: workflows.steps.FastQCStep
      params:
        input_files: [${input_fastq_r1}, ${input_fastq_r2}]
        threads: ${threads}
    
    - name: AdapterTrimming
      classname: workflows.steps.TrimmomaticStep
      condition: ${enable_trimming}
      params:
        input_r1: ${input_fastq_r1}
        input_r2: ${input_fastq_r2}
        output_r1: trimmed_R1.fastq.gz
        output_r2: trimmed_R2.fastq.gz
        threads: ${threads}
    
    - name: Alignment
      classname: workflows.steps.STARStep
      params:
        input_r1: "${enable_trimming ? 'trimmed_R1.fastq.gz' : input_fastq_r1}"
        input_r2: "${enable_trimming ? 'trimmed_R2.fastq.gz' : input_fastq_r2}"
        reference_genome: ${reference_genome}
        annotation: ${gene_annotation}
        threads: ${threads}
    
    - name: Quantification
      classname: workflows.steps.FeatureCountsStep
      params:
        input_bam: aligned.bam
        annotation: ${gene_annotation}
        threads: ${threads}
    
    - name: DifferentialExpression
      classname: workflows.steps.DESeq2Step
      condition: ${perform_de_analysis}
      params:
        count_matrix: counts.txt
        sample_sheet: ${sample_sheet}
        contrast: ${de_contrast}

  inputs:
    # Input files
    - id: input_fastq_r1
      type: file
      description: "FASTQ file (Read 1)"
      required: true
      accept: ".fastq,.fastq.gz,.fq,.fq.gz"
    
    - id: input_fastq_r2
      type: file
      description: "FASTQ file (Read 2, for paired-end sequencing)"
      required: false
      accept: ".fastq,.fastq.gz,.fq,.fq.gz"
    
    - id: reference_genome
      type: file
      description: "Reference genome (FASTA format)"
      required: true
      accept: ".fa,.fasta,.fa.gz,.fasta.gz"
    
    - id: gene_annotation
      type: file
      description: "Gene annotation file (GTF/GFF format)"
      required: true
      accept: ".gtf,.gff,.gtf.gz,.gff.gz"
    
    # Analysis parameters
    - id: threads
      type: number
      description: "Number of CPU threads to use"
      value: 4
      min: 1
      max: 32
    
    - id: enable_trimming
      type: checkbox
      description: "Enable adapter trimming with Trimmomatic"
      value: true
    
    - id: perform_de_analysis
      type: checkbox
      description: "Perform differential expression analysis"
      value: false
    
    - id: sample_sheet
      type: textarea
      description: |
        Sample sheet for differential expression (CSV format).
        Required if performing DE analysis.
        
        Format:
        sample_id,condition,batch
        sample1,treated,1
        sample2,control,1
      required: false
      visible: ${perform_de_analysis}
      rows: 8
    
    - id: de_contrast
      type: text
      description: "Differential expression contrast (e.g., treated_vs_control)"
      required: false
      visible: ${perform_de_analysis}
      value: "treated_vs_control"

  outputs:
    - id: qc_reports
      type: folder
      description: "Quality control reports"
      download: true
    
    - id: aligned_reads
      type: file
      description: "Aligned reads (BAM format)"
      download: true
    
    - id: gene_counts
      type: file
      description: "Gene expression counts matrix"
      download: true
    
    - id: de_results
      type: file
      description: "Differential expression results"
      download: true
      condition: ${perform_de_analysis}
    
    - id: analysis_log
      type: file
      description: "Pipeline execution log"
      download: false
      temp: true

  validation:
    - rule: "${perform_de_analysis} == false or ${sample_sheet} != ''"
      message: "Sample sheet is required for differential expression analysis"
    
    - rule: "file_extension(${reference_genome}) in ['.fa', '.fasta', '.fa.gz', '.fasta.gz']"
      message: "Reference genome must be in FASTA format"
```

### Variant Calling Workflow

```yaml
id: variant-calling-gatk
name: GATK Variant Calling Pipeline
description: |
  GATK-based variant calling pipeline following best practices.
  
  Pipeline includes:
  - Read mapping with BWA
  - Duplicate marking with Picard
  - Base quality score recalibration
  - Variant calling with HaplotypeCaller
  - Variant filtering

version: 1.3.0
category: variant-calling
public: false
groups:
  - genomics
  - variant-analysis

workflow:
  resources:
    min_memory: "16GB"
    min_cpus: 4
    recommended_memory: "32GB"
    recommended_cpus: 8
    max_time: "48:00:00"

  steps:
    - name: ReadMapping
      classname: workflows.steps.BWAMemStep
      params:
        reference: ${reference_genome}
        reads_r1: ${input_fastq_r1}
        reads_r2: ${input_fastq_r2}
        threads: ${threads}
    
    - name: MarkDuplicates
      classname: workflows.steps.PicardMarkDuplicatesStep
      params:
        input_bam: mapped.bam
        output_bam: marked.bam
    
    - name: BaseRecalibration
      classname: workflows.steps.GATKBQSRStep
      params:
        input_bam: marked.bam
        reference: ${reference_genome}
        known_sites: ${dbsnp_vcf}
    
    - name: VariantCalling
      classname: workflows.steps.GATKHaplotypeCallerStep
      params:
        input_bam: recalibrated.bam
        reference: ${reference_genome}
        intervals: ${target_intervals}
        threads: ${threads}
    
    - name: VariantFiltering
      classname: workflows.steps.GATKVariantFilterStep
      params:
        input_vcf: raw_variants.vcf
        reference: ${reference_genome}
        filters: ${variant_filters}

  inputs:
    # Required inputs
    - id: input_fastq_r1
      type: file
      description: "Input FASTQ file (Read 1)"
      required: true
      accept: ".fastq,.fastq.gz,.fq,.fq.gz"
    
    - id: input_fastq_r2
      type: file
      description: "Input FASTQ file (Read 2)"
      required: true
      accept: ".fastq,.fastq.gz,.fq,.fq.gz"
    
    - id: reference_genome
      type: file
      description: "Reference genome with BWA index"
      required: true
      accept: ".fa,.fasta,.fa.gz,.fasta.gz"
    
    - id: dbsnp_vcf
      type: file
      description: "dbSNP VCF file for base recalibration"
      required: true
      accept: ".vcf,.vcf.gz"
    
    # Optional inputs
    - id: target_intervals
      type: file
      description: "Target intervals (BED format, optional)"
      required: false
      accept: ".bed,.bed.gz"
    
    - id: sample_name
      type: text
      description: "Sample identifier"
      required: true
      value: "sample001"
      validation:
        pattern: "^[a-zA-Z0-9_-]+$"
        min_length: 3
        max_length: 50
    
    # Pipeline parameters
    - id: threads
      type: number
      description: "Number of CPU threads"
      value: 8
      min: 1
      max: 32
    
    - id: variant_filters
      type: list
      description: "Variant filtering stringency"
      value: "standard"
      values:
        lenient: "Lenient filtering (more variants)"
        standard: "Standard GATK filtering"
        strict: "Strict filtering (high confidence)"

  outputs:
    - id: final_vcf
      type: file
      description: "Filtered variants (VCF)"
      download: true
    
    - id: final_bam
      type: file
      description: "Processed alignments (BAM)"
      download: true
    
    - id: variant_stats
      type: file
      description: "Variant calling statistics"
      download: true
    
    - id: pipeline_report
      type: file
      description: "Pipeline execution report"
      download: true

  validation:
    - rule: "file_exists(${reference_genome})"
      message: "Reference genome file must exist"
    
    - rule: "file_exists(${dbsnp_vcf})"
      message: "dbSNP VCF file must exist"
    
    - rule: "${threads} <= 32"
      message: "Maximum 32 threads allowed"
```

---

## Migration from Cloudgene 1.x

### Key Changes

**1. YAML Structure**:
```yaml
# Cloudgene 1.x (YAML)
name: Workflow Name
description: Description
version: 1.0

# Cloudgene 2.x (Django)
id: workflow-name
name: Workflow Name
description: Description
version: 1.0.0
```

**2. Parameter Syntax**:
```yaml
# Cloudgene 1.x
inputs:
  - id: input1
    description: Input 1
    type: text

# Cloudgene 2.x (same, but enhanced)
inputs:
  - id: input1
    type: text
    description: Input 1
    required: true
    validation:
      min_length: 1
```

**3. Step Definition**:
```yaml
# Cloudgene 1.x
steps:
  - name: step1
    jar: tool.jar
    params: input1 output1

# Cloudgene 2.x
steps:
  - name: step1
    classname: workflows.steps.ToolStep
    params:
      input: ${input1}
      output: ${output1}
```

### Migration Checklist

- [ ] Add unique `id` field
- [ ] Update step definitions to use Python classes
- [ ] Add parameter validation rules
- [ ] Update resource specifications
- [ ] Test workflow execution
- [ ] Update documentation

---

## Troubleshooting

### Common Issues

**1. Workflow Not Loading**:
```yaml
# Check YAML syntax
id: test-workflow    # Missing quotes is OK
name: "Test Workflow"  # Quotes needed for special chars

# Validate required fields
workflow:
  steps: []          # At least empty steps required
  inputs: []         # Can be empty
  outputs: []        # Can be empty
```

**2. Parameter Validation Errors**:
```yaml
# Ensure parameter IDs are unique
inputs:
  - id: input_file
    type: file
  - id: input_file    # ERROR: Duplicate ID
    type: folder

# Use valid parameter types
inputs:
  - id: param1
    type: invalid_type  # ERROR: Unknown type
```

**3. Step Execution Failures**:
```yaml
# Ensure classname exists and is importable
steps:
  - name: ProcessData
    classname: workflows.steps.NonExistentStep  # ERROR

# Check parameter references
steps:
  - name: ProcessData
    params:
      input: ${nonexistent_param}  # ERROR: Parameter not defined
```

### Debugging Tools

**1. Validate YAML Syntax**:
```bash
# Use yamllint or Python
python -c "import yaml; yaml.safe_load(open('workflow.yaml'))"
```

**2. Test Workflow Loading**:
```python
from workflows.config_loader import CloudgeneConfigLoader

loader = CloudgeneConfigLoader()
workflow = loader.load_workflow_from_yaml(yaml_content)
```

**3. Check Parameter Resolution**:
```python
# In Django shell
from workflows.models import Workflow

workflow = Workflow.objects.get(id='workflow-id')
config = workflow.get_config()
print(config['workflow']['inputs'])
```

### Performance Tips

**1. Optimize Large Workflows**:
- Use appropriate parameter types
- Implement efficient step classes
- Set resource limits appropriately
- Use temporary files for intermediates

**2. Handle Large Files**:
- Stream file processing where possible
- Use compression for outputs
- Implement progress tracking
- Set appropriate timeouts

---

This comprehensive reference covers all aspects of creating and configuring Cloudgene workflow definitions. For server configuration, see the [Admin Configuration Guide](ADMIN_CONFIGURATION.md).