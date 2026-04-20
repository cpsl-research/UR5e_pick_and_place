from setuptools import find_packages, setup

package_name = 'realsense_pub'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='aashikajaggy',
    maintainer_email='aashika.jagadeesh@gmail.com',
    description='Publishing coordinates to a topic',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	'publisher_node = realsense_pub.markerFinderPublisherNode:main' 
        ],
    },
)
