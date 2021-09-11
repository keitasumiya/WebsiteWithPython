from bs4 import BeautifulSoup
import glob
import subprocess
import os
import os.path
import json
from datetime import datetime as dt
import pandas as pd
import numpy as np
import collections

def flatten(l):
    for el in l:
        if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def listDir(_path):
    files = os.listdir(_path)
    files_dirTmp = [f for f in files if os.path.isdir(os.path.join(_path, f))]
    files_dir = []
    for f in files_dirTmp:
        if isInt(f):
            files_dir.append(f)
    files_dir = sorted(files_dir, key=str.lower)
    # print(files_dir)
    return files_dir

def listRelativeYearPaths(_topDirPath, _articleTopName, _years):
    _relativePaths = []
    for y in _years:
        _relativePaths.append(_topDirPath+'/'+_articleTopName+'/'+y+'/')
    return _relativePaths

def isInt(s):
    try:
        int(s, 10)
    except ValueError:
        # print("[TryError] " + s + " is not integer!!")
        return False
    else:
        # print("[TrySccss] " + s + " is integer!!")
        return True

def makeArticleDirs(_articleTopDirYears):
    _articleDirs = []
    for d in _articleTopDirYears:
        # print(d)
        _year = d.split("/")[-2]
        if isInt(_year):
            dirs = glob.glob(d+'**/', recursive=False)
            _articleDirs += dirs
    return _articleDirs

def makeTitleLists(_articleDirs, _articleTopDir):
    _titleLists = []
    for d in _articleDirs:
        dirFromArticleTop = os.path.relpath(d, _articleTopDir)

        soup = BeautifulSoup(open(d+"index-article.html"), "html.parser")
        title = soup.find("h1").text

        metaJsonFilename = "index-article-meta.json"
        metaJsonPath = d + metaJsonFilename
        metaJson = json.loads(open(metaJsonPath, 'r').read())
        publishedDatetimeStr = metaJson["published-datetime"]
        publishedDatetime = dt.strptime(publishedDatetimeStr, '%Y-%m-%d_%H-%M-%S')
        publishedYear = publishedDatetime.strftime("%Y")
        publishedYMD = publishedDatetime.strftime("%Y-%m-%d")

        keywords = metaJson["keywords"].split(",")
        description = metaJson["description"]

        # titleList = "- ["+publishedYMD+": "+title+"]("+dirFromArticleTop+")"
        titleList = "- ["+title+"__"+publishedYMD+"]("+dirFromArticleTop+")"
        _titleLists.append([publishedYMD,publishedDatetime,titleList,publishedYear,keywords,description,title,dirFromArticleTop])
    return _titleLists

def makeDfTitlesSorted(_titleLists, _articleTopName):
    _clmns = ["publishedYMD","datetime","title","year","keywords","description","rawTitle","dirFromArticleTop"]
    dfTitles = pd.DataFrame(_titleLists, columns=_clmns)
    _dfTitlesSorted = dfTitles.sort_values("datetime").copy()
    _dfTitlesSorted.index = range(len(_dfTitlesSorted))

    rawTitleList = _dfTitlesSorted["rawTitle"].tolist()
    dirFromArticleTopList = _dfTitlesSorted["dirFromArticleTop"].tolist()
    nextRawTitleList = rawTitleList[1:] + [""]
    prevRawTitleList = [""] + rawTitleList[:-1]
    nextDirFromArticleTopList = dirFromArticleTopList[1:] + [""]
    prevDirFromArticleTopList = [""] + dirFromArticleTopList[:-1]
    dfTitlesPrevNext = pd.DataFrame([prevRawTitleList,prevDirFromArticleTopList,nextRawTitleList,nextDirFromArticleTopList]).T
    dfTitlesPrevNext.columns = ["prevRawTitle","prevDirFromArticleTop","nextRawTitle","nextDirFromArticleTop"]
    # print(dfTitlesPrevNext)

    _dfTitlesSorted = pd.concat([_dfTitlesSorted, dfTitlesPrevNext], axis=1)
    _dfTitlesSorted.to_excel("out/articleLists_byYear_"+_articleTopName.replace("/","-")+".xlsx", index=False)

    return _dfTitlesSorted

def makeKeywordsList(_dfTitlesSorted):
    keywordsTmp = list(flatten(_dfTitlesSorted["keywords"].values.tolist()))
    _keywordsList = sorted(list(set(keywordsTmp)), key=str.lower)
    return _keywordsList

def makeTitleListsSelectedByKeywordsForMd(_dfTitlesSorted, _keywordsList):
    _titleListsSelectedKeywords = ["## Keywords"]
    for k in _keywordsList:
        TFList = []
        for k1 in _dfTitlesSorted["keywords"].tolist():
            TFList.append(k in k1)
        keywordTFSeries = pd.Series(TFList)
        _titleListsSelectedKeywords += ["### "+k]
        _titleListsSelectedKeywords += _dfTitlesSorted[keywordTFSeries]["title"].values.tolist()
        _titleListsSelectedKeywords += [""]
    _titleListsSelectedKeywords += ["",""]
    return _titleListsSelectedKeywords

def makeTitleListsSelectedByKeywordsForHtml(_dfTitlesSorted, _keywordsList):
    _titleListsSelectedKeywordsForHtml = []
    for k in _keywordsList:
        TFList = []
        for k1 in _dfTitlesSorted["keywords"].tolist():
            TFList.append(k in k1)
        keywordTFSeries = pd.Series(TFList)
        _titleListsSelectedKeywordsForHtmlTmp = ["<h3>"+k+"</h3>","<ul>"]
        tmpPublishedYMDList = _dfTitlesSorted[keywordTFSeries]["publishedYMD"].values.tolist()
        tmpRawTitleList = _dfTitlesSorted[keywordTFSeries]["rawTitle"].values.tolist()
        tmpDirFromArticleTopList = _dfTitlesSorted[keywordTFSeries]["dirFromArticleTop"].values.tolist()
        for i in range(len(tmpRawTitleList)):
            _titleListsSelectedKeywordsForHtmlTmp += ['<li><a href="articleTopDir/'+tmpDirFromArticleTopList[i]+'">'+tmpPublishedYMDList[i]+': '+tmpRawTitleList[i]+'</a></li>']
        _titleListsSelectedKeywordsForHtmlTmp += ["</ul>",""]
        _titleListsSelectedKeywordsForHtml.append([k, "\n".join(_titleListsSelectedKeywordsForHtmlTmp)])
    return _titleListsSelectedKeywordsForHtml

def outputExcelOfTitleListsForHtml(_titleListsSelectedKeywordsForHtml,_articleTopName):
    dfTitlesKeywords = pd.DataFrame(_titleListsSelectedKeywordsForHtml)
    dfTitlesKeywords.columns = ["keyword","relatedArticles"]
    dfTitlesKeywords.to_excel("out/articleLists_byKeywords_"+_articleTopName.replace("/","-")+".xlsx", index=False)

def makeTitleListsSortedByYearsForMd(_dfTitlesSorted, _years):
    _dfTitlesSorted = _dfTitlesSorted.sort_values("datetime", ascending=False).copy()
    _dfTitlesSorted.index = range(len(_dfTitlesSorted))
    _years = sorted(_years, reverse=True)

    _titleListsSortedYears = ["## Time Series"]
    for y in _years:
        dfTmp = _dfTitlesSorted[_dfTitlesSorted["year"] == y].copy()
        titleListsSortedAnYear = dfTmp["title"].values.tolist()
        _titleListsSortedYears += ["### "+y]
        _titleListsSortedYears += titleListsSortedAnYear
        _titleListsSortedYears += [""]
    _titleListsSortedYears += ["",""]
    return _titleListsSortedYears

def makeTitleListsForArticleTopMd(_articleTopName, _titleListsSortedYears, _titleListsSelectedKeywords):
    _titleListsForArticleTop = ["# "+_articleTopName.capitalize(), "", ""]
    _titleListsForArticleTop += _titleListsSortedYears + _titleListsSelectedKeywords
    return _titleListsForArticleTop

def outputTitleListsForArticleTopMd(_titleListsForArticleTop, _articleTopName, _articleTopDir):
    titleListsMerged = "\n".join(_titleListsForArticleTop)
    outputFilename = "out/articleLists_topPage_"+_articleTopName.replace("/","-")+".md"
    f = open(outputFilename, 'w')
    f.write(titleListsMerged)
    f.close()
    outputFilename = _articleTopDir+"index-article.md"
    f = open(outputFilename, 'w')
    f.write(titleListsMerged)
    f.close()

def mainProcess(_articleTopName, _topDirPath):
    print("[Making...] start to make "+_articleTopName+" lists")
    articleTopDir = _topDirPath+'/'+_articleTopName+'/'
    years = listDir(articleTopDir)
    articleTopDirYears = listRelativeYearPaths(_topDirPath, _articleTopName, years)
    articleDirs = makeArticleDirs(articleTopDirYears)
    titleLists = makeTitleLists(articleDirs, articleTopDir)
    dfTitlesSorted = makeDfTitlesSorted(titleLists, _articleTopName)
    keywordsList = makeKeywordsList(dfTitlesSorted)
    # Markdown
    titleListsSelectedKeywords = makeTitleListsSelectedByKeywordsForMd(dfTitlesSorted, keywordsList)
    titleListsSortedYears = makeTitleListsSortedByYearsForMd(dfTitlesSorted, years)
    titleListsForArticleTop = makeTitleListsForArticleTopMd(_articleTopName, titleListsSortedYears, titleListsSelectedKeywords)
    outputTitleListsForArticleTopMd(titleListsForArticleTop, _articleTopName, articleTopDir)
    # html
    titleListsSelectedKeywordsForHtml = makeTitleListsSelectedByKeywordsForHtml(dfTitlesSorted, keywordsList)
    outputExcelOfTitleListsForHtml(titleListsSelectedKeywordsForHtml, _articleTopName)
    print("[Success] end to make "+_articleTopName+" lists")

# ====================================================================================================================

if __name__ == "__main__":
    articleTopName = "blog"
    topDirPath = '../public'
    mainProcess(articleTopName, topDirPath)

