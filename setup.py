from setuptools import setup, find_packages

setup(
    name='ShapeFlow Monitor',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'dash',
        'dash-bootstrap-components',
        'firebase',
        'flask',
        'pyngrok',
        'pandas',
        'plotly',
        'beautifulsoup4',
        'nltk',
        'requests',
    ],
    entry_points={
        'console_scripts': [],
    },
    author='Team Unicorn',
    description='onShape Log Analysis Dashboard',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/EyalMK/ShapeFlow-Monitor-Cloud',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
