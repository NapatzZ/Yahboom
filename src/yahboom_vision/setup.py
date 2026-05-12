from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'yahboom_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robotkubofficial',
    maintainer_email='robotkubofficial@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "image_proc=yahboom_vision.image_proc:main",
            "human_detection=yahboom_vision.human_detection:main",
        ],
    },
)
