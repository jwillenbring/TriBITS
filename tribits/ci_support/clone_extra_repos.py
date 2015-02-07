#!/usr/bin/env python

# @HEADER
# ************************************************************************
#
#            TriBITS: Tribal Build, Integrate, and Test System
#                    Copyright 2013 Sandia Corporation
#
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the Corporation nor the names of the
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SANDIA CORPORATION "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SANDIA CORPORATION OR THE
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ************************************************************************
# @HEADER

from CheckinTestConstants import *
from FindGeneralScriptSupport import *
from GeneralScriptSupport import *
import gitdist


#
# Constants
#

g_extraReposTypes = g_knownTribitsTestRepoTypes
g_extraReposTypeDefault = "Nightly"
g_extraReposTypesDefaulIdx = g_extraReposTypes.index(g_extraReposTypeDefault)

g_extraRerposFileDefault = "cmake/ExtraRepositoriesList.cmake"

g_verbosityLevels = [ "none", "minimal",  "more", "most" ]
g_verbosityLevelDefault = "more"
g_verbosityLevelDefaultIdx = g_verbosityLevels.index(g_verbosityLevelDefault)


#
# Help message
#

# This part can be reused in other scripts that are project-specific
genericUsageHelp = \
r"""
By default, that will clone all the 'Nightly' extra repos that are listed in the
file:

  <projectDir>/"""+g_extraRerposFileDefault+r"""

(other repo types can be selected usng --extra-repos-type).

The list of which repos to clone can "white-list" selected with the option
--extra-repos (see options below for details).  Extra repos can in addition be
"back-listed" using the option --not-extra-repos.

To see the full list of repos that can be cloned, pass in just:

  --skip-clone --verbosity=more

That will print out a table like:

  ------------------------------------------------------------------------------
  | ID | Repo Name  | Repo Dir   | VC  | Repo URL                 | Category   |
  |----|------------|------------|-----|--------------------------|------------|
  |  1 | ExtraRepo1 | ExtraRepo1 | GIT | someurl.com.ExtraRepo1   | Continuous |
  |  2 | ExtraRepo3 | ExtraRepo3 | GIT | someurl3.com:/ExtraRepo3 | Continuous |
  ------------------------------------------------------------------------------

If the git repo server is using gitolite, one can set
--gitolite-root=<gitolite-root> and that will result in git repos being
selected only if the selcted repos are listed in 'ssh <gitolite-root> info'.
This allows one to automatically exclude repos from being cloned that the user
has no permissions to clone.

TIP: After cloning the set of repos, a nice too to use on the repos is
'gitdist'.
"""


usageHelp = r"""clone_extra_repos.py [options]

This script clones one more extra repos from a TriBITS
ExtraRepositoriesList.cmake file.  The standard usage is:

  $ cd base <projectDir>
  $ ./cmake/tribits/ci_support/clone-extra-repos.py

where <projectDir> is the base TriBITS project dir and base git repo.

""" + \
genericUsageHelp


#
# Helper functions
#


def injectCmndLineOptionsInParser(clp, gitoliteRootDefault=""):
  
  clp.add_option(
    "--extra-repos", dest="extraRepos", type="string", default="",
    help="List of names of extra repos to be cloned <extra-repos>" \
      " (i.e. \"repo0,repo1,,...\").  When set to empty '' (the default value)" \
      " then all repos that match <extra-repos-type> listed in <extra-repos-file>" \
      " will be selected.  But the repos listed in <extra-repos> must always" \
      " be a subset of the repos of type <extra-repos-type> selected from" \
      " <extra-repos-file>.   (Default '')" )
  
  clp.add_option(
    "--not-extra-repos", dest="notExtraRepos", type="string", default="",
    help="List of names of extra repos *NOT* to clone (i.e. \"repo0,repo1,...\")." \
      "  (Default '')" )
  
  clp.add_option(
    "--extra-repos-file", dest="extraReposFile", type="string",
     default=g_extraRerposFileDefault,
    help="The file path <extra-repos-file> for the ExtraRepositoriesList.cmake file." \
      "  This can be an absolute or relative path." \
      "  (Default = '"+g_extraRerposFileDefault+"')")

  addOptionParserChoiceOption(
    "--extra-repos-type", "extraReposType",
    g_extraReposTypes , g_extraReposTypesDefaulIdx,
    "Type of extra repositories <extra-repos-type> to select from " \
      "<extra-repos-file>.  When --extra-repos is set, then this arugment" \
      " is ignored.",
    clp )
  
  clp.add_option(
    "--gitolite-root", dest="gitoliteRoot", type="string", default=gitoliteRootDefault,
    help="Gives the root for a gitolite repos <gitolite-root> (e.g. git@<some-url>)." \
      "  If specified, then any git repos with the <gitolite-root> listed as their" \
      " root will only be selected if they are listed with 'R' permissions returned" \
      " from 'ssh <gitolite-root> info'.  (Default = '"+gitoliteRootDefault+"')" )

  clp.add_option(
    "--with-cmake", dest="withCmake", type="string", default="cmake",
    help="CMake executable to use with cmake -P scripts internally (only set" \
    +" by unit testing code).  (Default = 'cmake')")

  addOptionParserChoiceOption(
    "--verbosity", "verbLevel", g_verbosityLevels, g_verbosityLevelDefaultIdx,
    "Verbosity of the script (levels are cumulative):" \
    "  none = no output at all (except for commands with --no-op). " \
    "  minimal = print script args echo and clone commands." \
    "  more = print basic repo include/exclude logic and print repo table." \
    "  most = print output from cmake script called and other detailed info." \
    ,
    clp )

  clp.add_option(
    "--do-clone", dest="doClone", action="store_true",
    help="Do the clone of the selected repos. [default]")
  clp.add_option(
    "--skip-clone", dest="doClone", action="store_false",
    help="Skip the clone of the repos and just show what would be done.",
    default=True )

  clp.add_option(
    "--do-op", dest="doOp", action="store_true",
    help="Do the clone of the selected repos. [default]" )
  clp.add_option(
    "--no-op", dest="doOp", action="store_false",
    help="Skip cloning the repos and just show the clone commands.",
    default=True )
  
  clp.add_option(
    "--show-defaults", dest="showDefaults", action="store_true",
    help="Show the default option values and do nothing at all.",
    default=False )


def getCmndLineOptions():
  from optparse import OptionParser
  clp = OptionParser(usage=usageHelp)
  injectCmndLineOptionsInParser(clp)
  (options, args) = clp.parse_args()
  return options


def isVerbosityLevel(inOptions, testVerbLevel):
  requestedVerbLevelInt = g_verbosityLevels.index(inOptions.verbLevel)
  testVerbLevelInt = g_verbosityLevels.index(testVerbLevel)
  if testVerbLevelInt <= requestedVerbLevelInt:
    return True
  return False


def fwdCmndLineOptions(inOptions, terminator=""):
  cmndLineOpts = \
    "  --extra-repos='"+inOptions.extraRepos+"'"+terminator +  \
    "  --not-extra-repos='"+inOptions.notExtraRepos+"'"+terminator +  \
    "  --extra-repos-file='"+inOptions.extraReposFile+"'"+terminator +  \
    "  --extra-repos-type='"+inOptions.extraReposType+"'"+terminator +  \
    "  --gitolite-root='"+inOptions.gitoliteRoot+"'"+terminator +  \
    "  --with-cmake='"+inOptions.withCmake+"'"+terminator +  \
    "  --verbosity='"+inOptions.verbLevel+"'"+terminator
  if inOptions.doClone:
    cmndLineOpts += "  --do-clone" + terminator
  else:
    cmndLineOpts +="  --skip-clone" + terminator
  if inOptions.doOp:
    cmndLineOpts += "  --do-op" + terminator
  else:
    cmndLineOpts += "  --no-op" + terminator
  return cmndLineOpts 


def echoCmndLineOptions(inOptions):
  print fwdCmndLineOptions(inOptions, " \\\n")


def echoCmndLine(inOptions):

  print ""
  print "**************************************************************************"
  print "Script: clone_extra_repos.py \\"

  echoCmndLineOptions(inOptions)


def getHeaderOutputAndExtraReposDictList(rawOutputFromCmakefile):
  headerOuput = ""
  pythonDictListStr = ""
  processingPythonDict = False
  for line in rawOutputFromCmakefile.split("\n"):
    if line == "*** Extra Repositories Python Dictionary":
      processingPythonDict=True
      continue
    if processingPythonDict:
      pythonDictListStr += (line + "\n")
    else:
      headerOuput += (line + "\n")
  #print "\nheaderOuput:\n\n", headerOuput
  #print "\npythonDictListStr = '"+pythonDictListStr+"'"
  pythonDictList = eval(pythonDictListStr)
  return (headerOuput, pythonDictList)


def getExtraReposDictListFromCmakefile(projectDir, extraReposFile, withCmake,
  extraReposType=g_extraReposTypeDefault, extraRepos="",
  tribitsDir=tribitsDir, verbose=True,
  ):
  cmnd = "\""+withCmake+"\""+ \
    " -DPROJECT_SOURCE_DIR="+projectDir+ \
    " -DTRIBITS_BASE_DIR="+tribitsDir+ \
    " -DEXTRA_REPOS_FILE="+extraReposFile+ \
    " -DENABLE_KNOWN_EXTERNAL_REPOS_TYPE="+extraReposType+ \
    " -DEXTRA_REPOS="+extraRepos+\
    " -DNO_CHECK_FOR_MISSING_EXTRA_REPOS=TRUE"
#  " -DTRIBITS_PROCESS_EXTRAREPOS_LISTS_DEBUG=TRUE"
  cmnd += \
    " -P "+ciSupportDir+"/TribitsGetExtraReposForCheckinTest.cmake"
  rawOutput = getCmndOutput(cmnd, throwOnError=True, getStdErr=True)
  (headerOutput, extraReposPytonDictList) = getHeaderOutputAndExtraReposDictList(rawOutput)
  if verbose:
    print "\n", headerOutput
  return extraReposPytonDictList


def filterExtraReposDictList(extraReposDictList_in, notExtraRepos, verbose=False):
  notExtraReposSet = set(notExtraRepos)
  extraReposDictList = []
  for extraReposDict in extraReposDictList_in:
    extraRepoName = extraReposDict["NAME"]
    if extraRepoName in notExtraReposSet:
      if verbose:
        print "Excluding extra repo '"+extraRepoName+"'!"
    else:
      extraReposDictList.append(extraReposDict)
  return extraReposDictList


def getExtraReposTable(extraReposDictList):

  # Get the lists for each column in the table
  repoIdList = []
  repoNameList = []
  repoDirList = []
  repoVcTypeList = []
  repoUrlList = []
  repoCategoryList = []
  repoId = 1 # Use one-base indexing to match gitdist IDs!
  for extraRepoDict in extraReposDictList:
    repoIdList.append(str(repoId))
    repoNameList.append(extraRepoDict["NAME"])
    repoDirList.append(extraRepoDict["DIR"])
    repoVcTypeList.append(extraRepoDict["REPOTYPE"])
    repoUrlList.append(extraRepoDict["REPOURL"])
    repoCategoryList.append(extraRepoDict["CATEGORY"])
    repoId += 1

  # Create the table
  extraReposTableDictList = [
    { "label":"ID", "align":"R", "fields":repoIdList },
    { "label":"Repo Name", "align":"L", "fields":repoNameList },
    { "label":"Repo Dir", "align":"L", "fields":repoDirList },
    { "label":"VC", "align":"L", "fields":repoVcTypeList },
    { "label":"Repo URL", "align":"L", "fields":repoUrlList },
    { "label":"Category", "align":"L", "fields":repoCategoryList },
    ]
  #print "extraReposTableDictList =", extraReposTableDictList
  
  extraReposTable = gitdist.createAsciiTable(extraReposTableDictList)

  # Return the table
  return extraReposTable


def cloneExtraRepo(inOptions, extraRepoDict):
  repoName = extraRepoDict["NAME"]
  repoDir = extraRepoDict["DIR"]
  repoUrl = extraRepoDict["REPOURL"]
  repoVcType = extraRepoDict["REPOTYPE"]
  verbLevelIsMinimum = isVerbosityLevel(inOptions, "minimal")
  if verbLevelIsMinimum:
    print "\nCloning repo "+repoName+" ..."
  if os.path.exists(repoDir):
    if verbLevelIsMinimum:
      print "\n  ==> Repo dir = '"+repoDir+"' already exists.  Skipping clone!"
    return
  if repoVcType != "GIT":
    print "\n  ==> ERROR: Repo type '"+repoVcType+"' not supported!"
    sys.exit(1)
  cmnd = "git clone "+repoUrl+" "+repoDir
  if inOptions.doOp:
    echoRunSysCmnd(cmnd, timeCmnd=True, verbose=verbLevelIsMinimum)
  elif verbLevelIsMinimum:
    print "\nRunning: "+cmnd


#
# Run the script
#

if __name__ == '__main__':

  #
  # A) Process the command-line input
  #

  inOptions = getCmndLineOptions()
  if isVerbosityLevel(inOptions, "minimal"):
    echoCmndLine(inOptions)
  if inOptions.showDefaults:
    sys.exit(0)

  verbLevelIsMinimal = isVerbosityLevel(inOptions, "minimal")

  #
  # B) Get the list of extra repos
  #

  extraRepoDictList = getExtraReposDictListFromCmakefile(
    projectDir=os.getcwd(),
    extraReposFile=inOptions.extraReposFile,
    extraReposType=inOptions.extraReposType,
    extraRepos=inOptions.extraRepos,
    withCmake=inOptions.withCmake,
    verbose=isVerbosityLevel(inOptions, "most")
    )
  #print "extraRepoDictList =", extraRepoDictList

  #
  # C) Filter the list of extra repos
  #

  if inOptions.notExtraRepos:
    if verbLevelIsMinimal:
      print "\n***"
      print "*** Filtering the set of extra repos based on --not-extra-repos:"
      print "***\n"
    extraRepoDictList = filterExtraReposDictList(
      extraRepoDictList,
      inOptions.notExtraRepos.split(","),
      verbose=verbLevelIsMinimal)

  #
  # D) print out table of repos
  #

  if isVerbosityLevel(inOptions, "more"):

    print "\n***"
    print "*** List of selected extra repos to clone:"
    print "***"
  
    extraReposTable = getExtraReposTable(extraRepoDictList)
    print extraReposTable

  #
  # E) Clone the repos
  #

  if inOptions.doClone:

    if verbLevelIsMinimal:
      print "\n***"
      print "*** Clone the selected extra repos:"
      print "***\n"

    for extraRepoDict in extraRepoDictList:
      cloneExtraRepo(inOptions, extraRepoDict)