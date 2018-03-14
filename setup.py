from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='Simple Git',
    version='0.1',
    author='Maksymilian Ratajczyk',
    author_email='kontakt@maksymilianratajczyk.pl',
    description=('Simple implementation of git like system'
                 'in Python'),
    license='MIT',
    py_modules=['sgit', 'formats'],
    packages=['simple_git'],
    url='https://github.com/mratajczyk/simple-git',
    install_requires=required,
    entry_points='''
        [console_scripts]
        sgit=sgit:cli
    '''
)
