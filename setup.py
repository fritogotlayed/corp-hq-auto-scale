#!/usr/bin/env python

import setuptools

setuptools.setup(
    name='corp-hq-auto-scale',
    author='maddonkeysoftware',
    description='CorpHQ auto scaling micro service',
    url='',
    version='0.0.1',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_dir={'corp_hq_auto_scale': 'corp_hq_auto_scale'},
    entry_points={
        'console_scripts': [
            'corp-hq-auto-scale = corp_hq_auto_scale.app:main'
        ]
    }
)