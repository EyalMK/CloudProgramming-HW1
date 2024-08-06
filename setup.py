import codecs

from setuptools import setup, find_packages

# Read the content of the README file for the long description
with codecs.open('README.md', 'r', 'utf-8') as f:
    long_description = f.read()

setup(
    name='ShapeFlow Monitor',
    version='0.1',
    packages=find_packages(),  # Automatically find packages in the project
    install_requires=[
        'dash',                       # Dash framework for building web applications
        'dash-bootstrap-components',  # Bootstrap components for Dash
        'firebase',                   # Firebase support
        'flask',                      # Flask web framework
        'pyngrok',                    # ngrok support for tunneling
        'pandas',                     # Data analysis library
        'plotly',                     # Plotting library
        'beautifulsoup4',             # HTML parsing library
        'nltk',                       # Natural Language Toolkit
        'requests',                   # HTTP library
    ],
    entry_points={
        'console_scripts': [],        # No console scripts are defined
    },
    author='Team Unicorn',
    description='onShape Log Analysis Dashboard',  # Short summary of the package
    long_description=long_description,  # Detailed description from README.md
    long_description_content_type='text/markdown',  # Format of long description
    url='https://github.com/EyalMK/ShapeFlow-Monitor-Cloud',  # Project URL
    classifiers=[
        'Programming Language :: Python :: 3',     # Indicates compatibility with Python 3
        'License :: OSI Approved :: MIT License',  # License type
        'Operating System :: OS Independent',      # Compatibility with all operating systems
    ],
    python_requires='>=3.8',  # Minimum Python version required
)
