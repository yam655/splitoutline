#/usr/bin/env python3

from distutils.core import setup

VERSION="0.3"

setup(name='splitoutline',
      version=VERSION,
      description="A helper script for writing novels with Sphinx.",
      long_description="""
`splitoutline` exists to take a reStructuredText outline file and convert
it in to a set of scene files and chapter files. As the outline gains more
detail, the changes are reflected in the scenes/chapters.

These scene files contain a full annotated version of the novel, so they
can easily have consolidated details of notes from various editors or
reviewers. For distribution all of these details get stripped out, leaving
only simple style that will work fine in ePUB files.
      """,
      author="Steven Black",
      author_email="yam655@gmail.com",
      maintainer="Steven Black",
      maintainer_email="yam655@gmail.com",
      license="GPLv3",
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Text Processing",
      ],
      packages=['splitoutline', ],
      scripts=["scripts/splitoutline", ],
    )

