# SEmu
A Specification-based Firmware Emulator

## Genearl idea
Unlike exsiting firmware emulator which finds out how to respond to peripheral read operations by analyzing the target firmware, we propose a new approach that builds peripheral models from the peripheral specification. Using Natural Language Processing (NLP), we translate peripheral behaviors in human language (documented in chip manuals) into a set of structured condition-action rules. By checking, executing, and chaining them at run time, we can dynamically synthesize a peripheral model for each firmware execution. 

## Citing our paper

```bibtex
@inproceedings{SEmu,
  title={What Your Firmware Tells You Is Not How You Should Emulate It: A Specification-Guided Approach for Firmware Emulation},
  author={Zhou, Wei and Zhang, Lan and Guan, Le and Liu, Peng and Zhang, Yuqing},
  booktitle={Proceedings of the 2022 ACM SIGSAC Conference on Computer and Communications Security},
  pages={3269--3283},
  year={2022}
}
```

## Directory structure of the repo
```
.
├── LICENSE
├── README.md
├── docs                     # more documentation about implementation and configuration
├── DataSet                  # test samples
|    ├── p2im-unit_tests      # p2im unit test samples
|    └── Fuzzing-tests        # Fuzzing test samples
├── SymDiagnose/Scripts
|    ├── launch-SEmu-template.sh  # template scripts to launch SEmu symbolic dignose tool
|    ├── SEmu-helper.py           # helper scripts to configurate SEmu based on configration file.
|    └── SEmu-config-template.lua # template config file of SEmu plugins used by helper script
├── RuleExtraction       # tool used to extract C-A rule for manual
├── Manual                   # Reference manual of MCU
|    └── Extracted Rules      # Extract C-A rules of MCU reference manual 
└── SEmu-Fuzz                # emulator tool for fuzzing based extracted C-A Rule
```

## Extract C-A Rules (SEmu-RuleExtractor )

1. Stanford [tagger](https://nlp.stanford.edu/software/tagger.shtml) and [parser](https://nlp.stanford.edu/software/lex-parser.shtml) have been uploaded to [google drive](https://drive.google.com/file/d/1ZoIL5lQMNPykCb4axHseqRxGbjw7S2x2/view?usp=sharing). You may need to download it and unzip to models. 

### Usage
```
cd RuleExtraction
python extract.py manual_name peripheral_name
```
Arguments:

- manual_name e.g., F103
- peripheral_name e.g., USART

Example:

```
python extract.py k64 UART
```

It takes **Manuals/manual_name/tabula-peripheral_name.csv** as the input to extract rules. We would suggest to retrieve the Memory map, register descriptions, and interrupt information from the original PDF manuals using tabula.

After the above command successfully finishes, the extracted results are saved in **manual_name/data/**(e.g. k64/data/). 

- peripheral_namememory.txt (e.g. USARTmemory.txt) lists the registers information including address, width, type, and so on.
- peripheral_nameread.txt (e.g. USARTread.txt) lists the read constriants.
- peripheral_namewrite.txt (e.g. USARTwrite.txt) lists the write constriants.
- peripheral_nameflags.txt(e.g.descriptorflags.txt) lists the rules about hardware signals.
- peripheral_nametas.txt (e.g. USARTtas.txt) lists the c-a rules.
- peripheral_nameregisters.txt (e.g. USARTregisters.txt) merges all results in one file.

3. Concatenate rules

```
bash run.sh
```
All C-A rules will be concatenated in **extractedRules/**(e.g. extractedRules/k64.txt).

## Diagnose C-A Rules (SEmu-RuleDoctor)

### Required packages
SEmu-RuleDoctor is built with S2E, so you must install a few packages in order to build SEmu
The required packages of SEmu is same as the current S2E 2.0,
You can check out all [required packages](https://github.com/MCUSec/uEmu/blob/main/vagrant-bootstrap.sh#L8) from line 8 to 21 in the Vagrant script.

### Checking out source code

The SEmu source code can be obtained from the our org. git repository using the following commands.

```console
 export SEmuDIR=/home/user/SEmu  # SEmuDIR must be in your home folder (e.g., /home/user/SEmu)
 sudo apt-get install git-repo   # or follow instructions at https://gerrit.googlesource.com/git-repo/
 cd $SEmuDIR
 repo init -u https://github.com/MCUSec/manifest.git -b SEmu
 repo sync
```
This will set up the SEmu repositories in ``$SEmuDIR``.


### Building SEmu-RuleDoctor
**Note:**Since the qemu in arm kvm mode will use ptrace.h which is from the host arm linux kernel, however the real host SEmu is X86, so you have to add ptracearm.h from [linux source code](https://elixir.bootlin.com/linux/latest/source/arch/arm/include/asm/ptrace.h) (you can directly download it from [μEmu repo](https://github.com/MCUSec/uEmu/blob/main/ptracearm.h)) to the your local path: ``/usr/include/x86_64-linux-gnu/asm``.
The SEmu-RuleDoctor Makefile can be run as follows:

```console
    $ sudo mkdir $SEmuDIR/build
    $ cd $SEmuDIR/build
    $ make -f $SEmuDIR/Makefile && make -f $SEmuDIR/Makefile install
    # This will take some time (approx. 30-60 mins on a 4-core machine)
```
By default, the ``make`` command compiles and installs SEmu in release mode to ``$SEmuDIR/build/opt``. To change this
location, set the ``S2E_PREFIX`` environment variable when running ``make``.

### Updating

You can use the same Makefile to recompile SEmu either when changing it yourself or when pulling new versions through
``repo sync``. Note that the Makefile will not automatically reconfigure the packages; for deep changes you might need
to either start from scratch by issuing ``make clean`` or to force the reconfiguration of specific modules by deleting
the corresponding files from the ``stamps`` subdirectory.

### Usage
All SEmu-RuleDoctor plugins are enabled and configured with Lua-based configuration file `SEmu-config.lua`.
To provide user a more user-friendly configuration file, we provide python script named `SEmu-helper.py` to quickly generate Lua-base configure files based on template file `SEmu-config-template.lua`  based on a sample user-defined CFG file.

It will also generate launch scripts to run SEmu-RuleDoctor based on `launch-SEmu-template.sh` file. 

Please checkout  `launch-SEmu-template.sh`, `SEmu-config-template.lua` and `library.lua` scripts in **SymDiagnose/Scripts** and make sure them exist and place in the same path e.g., <proj_dir>  with `SEmu-helper.py`.

#### Preparing the user configuration file
You can use the configuration files provided in our DataSet folder to test our samples.
If you want to test your own firmware, please refer to [instruction](docs/Configuration.md) and [μEmu](https://github.com/MCUSec/uEmu) tool to edit the user configuration file.

#### Demo
```bash
Usage: python3 <repo_path>/SEmu-helper.py <firmware_name> <config_file_name>  -rule RuleFILENAME
```
- arguments:
  * -rule FILENAME,       Configure the C-A Rule filename used for SEmu-RuleDoctor

## Fuzzing with C-A SEmu (SEmu-Fuzz)
Refer to [SEmu-Fuzz](https://github.com/IoTS-P/SEmu-Fuzz) repo.


