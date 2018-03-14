# Simple git 

Simple implementation of git like program in Python

## Getting Started

### Requirements

Python 3

### Installing

```
git clone https://github.com/mratajczyk/simple-git.git
cd simple-git
python3 setup.py install
```

### Sample usage

```
mkdir test && cd test && sgit init
touch file1 && touch file2 
sgit status
sgit add file1 && sgit status
echo "test" >> file1 && sgit status
sgit commit -m test && sgit status
sgit add . && sgit commit -m all && sgit status
sgit log
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
