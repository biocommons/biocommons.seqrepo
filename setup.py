# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

package_name = "biocommons.seqrepo"
short_description = open("doc/short_description.txt").read()
long_description = open("README.rst").read()

namespace_package = "".join(package_name.split(".")[:-1])
setup(
    author = package_name + " Committers",
    description = short_description.replace("\n", " "),
    license = "Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)",
    long_description = long_description,
    name = package_name,
    namespace_packages = [namespace_package],
    package_data = {
        "biocommons.seqrepo.fastadir": ["_data/migrations/*"],
        "biocommons.seqrepo.seqaliasdb": ["_data/migrations/*"],
        },
    packages = find_packages(),
    use_scm_version = True,
    zip_safe = True,

    author_email = "biocommons-dev@googlegroups.com",
    url = "https://github.com/biocommons/" + package_name,

    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Database :: Front-Ends",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],

    keywords = [
        'bioinformatics',
    ],

    entry_points = {
        "console_scripts": [
            "seqrepo = biocommons.seqrepo.cli:main",
        ],
    },

    extras_require = {
        "admin": ["coloredlogs", "requests_html"],
    },

    install_requires = [
        "bioutils>=0.3.1",
        "ipython>=5,<6",        # limit for Python 2 compatibility
        "pysam",
        "six",
        "tqdm",
        "yoyo-migrations>5,<6",
    ],

    setup_requires = [
        "pytest-runner",
        "setuptools_scm",
        #"sphinx",
        #"sphinx_rtd_theme",
        #"sphinxcontrib-fulltoc",
        "wheel",
    ],

    tests_require = [
        "pytest",
        "pytest-cov",
        "coverage<5.0",         # 5.0a2 appears to break coverage file format
    ],
)

# <LICENSE>
# Copyright 2016 Source Code Committers
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
