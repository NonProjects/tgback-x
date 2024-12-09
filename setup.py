from setuptools import setup
from ast import literal_eval

with open('tgback_x/version.py', encoding='utf-8') as f:
    version = literal_eval(f.read().split('=')[1].strip())

setup(
    name         = 'tgback-x',
    version      = version,
    packages     = ['tgback_x'],
    license      = 'MIT',
    description  = 'tgback-x — a library for making Telegram account backups',
    long_description = open('README.md', encoding='utf-8').read(),
    author_email = 'thenonproton@pm.me',
    url          = 'https://github.com/NonProjects/tgback-x',
    download_url = f'https://github.com/NonProjects/tgback-x/archive/refs/tags/v{version}.tar.gz',

    long_description_content_type='text/markdown',

    keywords = [
        'Telegram', 'Backup', 'Account', 'Non-official'
    ],
    install_requires = [
        'pyaes==1.6.1',
        'telethon==1.38.1',
        'phrasegen==1.0.0'
    ],
)
