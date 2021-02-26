from setuptools import setup

import os.path
# Change to the directory of this file before the build
os.chdir(os.path.dirname(os.path.realpath(__file__)))
# Build setup
setup(
    name='ffwm',
    version='1.0.1',
    packages=['ffwm'],
    license='MIT License',
    author='Yuxiang Wei',
    url='https://github.com/ananiask8/FFWM',
    description='Learning Flow-based Feature Warping for Face Frontalization '
                'with Illumination Inconsistent Supervision',
    setup_requires=[
        'setuptools>=18.0'
    ],
    package_data={
        'ffwm': [
            'data/*',
            'data_process/*',
            'lightcnn/*',
            'models/*',
            'options/*',
            'util/*',
        ]
    },
    install_requires=[],  # requirements.txt is included
    include_package_data=True,
)
