import os.path as path
from setuptools import setup, find_packages

with open(path.join(path.abspath(path.dirname(__file__)), 'README.md')) as f:
    long_description = f.read()

setup(name='lrcurve',
      version='2.2.0',
      description='Real-time learning curve for Jupiter notebooks',
      long_description=long_description,
      long_description_content_type='text/markdown',
      keywords='learning curve pytorch keras tensorflow jupyter colab interactive live real-time',
      url='https://github.com/AndreasMadsen/lrcurve',
      author='Andreas Madsen',
      author_email='amwebdk@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
        'ipython'
      ],
      test_suite='nose.collector',
      tests_require=[
        'nose',
        'jupyterlab',
        'tensorflow',
        'torch',
        'scikit-learn'
      ],
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      include_package_data=True,
      zip_safe=False)