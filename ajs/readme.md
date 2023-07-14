# Analyse JStacks (AJS)

## Setup

### Ensure the following files are there

- `.ajs`
  - `analysis.txt`
  - `config.json`
  - `config.sample.json`
  - `jstacks.txt`
  - `warnings.log`
- `ajs.py`
- `connectors.py`
- `context.py`
- `core.py`
- `jenkins_configuration.py`
- `legacy_configuration.py`
- `thread_schema.py`
- `utils.py`

Depending on what you want to use, `jenkins_configuration.py` or `legacy_configuration.py`, make necessary changes in script. Changes would optimistically only include `import` statements.

### Dependencies

- AJS has primarily only one python library dependency
- `pip install prettytable`

### If you want to use azure upload service

- Setup and login into azure cli
  - `brew update && brew install azure-cli`
  - `az login`

- Install azure python connector libraries
- `pip install azure-storage-blob azure-identity`

- Uncomment the following lines
- `ajs.py` : Line 41
  - `connectors.py` : Line [386 - 391]
  - `utils.py` : Line 4, [16-17] and [180 - 199]

### If you're using Python 2
- Uncomment the following lines, for cleaner output
  -`utils.py` : Line [10-14]

## Usage

### CLI

- `python3 ajs.py -h`
```
usage: ajs.py [-h] [-b] [-f] [-A] [-I] [-O] [-S] [-C] [-R] [-J] [-T] [-F] session_name

Analyse JStacks, a tool to analyze java thread dumps. Configure settings in 'config.json', Sample config file is given in
'.ajs/config.sample.json'

positional arguments:
  session_name                        Name of the debugging session

options:
  -h, --help                          show this help message and exit
  -b, --benchmark                     Run in [b]enchmark mode
  -f, --file-input                    Use configured JStack and Top [f]iles as input
  -A, --full-analysis                 Perform [A]ll analysis, equivalent to -IOSCRJTF
  -I, --include-only                  Only [I]nclude configured threads
  -O, --filter-out                    Filter [O]ut configured threads [preference will be given to -I]
  -S, --search-tokens                 [S]earch for configured tokens in the jstack
  -C, --classify-threads              [C]lassify threads based on configured regexes
  -R, --repetitive-stack-trace        Detect [R]epetitive stack traces in threads
  -J, --cpu-consuming-threads-jstack  Output most CPU Intensive threads, calculated using [J]stacks [supported in jdk11+]
  -T, --cpu-consuming-threads-top     Output most CPU Intensive threads, calculated using [T]op utility
  -F, --thread-state-frequency        Analyse thread state [F]requencies for all jstacks

```

### Legacy Configuration

- Legacy configuration uses `.ajs/config.json` file for configuration
- Following is a sample `.ajs/config.json` file, which is also there in `.ajs/config.sample.json`

```
{
  "include_only": [
    { "regex": "mongo" },
    { "regex": "RUNNABLE" }
  ],
  "filter_out": [
    { "regex": "cluster-ClusterId"},
    { "regex": "grpc-default" },
    { "regex": "kafka-producer-network-thread" },
    { "regex": "broadcastRedisContainer" },
    { "regex": "cluster-rtt-ClusterId" },
    { "regex": "CompilerThread0" }
  ],
  "search_tokens": [
    {
      "text": "Finalizer",
      "output_all_matches": true 
    }
  ],
  "classification": [
    { "regex": ".*MongoTemplateInternal.*", "tag": "Mongo" },
    { "regex": ".*elasticsearch.*", "tag": "Elasticsearch" }
  ],
  "classification_print_trace": true,

  "namespace": "default",
  "pod_name": "java-deployment-66c74f6dbd-vjzhq",
  "container_name": "java-app",
  "num_of_jstacks": 5,
  "delay_bw_jstacks": 1,

  "top_file_path": "/path/to/top/file",
  "jstack_file_path": "/path/to/jstack/file",

  "cpu_threshold_percentage": 5,
}
```
