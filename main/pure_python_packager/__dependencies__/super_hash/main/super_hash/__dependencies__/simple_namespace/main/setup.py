import setuptools
 
with open("../README.md", "r") as file_handle:
    long_description = file_handle.read()
 
setuptools.setup(
    name='simple_namespace',
    version='1.0.0',
    description="Organize code better with namespaces",
    url='https://github.com/jeff-hykin/simple_namespace',
    author='Jeff Hykin',
    author_email='jeff.hykin@gmail.com',
    license='MIT',
    packages=['simple_namespace'],
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
)