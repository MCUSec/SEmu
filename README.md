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

## Cleaning Code .... (expected to be public before March)
