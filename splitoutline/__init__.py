#!/usr/bin/env python3

#  Copyright 2014 Steven Black
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import csv, codecs, io
import configparser
import os
import os.path
import sys
import re
import locale
import gettext

from datetime import date
from argparse import ArgumentParser

from csvhelpers import *

version = "%{prog}s Version 0.3"

usage = "usage: %{prog}s"
description = (
    "A simple helper for fiction-related projects."
)
epilog = (
    ""
)
config_file="splitoutline.ini"

parser = ArgumentParser(usage=usage, 
                      description=description)
parser.add_argument('--version', action='version', version=version,
                  help="Print the version text.")
parser.add_argument("-v", "--verbose",
                  action="count", default=0,
                  help="Be more verbose")
parser.add_argument("-c", "--config", metavar="FILE", default=None,
                  help="Set the configuration file to FILE."
                       "[default: %s]" % (os.path.relpath(config_file),))
parser.add_argument("-d", "--dry-run", default=False, action="store_true",
                  help="Do not update any reStructuredText files.")
parser.add_argument("projects", nargs='*', metavar="PROJECT",
                  help="Select alternate projects from the config.")
 SplitOutline(object):
    _verbose = 0
    _dryrun = False
    outline_re = re.compile(r"^(?P<space>\s*)(?P<list>[*+-]|[0-9]+[.]?|[#][.])\s*")
    chapter_re = re.compile(r"^\s*(?:[*+-]|[0-9]+[.]?|[#][.])\s*(?P<title>[^<>]*?)\s*$")
    scene_re = re.compile(r"^\s*(?:[*+-]|[0-9]+[.]|[#][.])\s+.*?`(?P<text>[^`<]+?)\s*<(?P<ref>.*?)>.*\s*$")
    epigraph_re = re.compile(r"^\s+:(?P<name>Epigraph|Also include|Start with):\s.*<(?P<ref>.*?)>.*\s*$")
    role_re = re.compile(r"(?:[:](?P<domain>[a-z0-9-]+))?[:](?P<role>[a-zA-Z0-9-]+)[:]`(?P<text>[^<`]+)(?:\s+[<](?P<ref>[^>`]+)>)?\s*`")
    term_re = re.compile(r"[:]term[:]`\s*(?P<text>[^<`]+?)\s*`")
    link_re = re.compile(r"`\s*(?P<text>[^ `]+?)\s*`_")
    footnote_re = re.compile(r"[[](?P<text>[^] []+)[]]_")
    section_re = re.compile(r"^([\]\[{}@?/\\%$&-=`;:'\"~^_*+#\)!\(<>|])\1+$")
    word_re = re.compile(r'(\w\S*\w|\w)')

    epigraphs = {}

    def verbose(self, s, nonl=False):
        if self._verbose > 0:
            if nonl:
                print(s, end=' ')
            else:
                print(s)

    def debug(self, i, s, nonl=False):
        if self._verbose > i:
            if nonl:
                print(s, end=' ')
            else:
                print(s)

    def parse_outline_file(self):

        outline_data = []
        try:
            with codecs.open(self.outline_path, "rtU", "utf-8") as outlineFile:
                outline_data = outlineFile.readlines()
        except IOError:
            print("Error: Unable to open outline file.")
            sys.exit(2)

        chNum = 0;
        data = []
        self.outlineData = {}
        start = 0
        end = None
        for i in range(len(outline_data)):
            if outline_data[i].startswith(".. outline:start"):
                start = i
            elif outline_data[i].startswith(".. outline:end"):
                end = i
        if start != 0 or end is not None:
            if end is None:
                outline_data = outline_data[start:]
            else:
                outline_data = outline_data[start:end]
        lastData = None
        lastHead = []
        for line in outline_data:
            outMatch = self.outline_re.match(line)
            epiMatch = self.epigraph_re.match(line)
            if outMatch is None and epiMatch is None:
                if lastData is not None and len(lastHead) > 0:
                    if line.strip() == "" or line.startswith(lastHead[-1]):
                        lastData.append(line)
                    else:
                        lastData = None
                        while len(lastHead) > 0 and not line.startswith(lastHead[-1]):
                            del lastHead[-1]
                continue
            if outMatch is not None:
                newHead = outMatch.group("space")
                if len(lastHead) > 0 and newHead.startswith(lastHead[-1]):
                    if len(lastHead) > 0 and newHead == lastHead[-1]:
                        pass
                    else:
                        lastHead.append(newHead)
                else:
                    while len(lastHead) > 0 and not line.startswith(lastHead[-1]):
                        del lastHead[-1]
                    if len(lastHead) > 0 and newHead == lastHead[-1]:
                        pass
                    else:
                        lastHead.append(newHead)

            chapMatch = self.chapter_re.match(line)
            sceneMatch = self.scene_re.match(line)
            if chapMatch is None and sceneMatch is None and epiMatch is None:
                if len(lastHead) == 1:
                    if len(data) > 0 and len(data[-1]) == 1:
                        del data[-1] # No scenes. Forget it.
                    else:
                        chNum += 1
                    chapter = "Chapter %u" % chNum
                    data.append([chapter])
                    lastData = [line]
                    self.outlineData[chapter] = lastData

                if lastData is not None:
                    lastData.append(line)
                continue
            if chapMatch is not None and sceneMatch is not None:
                print("WARNING: line matches chapter and scene:", line)
                continue
            if chapMatch is not None and len(lastHead) == 1:
                chapter = chapMatch.group("title")
                if chapter is None:
                    continue
                if len(data) > 0 and len(data[-1]) == 1:
                    del data[-1] # No scenes. Forget it.
                else:
                    chNum += 1
                if chapter == "":
                    chapter = "Chapter %u" % chNum
                data.append([chapter])
                lastData = [line]
                self.outlineData[chapter] = lastData
            elif chapMatch is not None:
                chapter = chapMatch.group("title")
                if chapter.strip() != "" and lastData is not None:
                    lastData.append(line)

            if sceneMatch is not None:
                if len(lastHead) == 1: # No existing chapter!
                    if len(data) > 0 and len(data[-1]) == 1:
                        del data[-1] # No scenes. Forget it.
                    else:
                        chNum += 1
                    chapter = sceneMatch.group("text")
                    data.append([chapter])
                    lastData = [line]
                    self.outlineData[chapter] = lastData

                last_scene = sceneMatch.group("ref")
                lastData = [line]
                self.outlineData[last_scene] = lastData
                data[-1].append(last_scene)
            if epiMatch is not None:
                epigraph_name = epiMatch.group("ref")
                self.epigraphs[epigraph_name] = True
                lastData = [line]
                self.outlineData[epigraph_name] = lastData
        if len(data) == 0:
            print("WARNING: no chapters found.")
            sys.exit(1)
        self.outline = data
        return data

    def create_chapter_stubs(self):
        chNum = 0
        chfmt = "%%0%uu" % (len(str(len(self.outline))),)
        for ch in self.outline:
            chNum += 1
            chappath = os.path.join(self.chapterstub_path,
                                    self.chapterstub_prefix
                                    + chfmt % (chNum,)
                                    + self.suffix)
            title = ch[0]
            d = '*' * len(title)

            if self._dryrun:
                chapfile = sys.stdout
            else:
                chapfile = codecs.open(chappath, "wt", "utf-8")

            ref = chappath
            if ref.endswith(self.suffix):
                ref = ref[:-len(self.suffix)]
            ref = re.sub("[-._/]+", "-", ref)
            if ref.startswith("-"):
                ref = ref[1:]
            chapfile.write(".. _" + ref + ":\n\n")

            chapfile.write(d + "\n" + title + "\n" + d + "\n\n")

            wrote = False
            eatTitle = True
            needNewline = False
            indentLevel = None

            for line in self.outlineData.get(title, []):
                if eatTitle:
                    if line.strip() == "":
                        eatTitle = False
                    continue
                if not wrote:
                    wrote = True
                    chapfile.write("\n.. container:: from-outline\n\n")
                if line.strip() == "":
                    chapfile.write("\n")
                    needNewline = False
                    continue
                elif indentLevel is None:
                    indentLevel = 0
                    while line[indentLevel] == ' ':
                        indentLevel += 1
                    indentLevel = " " * indentLevel
                    if indentLevel == "":
                        # drop this line and try again
                        indentLevel = None
                        needNewline = False
                        chapfile.write("\n")
                        continue
                if not line.startswith(indentLevel):
                    # Invalid line, ignore it
                    needNewline = False
                    chapfile.write("\n")
                    continue
                needNewline = True
                chapfile.write("   ")
                chapfile.write(line[len(indentLevel):])

            if needNewline:
                chapfile.write("\n")

            chapfile.write(".. toctree::\n\n")
            for scene in ch[1:]:
                sceneRealPath = self.find_path(scene, self.outline_path)
                scenePath = os.path.relpath(sceneRealPath,
                                    self.chapterstub_path)
                chapfile.write("   %s\n" % scenePath)
            chapfile.write("\n")
            chapfile.write(".. container:: from-stats\n")
            chapfile.write("\n")
            statpath = os.path.join(self.chapter_path, self.statdir, os.path.basename(chappath))
            if not statpath.startswith("/"):
                statpath = "/" + statpath
            chapfile.write("   .. include:: %s\n" % (statpath,))
            chapfile.write("\n")
            if not self._dryrun:
                chapfile.close()
                chapfile = None
            else:
                chapfile.write("\n")
        return

    def rewrite_scene(self, scene, chaptitle = None):
        scenePath = self.find_path(scene, self.outline_path)
        if self._dryrun:
            sys.stdout.write("# start rewriting " + scene + " \n")

        outlineJunk = []

        outlineJunk.append(".. container:: from-outline")
        outlineJunk.append("")

        eatTitle = True
        indentLevel = None
        wrote = False
        if chaptitle is not None:
            for line in self.outlineData.get(chaptitle, []):
                if eatTitle:
                    if line.strip() == "":
                        eatTitle = False
                    continue
                if not wrote:
                    wrote = True
                    outlineJunk.append("   .. rubric:: Chapter Information")
                    outlineJunk.append("")
                if line.strip() == "":
                    if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                        outlineJunk.append("")
                    continue
                elif indentLevel is None:
                    indentLevel = 0
                    while line[indentLevel] == ' ':
                        indentLevel += 1
                    indentLevel = " " * indentLevel
                    if indentLevel == "":
                        # drop this line and try again
                        indentLevel = None
                        if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                            outlineJunk.append("")
                        continue
                if not line.startswith(indentLevel):
                    # Invalid line, ignore it
                    if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                        outlineJunk.append("")
                    continue
                useline = "   " + line[len(indentLevel):].rstrip()
                outlineJunk.append(useline)
            if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                outlineJunk.append("")

        eatTitle = True
        indentLevel = None
        wrote = False
        for line in self.outlineData.get(scene, []):
            if eatTitle:
                if line.strip() == "":
                    eatTitle = False
                continue

            if not wrote:
                wrote = True
                outlineJunk.append("   .. rubric:: Scene Information")
                outlineJunk.append("")
            if line.strip() == "":
                if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                    outlineJunk.append("")
                continue
            elif indentLevel is None:
                indentLevel = 0
                while line[indentLevel] == ' ':
                    indentLevel += 1
                indentLevel = " " * indentLevel
                if indentLevel == "":
                    # drop this line and try again
                    indentLevel = None
                    if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                        outlineJunk.append("")
                    continue
            if not line.startswith(indentLevel):
                # Invalid line, ignore it
                if len(outlineJunk) > 0 and outlineJunk[-1] != "":
                    outlineJunk.append("")
                continue
            useline = "   " + line[len(indentLevel):].rstrip()
            outlineJunk.append(useline)

        if len(outlineJunk) > 0 and outlineJunk[-1] != "":
            outlineJunk.append("")

        del(wrote)
        del(eatTitle)
        del(indentLevel)
        outlineJunk.append("   .. container:: from-stats")
        outlineJunk.append("")
        statpath = os.path.join(os.path.dirname(scene), self.statdir, os.path.basename(scene) + self.suffix)
        if statpath.startswith("/"):
            statpath = statpath[1:]
        if os.path.isfile(statpath):
            statpath = "/" + statpath
            outlineJunk.append("      .. include:: %s" % (statpath,))
            outlineJunk.append("")
        else:
            sys.stdout.write("Failed to find %s\n" % statpath)

        if not os.path.isfile(scenePath + self.suffix):
            if len(self.outlineData.get(scene, [])) == 0:
                sys.stdout.write("No scene data for %s\n" % scene)
                return
            dirname = os.path.dirname(scenePath)
            if not os.path.isdir(dirname):
                if self._dryrun:
                    print("Would make directories: ", dirname)
                elif not os.path.isdir(dirname):
                    os.makedirs(dirname)

            sceneMatch = self.scene_re.match(self.outlineData.get(scene)[0])
            if sceneMatch is None:
                sys.stdout.write("Failed to find match for %s\n" % scenePath)
                return
            title = sceneMatch.group("text")

            if self._dryrun:
                print("Scene path does not exist:", scene)
                print("... would create new scene file.")
                print("    ", scenePath)
            else:
                self.verbose("Creating missing scene %s\n" % scenePath)
                with codecs.open(scenePath + self.suffix, "wt", "utf-8") as out:

                    ref = sceneMatch.group("ref")
                    ref = re.sub(r"[-._/]+", "-", ref)
                    if ref.startswith("-"):
                        ref = ref[1:]
                    out.write(".. _" + ref + ":\n\n")

                    s = "=" * len(title)
                    out.write("%s\n%s\n\n" % (title, s,))

                    if len(outlineJunk) > 0:
                        out.write("\n".join(outlineJunk))
                        out.write("\n\n")
                        out.write(".. todo::\n   Write :ref:`" + ref + "`\n\n")

        else:
            sceneFile = codecs.open(scenePath + self.suffix, "rtU", "utf-8")
            lines = sceneFile.readlines()
            sceneFile.close()
            
            isBlank = True
            insertMark = None
            cutStart = cutEnd = None
            noChange = True
            lastcol = col = 0
            for i in range(len(lines)):
                lastBlank = isBlank
                line = lines[i].rstrip()
                if line == ".. container:: from-outline":
                    cutStart = i
                    continue
                lastcol = col
                col = 0
                line = line.replace("\t", "        ")
                while len(line) > col and line[col].isspace():
                    col += 1
                if cutStart is not None and cutEnd is None:
                    cutIndex = i - cutStart
                    if cutIndex < len(outlineJunk):
                        if col == 0 and line != "":
                            self.debug(2, "%s unexpected empty line" % scenePath)
                            cutEnd = i
                            noChange = False
                        elif outlineJunk[cutIndex] != line:
                            noChange = False
                            self.debug(2, "%s different content" % scenePath)
                    elif cutIndex == len(outlineJunk):
                        if col == 0 and len(line) > 0:
                            cutEnd = i
                        if cutIndex > len(outlineJunk)+1:
                            self.debug(2, "%s extra junk in file: %s" % (scenePath, line))
                            noChange = False
                    elif col == 0 and len(line) > 0:
                        cutEnd = i
                        self.debug(2, "%s found end late" % scenePath)
                        noChange = False
                    else:
                        continue
                line = line.strip()
                isBlank = False
                if line == "":
                    isBlank = True
                sectionMatch = self.section_re.match(line)
                if sectionMatch is not None:
                    if (0 < i < len(lines)-3 and lines[i-1].strip() == "" 
                            and len(line) >= len(lines[i+1].strip())
                            and lines[i+2].strip() == line
                            and lines[i+3].strip() == ""):
                        # top line of double-lined section
                        insertMark = i+3
                    elif (i < len(lines)-1 and lines[i-2].strip() == "" 
                            and len(line) >= len(lines[i-1].strip())
                            and lines[i+1].strip() == ""):
                        # only bottom lined section
                        insertMark = i+1

            if insertMark is None or cutStart is None or cutEnd is None:
                # sys.stderr.write("insert: %s, start: %s, end: %s\n" % (repr(insertMark), repr(cutStart), repr(cutEnd)))
                noChange = False

            if noChange:
                if self._dryrun:
                    sys.stdout.write("# End rewriting. No change to '" + scenePath + "'. Would not modify.\n")
                #else:
                #    sys.stderr.write("No change to '%s'.\n" % scenePath)
                return
            else:
                sys.stderr.write("Changes to '%s'. Will update.\n" % scenePath)

            if self._dryrun:
                out = sys.stdout
            else:
                out = codecs.open(scenePath + ".new", "wt", "utf-8")

            sceneMatch = self.scene_re.match(self.outlineData.get(scene)[0])
            if sceneMatch is None:
                sys.stderr.write("Failed to find match for " + scene)
                return
            title = sceneMatch.group("text")
            ref = sceneMatch.group("ref")
            ref = re.sub("[-._/]+", "-", ref)
            if ref.startswith("-"):
                ref = ref[1:]
            if len(lines) == 0:
                lines.append("")
            for i in range(len(lines)):
                if i == 0 and insertMark is None:
                    out.write(".. _%s:\n\n" % (ref,))
                    s = "=" * len(title)
                    out.write("%s\n%s\n\n" % (title, s,))
                    insertMark = i
                if (cutStart is None and i == insertMark) or cutStart == i:
                    wrote = False
                    eatTitle = True

                    if len(outlineJunk) > 0:
                        out.write("\n".join(outlineJunk))
                        out.write("\n")
                        if cutEnd is None:
                            out.write("\n..\n")

                if cutStart is None or cutEnd is None:
                    pass
                elif cutStart <= i < cutEnd:
                    continue
                out.write(lines[i])

            if not self._dryrun:
                out.close()
            os.rename(scenePath + ".new", scenePath + self.suffix)
        if self._dryrun:
            sys.stdout.write("# end rewriting " + scene + " \n")

    def create_book(self):
        chNum = 0
        chfmt = "%%0%uu" % (len(str(len(self.outline))),)
        bookpath = self.book_toc_path

        if self._dryrun:
            bookfile = sys.stdout
            bookfile.write(".. "+ bookpath + "\n\n")
        else:
            bookfile = codecs.open(bookpath, "wt", "utf-8")

        d = '*' * len(self.book_title)
        bookfile.write(d + "\n")
        bookfile.write(self.book_title + "\n")
        bookfile.write(d + "\n")
        bookfile.write("\n")
        bookfile.write(".. toctree::\n\n")
        for ch in self.outline:
            chNum += 1
            chappath = os.path.join(self.chapter_path,
                                    self.chapter_prefix
                                    + chfmt % (chNum,)
                                    + self.suffix)
            chappath = os.path.relpath(chappath, bookpath)
            bookfile.write("   %s\n" % chappath)
        if not self._dryrun:
            bookfile.close()
            bookfile = None
        return

    def create_chapters(self):
        chNum = 0
        chfmt = "%%0%uu" % (len(str(len(self.outline))),)
        self.termsForChaps = {}
        for ch in self.outline:
            chNum += 1
            chappath = os.path.join(self.chapter_path,
                                    self.chapter_prefix
                                    + chfmt % (chNum,)
                                    + self.suffix)
            title = ch[0]
            d = '*' * len(title)
            self.termsForChaps[chNum] = {}

            if self._dryrun:
                chapfile = sys.stdout
                chapfile.write(".. "+ chappath + "\n\n")
            else:
                chapfile = codecs.open(chappath, "wt", "utf-8")

            chapfile.write(d + "\n")
            chapfile.write(title + "\n")
            chapfile.write(d + "\n")
            chapfile.write("\n")

            need_separator = False
            for scene in ch[1:]:
                scenePath = self.find_path(scene, self.outline_path)
                self.rewrite_scene(scene, ch[0])
                filtered = self.filter_lines(scenePath, self.termsForChaps[chNum])
                if len(filtered) > 0:
                    if need_separator:
                        chapfile.write("----\n\n")
                    need_separator = True
                    if scene in self.epigraphs:
                        need_separator = False
                    chapfile.write("\n".join(filtered))
                    chapfile.write("\n")
            if not self._dryrun:
                chapfile.close()
                chapfile = None
        return

    def gather_terms(self, marker, line, terms={}):
        for term in self.term_re.finditer(line):
            term = term.group(1)
            term = term.lower()
            term = "_book".join(term.split(" (book"))
            term = "".join(term.split(")"))
            term = "".join(term.split("'"))
            term = "-".join(term.split())
            terms[term] = terms.get(term, 0) + 1
            if term not in self.termmap:
                self.termmap[term] = set()
            self.termmap[term].add(marker)

    def filter_lines(self, inPath, terms={}):
        try:
            inFile = codecs.open(inPath + self.suffix, "rtU", "utf-8")
        except IOError:
            # can only happen in _dryrun
            sys.stdout.write("MISSING FILE: " + inPath + "\n\n")
            return

        if self._dryrun:
            sys.stdout.write("# start filtering scene " + inPath + "\n")
        para = None
        lastcol = 0
        eatTilLast = False
        eatTilBlank = False
        addContinuance = False
        lines = inFile.readlines()
        inFile.close()
        skip = 0
        out = []
        marker = os.path.relpath(inPath, self.root)
        for i in range(len(lines)):
            origline = line = lines[i]
            if skip > 0:
                skip -= 1
                continue
            col = 0

            line = line.replace("\t", "        ")
            while len(line) > 0 and line[-1] in "\r\n":
                line = line[:-1]
            while len(line) > col and line[col].isspace():
                col += 1

            line = line.strip()

            sectionMatch = self.section_re.match(line)
            if sectionMatch is not None:
                if (0 < i < len(lines)-3 and lines[i-1].strip() == "" 
                        and line >= len(lines[i+1].strip())
                        and lines[i+2].strip() == line
                        and lines[i+3].strip() == ""):
                    u# top line of double-lined section
                    skip = 3
                    continue
                elif (i < len(lines)-1 and lines[i-2].strip() == "" 
                        and line >= len(lines[i-1].strip())
                        and lines[i+1].strip() == ""):
                    # only bottom lined section
                    para = None
                    skip = 1
                    continue

            self.gather_terms(marker, line, terms)
            isBlank = False
            if len(line) == 0:
                isBlank = True
            if eatTilLast and col > lastcol:
                continue
            elif eatTilLast and isBlank:
                continue
            else:
                eatTilLast = False
                eatTilBlank = False
            if eatTilBlank and not isBlank and col > lastcol:
                continue
            else:
                eatTilBlank = False

            if para is None:
                if isBlank:
                    if len(out) > 1 and out[-1] != "":
                        out.append("")
                elif line.startswith(".. ") and "::" in line:
                    eatTilLast = True
                    continue
                elif line.startswith(".. ") or line == "..":
                    eatTilBlank = True
                    continue
                else:
                    if line.startswith("| "):
                        addContinuance = True
                    para = [line]
            elif isBlank:
                para = self.filter_paragraph(inPath, para)
                self.indent_and_extend(para, lastcol, out)
                if len(out) > 1 and out[-1] != "":
                    out.append("")
                self.build_stats(inPath, para)
                para = None
            elif addContinuance and col > lastcol:
                col = lastcol
                para[-1] = para[-1] + " " + line
            elif col == lastcol:
                if line.startswith("| "):
                    addContinuance = True
                para.append(line)
            else:
                if line.startswith("| "):
                    addContinuance = True
                para = self.filter_paragraph(inPath, para)
                self.indent_and_extend(para, lastcol, out)
                self.build_stats(inPath, para)
                para = None
            lastcol = col
        if para is not None:
            para = self.filter_paragraph(inPath, para)
            self.indent_and_extend(para, lastcol, out)
            if len(out) > 1 and out[-1] != "":
                out.append("")
            self.build_stats(inPath, para)
        i = 0
        while i < len(out) and out[i].strip() == "":
            i += 1
        if marker not in self.stats:
            self.build_stats(inPath, [""])
        out = out[i:]
        if self._dryrun:
            sys.stdout.write("# end filtering scene " + inPath + "\n")
        return out

    def filter_paragraph(self, inPath, para):
        marker = os.path.relpath(inPath, self.root)
        line = "\t".join(para)
        line = self.filter_role(line, marker)
        line = self.filter_a_re(line, self.link_re)
        line = self.filter_a_re(line, self.footnote_re)
        return line.split("\t")

    def filter_a_re(self, line, a_re):
        aMatch = a_re.search(line)
        matches = []
        if aMatch is None:
            return line
        matches = [aMatch]
        while aMatch is not None:
            matches.append(aMatch)
            aMatch = a_re.search(line, aMatch.end())
        nomatches = a_re.sub("\000", line).split("\000")
        for i in range(len(matches)):
            out.append(nomatches[i])
            match = matches[i]
            out.append(match.group("text"))
        out.append(nomatches[-1])
        return "".join(out)

    def filter_role(self, line, marker):
        roleMatch = self.role_re.search(line)
        roles = []
        out = []
        if roleMatch is None:
            return line
        roles = [roleMatch]
        while roleMatch is not None:
            roles.append(roleMatch)
            roleMatch = self.role_re.search(line, roleMatch.end())
        nonrole = self.role_re.sub("\000", line).split("\000")
        for i in range(len(roles)):
            out.append(nonrole[i])
            role = roles[i]
            if role.group("domain") != "":
                # All domains are squashed.
                out.append(role.group("text"))
            elif role.group("ref") == "" and role.group("role") in ("ref", "doc"):
                sys.stdout.write("Warning: Titles must be manually supplied: " + role.group(0) + "\n")
                out.append(role.group("text"))
            elif role.group("role") in ("ref", "doc"):
                out.append(role.group("text"))
            elif role.group("role") in ("term", "keyword"):
                out.append(role.group("text"))
            elif role.group("role") != "":
                out.append(role.group("text"))
            else:
                # no idea...
                out.append(role.group(0))
        if nonrole is not None:
            out.append(nonrole[-1])
        return "".join(out)

    def indent_and_extend(self, para, col, out):
        spacer = " " * col
        for line in para:
            out.append(spacer + line)
        return None

    def build_stats(self, inPath, para):
        marker = os.path.relpath(inPath, self.root)
        if not hasattr(self, "cases"):
            self.cases = {}
        stats = self.stats.get(marker)
        if stats is None:
            stats = {}
            self.stats[marker] = stats
        if len(" ".join(para).strip()) > 0:
            stats["__para__"] = stats.get("__para__", 0) + 1
        stats["__char__"] = (stats.get("__char__", 0) +
            sum([len(x) for x in para]))
        #c = para.count('"')
        #if c % 2 == 1:
        #    para = para + '"'
        # qlist = para.split('"')
        # said = qlist[slice(1, None, 2)]
        # notsaid = qlist[slice(0, None, 2)]
        punctuation = self.word_re.sub(" ", " ".join(para)).split()
        stats["__punc__"] = stats.get("__punc__", set()) | set(punctuation)
        word = 0
        for p in self.word_re.split("\t".join(para)):
            if len(p) == 0:
                continue
            lp = p.lower()
            cp = self.cases.get(lp, p)
            if lp not in self.cases:
                self.cases[lp] = cp
            if lp.islower() and cp != lp and cp != p:
                # cased characters exist 
                # and not already using lowercase version
                # and different casing
                self.convert_case(lp, cp)
            stats[cp] = stats.get(cp,0) + 1
            if p[0].isalnum():
                stats["__wc__"] = stats.get("__wc__", 0) + 1
                word += 1
        if "__wpp__" in stats and word != 0:
            stats["__wpp__"] = (stats.get("__wpp__", 0) + word) / 2.0
        elif word != 0:
            stats["__wpp__"] = word

    def convert_case(self, lowered, last_seen):
        for marker in list(self.stats.keys()):
            stats = self.stats[marker]
            if last_seen in stats:
                stats[lowered] = stats[last_seen]
                del(stats[last_seen])
        self.cases[lowered] = lowered

    def write_stats(self):
        if not hasattr(self, "cases"):
            return
        names = []
        special = []
        words = []
        punc = self.cases.get("__punc__","")
        for lower in list(self.cases.keys()):
            seen = self.cases[lower]
            if lower == seen:
                if lower.startswith("__") and lower.endswith("__"):
                    special.append(seen)
                elif lower not in punc:
                    words.append(seen)
                # `punc` already filled.
            elif seen in self.abbreviations:
                words.append(seen)
            else:
                names.append(seen)
        allstats = {}
        self.stats[self.project] = allstats
        if not hasattr(self, "scenelists"):
            self.scenelists = {}
        scenelist = []
        self.scenelists[self.project] = scenelist
        chapter = 0
        chfmt = "%%0%uu" % (len(str(len(self.outline))),)
        for s in self.outline:
            chapter += 1
            scenes = s[1:]
            scenelist.extend(scenes)
            if len(scenes) > 0:
                chapmark = os.path.join(self.chapter_path,
                                    self.chapter_prefix
                                    + chfmt % (chapter,))
                if chapmark not in self.stats:
                    chstats = {}
                    self.stats[chapmark] = chstats
                chstats = self.stats[chapmark]
                for filname in scenes:
                    if filname[0] == "/":
                        filname = filname[1:]
                        scstats = self.stats.get(filname,{})
                        chstats["__para__"] = chstats.get("__para__", 0) + scstats.get("__para__", 0)
                        chstats["__char__"] = chstats.get("__char__", 0) + scstats.get("__char__", 0)
                        chstats["__wpp__"] = (chstats.get("__wcc__", 0.0) + scstats.get("__wpp__", 0.0)) / 2.0
                        chstats["__wc__"] = chstats.get("__wc__", 0) + scstats.get("__wc__", 0)
                        allstats["__para__"] = allstats.get("__para__", 0) + scstats.get("__para__", 0)
                        allstats["__char__"] = allstats.get("__char__", 0) + scstats.get("__char__", 0)
                        allstats["__wpp__"] = (allstats.get("__wcc__", 0.0) + scstats.get("__wpp__", 0.0)) / 2.0
                        allstats["__wc__"] = allstats.get("__wc__", 0) + scstats.get("__wc__", 0)

        if not hasattr(self, "hitlist"):
            self.hitlist = {}
        for filname in scenelist:
            if filname[0] == "/":
                filname = filname[1:]
            for n in names:
                if n is None:
                    continue
                if n in self.stats.get(filname, []):
                    h = self.hitlist.get(n)
                    if h is None:
                        h = []
                        self.hitlist[n] = h
                    h.append(filname)
        for filname in list(self.stats.keys()):
            if filname.startswith("__"):
                if filname.endswith("__"):
                    filenm = filname[2:-2]
                else:
                    filenm = filname[2:]
            else:
                if filname.endswith("__"):
                    filenm = filname[:-2]
                else:
                    filenm = filname

            st = self.stats.get(filname)
            if st is None:
                sys.stdout.write("%s has no stats\n" % filname)
                continue
            tabpath = os.path.join(self.root, os.path.dirname(filenm), self.statdir, os.path.basename(filenm) + ".dat")
            tabdata = []
            if not os.path.exists(tabpath):
                trytabnm = os.path.basename(filenm)
                trytab = os.path.join(self.root, os.path.dirname(filenm), self.statdir, trytabnm + ".dat")
                while not os.path.exists(trytab) and "-0" in trytabnm:
                    trytabnm = trytabnm.replace("-0","-", 1)
                    trytab = os.path.join(self.root, os.path.dirname(filenm), self.statdir, trytabnm + ".dat")
                if os.path.exists(trytab):
                    with open(trytab, 'rb') as csvfile:
                        reader = UnicodeReader(csvfile)
                        for row in reader:
                            tabdata.append(row)
                    if len(tabdata) > 0:
                        os.unlink(trytab)

            else:
                with open(tabpath, 'rb') as csvfile:
                    reader = UnicodeReader(csvfile)
                    for row in reader:
                        tabdata.append(row)

            headers = ["Date", "Words", "Characters", "Paragraphs", "Words Per Paragraph", "Pages (250)", "Pages (350)", "Word Changes"]
            if len(tabdata) == 0:
                tabdata.append(headers)
            elif len(tabdata[0]) < len(headers):
                tabdata[0] = headers
            st["__date__"] = str(date.today().isoformat())
            st["__pg250__"] = st.get("__wc__",0) / 250.0
            st["__pg350__"] = st.get("__wc__",0) / 350.0
            st["__wchange__"] = st.get("__wc__", 0)
            if len(tabdata) > 1:
                if tabdata[-1][0] == st.get("__date__"):
                    del tabdata[-1]
            lastwc = None
            if len(tabdata) > 1:
                if tabdata[-1][1] == "":
                    lastwc = 0
                else:
                    lastwc = int(tabdata[-1][1])
                st["__wchange__"] = st.get("__wc__", 0) - lastwc

            txtpath = os.path.join(self.root, os.path.dirname(filenm), self.statdir, os.path.basename(filenm) + self.suffix)
            if lastwc is not None and lastwc == st.get("__wc__", 0):
                if os.path.exists(tabpath) and os.path.exists(txtpath):
                    continue
                else:
                    sys.stdout.write("Word count no change, but stat file missing for %s\n" % filenm)
            newrow = []
            for n in ("__date__", "__wc__", "__char__", "__para__", "__wpp__", "__pg250__", "__pg350__", "__wchange__"):
                newrow.append(st.get(n, ""))
            # We could be upgrading the name, so don't force a row
            # when the data hasn't changed.
            if lastwc is None or lastwc != st.get("__wc__", 0):
                tabdata.append(newrow)
            outpath = tabpath + ".new"
            if self._dryrun:
                print("\n# ", tabpath, "\n")
            else:
                if not os.path.isdir(os.path.dirname(outpath)):
                    os.makedirs(os.path.dirname(outpath))
                with open(outpath, 'wb') as csvfile:
                    writer = UnicodeWriter(csvfile)
                    writer.writerows(tabdata)
                os.rename(outpath, tabpath)

            outpath = txtpath
            if not os.path.isdir(os.path.dirname(outpath)):
                os.makedirs(os.path.dirname(outpath))
            if self._dryrun:
                out = sys.stdout
                out.write("\n# %s\n\n" % outpath)
            else:
                out = codecs.open(outpath, "wt", "utf-8")
            for n in ("__date__", "__wc__", "__wchange__", "__pg250__", "__pg350__", "__char__", "__para__", "__wpp__"):
                if n == "__para__":
                    out.write(":Paragraphs: ")
                elif n == "__char__":
                    out.write(":Characters: ")
                elif n == "__wpp__":
                    out.write(":Avg Para WC: ")
                elif n == "__wc__":
                    out.write(":Word count: ")
                elif n == "__date__":
                    out.write(":Date: ")
                elif n == "__pg250__":
                    out.write(":Pages (250w): ")
                elif n == "__pg350__":
                    out.write(":Pages (350w): ")
                elif n == "__wchange__":
                    out.write(":Changes (WC): ")
                else:
                    out.write(":%s: " % n)
                if isinstance(st.get(n), float):
                    out.write("%.3f\n"% st.get(n))
                else:
                    out.write("%s\n"% st.get(n))

            if not self._dryrun:
                out.close()

    def write_term_stats(self):
        if not hasattr(self, "scenelists"):
            self.scenelists = {}
        for term in list(self.termmap.keys()):
            files = set(self.hitlist.get(term, [])) | set(self.termmap[term])
            termpath = os.path.join(self.root, self.statdir, term + self.suffix)
            if not os.path.isdir(os.path.dirname(termpath)):
                os.makedirs(os.path.dirname(termpath))
            if self._dryrun:
                out = sys.stdout
                out.write("\n# %s\n\n" % termpath)
            else:
                out = codecs.open(termpath, "wt", "utf-8")
            for proj in self.projects:
                scenelist = self.scenelists.get(proj,[])
                inproj = False
                for absfil in scenelist:
                    relfil = absfil
                    if absfil[0] == '/':
                        relfil = absfil[1:]
                    else:
                        sys.stdout.write("scenelist contained relative path: %s\n" % (absfil,))
                    if relfil in files:
                        if not inproj:
                            out.write("\n* :doc:`/%s`\n\n" % (proj,))
                            inproj = True
                        out.write("   * :doc:`%s`\n"% (absfil,))
            if not self._dryrun:
                out.close()

    def main(self, argv):
        self.stats = {}
        self.termmap = {}
        self.options = parser.parse_args(argv)
        self._verbose = self.options.verbose
        self._dryrun = self.options.dry_run
        self.ini = self.check_config(self.options)
        if self.ini.has_section("global"):
            if self.ini.has_option("global", "projects"):
                projects = self.ini.get("global", "projects").split()
        if self.options.projects is not None and len(self.options.projects) > 0:
            projects = config.projects
        self.projects = projects
        for project in projects:
            self.config = self.switch_config(self.ini, project)
            self.project = project

            self.outline_path = self.config["outline"]
            self.chapter_path = self.config["chapter-dir"]
            self.chapter_prefix = self.config.get("chapter-prefix",  "chapter-")
            self.chapterstub_path = self.config["chapter-stub-dir"]
            self.chapterstub_prefix = self.config.get("chapter-stub-prefix",  "chapter-")
            self.suffix = self.config.get("suffix", ".txt")
            self.abbreviations = self.config.get("abbreviations","").split()
            self.statdir = self.config.get("stat-dir",".stats")
            self.remove_chapstubs(self.chapterstub_path,
                                  self.chapterstub_prefix, self.suffix)
            self.remove_chapstubs(self.chapter_path,
                                  self.chapter_prefix, self.suffix)
            if not os.path.exists(self.outline_path):
                print("Error: need outline file name.")
                sys.exit(1)
            self.parse_outline_file()
            if not os.path.exists(self.config["chapter-dir"]):
                print("Error: need chapter directory.")
                sys.exit(1)
            self.create_chapter_stubs()
            self.create_chapters()
            self.write_stats()
        self.write_term_stats()

    def remove_chapstubs(self, path, prefix, suffix):
        for f in os.listdir(path):
            full = os.path.join(path, f)
            if not os.path.isfile(full):
                continue
            if not f.startswith(prefix):
                continue
            if not f.endswith(suffix):
                continue
            f = f[len(prefix):-len(suffix)]
            if not f.isdigit():
                self.debug(2, "Unexpected chapter number: %s in %s" %
                      (f, full))
                continue
            if self._dryrun:
                print("Would remove %s" % (full,))
            else:
                self.verbose("Removing %s" % (full,))
                os.unlink(full)
        return

    def check_config(self, options):
        global config_file
        config_name = os.path.expanduser(os.path.join("~", "." + config_file))
        if not os.path.isfile(config_name):
            config_name = None
        c = os.environ.get("SPLITOUTLINE_CONF")
        if c is not None:
            config_name = c
        c = options.config;
        if c is not None:
            config_name = c
        if config_name is None:
            config_name = config_file
        ini = configparser.SafeConfigParser()
        ini.read(config_name)
        return ini

    def switch_config(self, ini, project):
        ret = {}
        if ini.has_section("global"):
            for option in ini.options("global"):
                ret[option] = ini.get("global", option)
        if project is not None:
            if ini.has_section(project):
                for option in ini.options(project):
                    ret[option] = ini.get(project, option)
        if "root" not in ret:
            ret["root"] = os.getcwd()
        self.root = ret["root"]
        return ret

    def find_path(self, ref, curdoc):
        ret = None
        if os.path.isabs(ref):
            ret = os.path.relpath(ref, os.path.sep)
            ret = os.path.join(self.root, ret)
        else:
            ret = os.path.dirname(curdoc)
            ret = os.path.join(ret, ref)
        return ret

def main() {
    locale.setlocale(locale.LC_ALL, '')
    sys.exit(SplitOutline().main(sys.argv[1:]))
}

