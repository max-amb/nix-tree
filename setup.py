from setuptools import setup

setup(
    name = 'nix-tree',
    version = '0.1.0',
    packages = ['nix-tree'],
    entry_points = {
        'console_scripts': [
            'nix-tree = nix-tree.main:main'
        ]
    }
)
