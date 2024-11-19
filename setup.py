from setuptools import setup, find_packages

setup(
    name='smart_time_management_clock',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'psutil',
        'Pillow'
    ],
    entry_points={
        'console_scripts': [
            'smart-clock=clock.main:main'
        ]
    },
    description='An intelligent time management clock with focus mode and app monitoring.',
    author='Your Name',
    author_email='your.email@example.com',
)