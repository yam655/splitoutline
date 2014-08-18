======================
The Configuration File
======================

File locations
==============

The configuration file is a standard INI format file. This functionality was
whipped out in a frenzy to support a NaNoWriMo attempt, and it appears that
some aspects of this was not thought through.

We support a number of configuration file names. These names are checked in order
with the later names taking precedence over the earlier names:

1. `./splitoutline.ini`: The normal use-case requires only a single configuration
   file per project, and the configuration file -- like the Sphinx configuration
   file -- should probably be at the root of the project.

2. `$HOME/.splitoutline.ini`: the use-case for this is that it doesn't require the
   command run from any particular directory, but running Sphinx still requires
   the process start from the root, so it is unclear whether there's any benefit
   of having this location.

3. `SPLITOUTLINE_CONF` environment variable: This is similar to the home directory
   use-case, but supports workflows where multiple projects are switched between
   through the use of shell functions. Unfortunately, the flaw with the earlier
   design also impacts this. Sphinx runs from the root of the documentation, so
   it is unclear whether this functionality is useful.

4. The `--config` option: This would be the normal way to store the configuration
   file in a subdirectory or with an alternate name. The `splitoutline` command
   must be embedded in the `Makefile` (or the `make.bat` file), so this is usually
   all that is needed.

File format
===========

The configuration file is a standard INI format, with one required section
(`global`). Within this section is a `projects` field which should be a space
separated list of other section names. ::

    [global]
    root=.
    suffix=.txt
    chapter-prefix=chapter-
    chapter-stub-prefix=chapter-
    projects=book1

    [book1]
    outline=book1/design/outline.txt
    chapter-dir=book1/chapters
    chapter-stub-dir=book1/scenes

The 'global' section
~~~~~~~~~~~~~~~~~~~~

`splitoutline` does not currently parse any of the Sphinx configuration files, so
there's some minor configuration that gets duplicated in both locations.

`root`: specifies the root of the documentation project, as also specified within 
the Sphinx documentation.

`suffix`: specifies the file suffix, just like in the Sphinx configuration. The
usual values are ".txt" and ".rst". I've found that ".txt" has been useful when
the project is stored in DropBox, as it allows the use of the DropBox mobile
text editor.

`chapter-prefix`: Chapters are composed of a series of scenes. `splitoutline`
both splits outlines in to scenes as well as pieces the scenes together to form
chapters. These chapters have been stripped of most of the enhanced reStructuredText
features, leaving just the core features for a novel.

`chapter-stub-prefix`: There's also a capacity for an annotated version of the novel.
This version contains details from the outline at the beginning of each scene, and
each scene retains all reStructuredText features. These scenes are pieced together
using generated "stub" chapters which contain references to the scenes in the correct
order.

`projects`: This is a space separated list of sections for each of the projects.
The design explicitly supports multiple books sharing a common set of notes.
We have a story bible containing the full notes for all books as well as annotated
scenes making a wealth of information in an easily sharable form.

The book section
~~~~~~~~~~~~~~~~

The book sections are simpler, but more important.

`outline`: This specifies the outline file. The outline file is the heart of the
`splitoutline` process.

`chapter-dir`: The location that the chapter files should be stored in. This location
can be a sibling of the scene directory, but neither should contain the other.

`chapter-stub-dir`: The location for the chapter stub files that directly reference
the scene files.

It should be possible to use some sane-standards for some of these values, but
trial was needed to iron out the best values.

