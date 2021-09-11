# python3 convert_to_index.py [root-dir] [article-dir] [isAdsNecessary(1/0)] [isSideMenuNecessary(1/0)] [isArticleDatetimeNecessary(1/0)]
from bs4 import BeautifulSoup
import sys
import os.path
import os
import datetime
import json
import pandas as pd

def getSysArgv(_argv):
    _rootDir = _argv[1]
    _articleTopName = _argv[2]
    _mainDir = _argv[3]
    if _mainDir[-1] != "/":
        _mainDir += "/"
    _isAdsNecessary = int(_argv[4])
    _isSideMenuNecessary = int(_argv[5])
    _isArticleDatetimeNecessary = int(_argv[6])
    return _rootDir, _articleTopName, _mainDir, _isAdsNecessary, _isSideMenuNecessary, _isArticleDatetimeNecessary

def getArticleTopNames(_jsonPath):
    _json = json.loads(open(_jsonPath, 'r').read())
    _articleTopNames = _json["articleTopNames"]
    return _articleTopNames

def readMetaJson(_mainDir, _metaJsonFilename):
    metaJsonPath = _mainDir + _metaJsonFilename
    _metaJson = json.loads(open(metaJsonPath, 'r').read())
    return _metaJson

def updateMetaJson(_mainDir, _mainArticleFilename, _metaJsonFilename):
    _statResult = os.stat(_mainDir + _mainArticleFilename)
    _dt = datetime.datetime.fromtimestamp(_statResult.st_mtime)
    _dtStr = _dt.strftime('%Y-%m-%d_%H-%M-%S')
    _metaJson = readMetaJson(_mainDir, _metaJsonFilename)
    _metaJson['update-datetime'] = _dtStr

    with open(_mainDir+_metaJsonFilename, 'w') as f:
        json.dump(_metaJson, f, indent=4, ensure_ascii=False)


def readArticleDfsWithCheck(_rootDir, _articleTopName, _mainDir):
    # _articleDirFromRoot = os.path.relpath(_mainDir, _rootDir)
    # _articleDirFromRootSplited = _articleDirFromRoot.split("/")
    # print(_articleDirFromRootSplited)
    # if len(_articleDirFromRootSplited) == 3 and _articleDirFromRootSplited[0] == "blog":
    #     _dfArticleTopTitles, _dfKeywordsArticles = readArticleDfs("blog")
    # elif len(_articleDirFromRootSplited) == 3 and _articleDirFromRootSplited[0] == "study":
    #     _dfArticleTopTitles, _dfKeywordsArticles = readArticleDfs("study")
    articleTopNames = getArticleTopNames("convert_settings.json")
    if _articleTopName in articleTopNames:
        _dfArticleTopTitles, _dfKeywordsArticles = readArticleDfs(_articleTopName)
    else:
        _dfArticleTopTitles = None
        _dfKeywordsArticles = None

    return _dfArticleTopTitles, _dfKeywordsArticles


def readArticleDfs(_articleTopName):
    _dfArticleTopTitles = pd.read_excel("out/articleLists_byYear_"+_articleTopName.replace("/","-")+".xlsx")
    _dfArticleTopTitles = _dfArticleTopTitles.set_index("dirFromArticleTop")
    _dfArticleTopTitles = _dfArticleTopTitles.fillna("")

    _dfKeywordsArticles = pd.read_excel("out/articleLists_byKeywords_"+_articleTopName.replace("/","-")+".xlsx")
    _dfKeywordsArticles = _dfKeywordsArticles.set_index("keyword")
    return _dfArticleTopTitles, _dfKeywordsArticles

def processForEachArticle(_articleDirFromRoot, _articleTopName, _tmplPrevNext, _tmplArticleInfo, _tmplRelatedArticles, _dfArticleTopTitles, _dfKeywordsArticles, _metaJson, _rootDirFromArticle):
    articleDirFromArticleTop = _articleDirFromRoot.replace(_articleTopName+"/","")
    _tmplPrevNext = _tmplPrevNext.replace('articleTopDir', _articleTopName)
    _tmplPrevNext = _tmplPrevNext.replace('prevDirFromArticleTop1234567890', _dfArticleTopTitles.loc[articleDirFromArticleTop]["prevDirFromArticleTop"])
    _tmplPrevNext = _tmplPrevNext.replace('nextDirFromArticleTop1234567890', _dfArticleTopTitles.loc[articleDirFromArticleTop]["nextDirFromArticleTop"])
    if _dfArticleTopTitles.index.get_loc(articleDirFromArticleTop) == 0:
        _tmplPrevNext = _tmplPrevNext.replace('prevTitle1234567890', _articleTopName.capitalize())
    else:
        _tmplPrevNext = _tmplPrevNext.replace('prevTitle1234567890', _dfArticleTopTitles.loc[articleDirFromArticleTop]["prevRawTitle"])
    if _dfArticleTopTitles.index.get_loc(articleDirFromArticleTop) == len(_dfArticleTopTitles) - 1:
        _tmplPrevNext = _tmplPrevNext.replace('nextTitle1234567890', _articleTopName.capitalize())
    else:
        _tmplPrevNext = _tmplPrevNext.replace('nextTitle1234567890', _dfArticleTopTitles.loc[articleDirFromArticleTop]["nextRawTitle"])
    
    _tmplArticleInfo = _tmplArticleInfo.replace('<!-- <b>Key: </b>keywords1234567890 -->', '<b>Key: </b>'+_metaJson["keywords"]).replace('updateDatetimeShow1234567890', 'updateDatetimeShow1234567890,')
    keywords = sorted(_metaJson["keywords"].split(','), key=str.lower)
    relatedArticleLists = []
    for k in keywords:
        relatedArticleLists.append(_dfKeywordsArticles.loc[k]["relatedArticles"])
    relatedArticlesStr = "\n".join(relatedArticleLists).replace("articleTopDir",_rootDirFromArticle+"/"+_articleTopName)
    _tmplRelatedArticles = _tmplRelatedArticles.replace("relatedArticles1234567890", relatedArticlesStr)
    return _tmplPrevNext, _tmplArticleInfo, _tmplRelatedArticles

def readMainArticleHtml(_mainPath):
    _soup = BeautifulSoup(open(_mainPath), "html.parser")
    # _articleBody = _soup.find("body")
    _articleBody = _soup.select('#write')[0]
    _mainArticle = "\n".join(map(lambda x: "                        " + str(x), _articleBody.contents))
    return _soup, _articleBody, _mainArticle

def makeSideLi(_articleBody):
    liStrs=[]
    targethTags = ["h1","h2","h3","h4","h5","h6"]
    for c in range(len(_articleBody.contents)):
        tmpHtml = BeautifulSoup(str(_articleBody.contents[c]), "html.parser")
        for t in range(len(targethTags)):
            tmpTagFind = tmpHtml.find(targethTags[t])
            if tmpTagFind!=None:
                liStr = "                        "
                liStr += '<li class="side-li-'+targethTags[t]+'"><a href="#'+str(tmpTagFind["id"])+'">'+str(tmpTagFind.text)+'</a></li>'
                liStrs.append(liStr)
    _sideLi = "\n".join(liStrs)
    return _sideLi

def updateArticleMetainfo(_soup, _metaJson, _tmplHead, _tmplArticleInfo):
    articleTitle = _soup.find("h1").text
    _tmplHead = _tmplHead.replace('title1234567890', articleTitle)
    _tmplHead = _tmplHead.replace('description1234567890', _metaJson["description"])
    _tmplHead = _tmplHead.replace('keywords1234567890', _metaJson["keywords"])
    _tmplArticleInfo = _tmplArticleInfo.replace('publishedDatetimeTag1234567890', _metaJson["published-datetime"].split('_')[0])
    _tmplArticleInfo = _tmplArticleInfo.replace('publishedDatetimeShow1234567890', _metaJson["published-datetime"].split('_')[0])
    _tmplArticleInfo = _tmplArticleInfo.replace('updateDatetimeShow1234567890', _metaJson["update-datetime"].split('_')[0])
    return _tmplHead, _tmplArticleInfo


def mainProcess(_rootDir, _articleTopName, _mainDir, _isAdsNecessary, _isSideMenuNecessary, _isArticleDatetimeNecessary, _dfArticleTopTitles, _dfKeywordsArticles):
    articleTopNames = getArticleTopNames("convert_settings.json")

    rootDirFromArticle = os.path.relpath(_rootDir, _mainDir)

    templatesDir = "templates/"
    templatesPath = templatesDir + "templates.html"
    templatesStr = open(templatesPath, 'r').read()
    templatesStrList = templatesStr.split("<!-- ==========division-line_1234567890_abcdefghijklmn====================================================== -->")
    tmplHtmlStart = templatesStrList[0]
    tmplHead = templatesStrList[1]
    tmplBodyStart = templatesStrList[2]
    tmplHeaderStart = templatesStrList[3]
    tmplHeaderSiteNav = templatesStrList[4]
    tmplHeaderArticleNavStart = templatesStrList[5]
    tmplHeaderArticleNavEnd = templatesStrList[6]
    tmplHeaderEnd = templatesStrList[7]
    tmplMainStart = templatesStrList[8]
    tmplArticleStart = templatesStrList[9]
    tmplArticleInfo = templatesStrList[10]
    tmplTyporaStart = templatesStrList[11]
    tmplTyporaEnd = templatesStrList[12]
    tmplPrevNext = templatesStrList[13]
    tmplRelatedArticles = templatesStrList[14]
    tmplArticleEnd = templatesStrList[15]
    tmplSideMenuStart = templatesStrList[16]
    tmplSideMenuMainStart = templatesStrList[17]
    tmplSideMenuIndexStart = templatesStrList[18]
    tmplSideMenuIndexEnd = templatesStrList[19]
    tmplSideMenuForm = templatesStrList[20]
    tmplAdSide = templatesStrList[21]
    tmplSideMenuMainEnd = templatesStrList[22]
    tmplSideMenuEnd = templatesStrList[23]
    tmplMainEnd = templatesStrList[24]
    tmplAdMain = templatesStrList[25]
    tmplFooterStart = templatesStrList[26]
    tmplFooterMain = templatesStrList[27]
    tmplAdSearch = templatesStrList[28]
    tmplFooterEnd = templatesStrList[29]
    tmplBodyEnd = templatesStrList[30]
    tmplHtmlEnd = templatesStrList[31]

    mainArticleFilename = "index-article.html"
    metaJsonFilename = "index-article-meta.json"
    outputFilename = "index.html"
    mainPath = _mainDir + mainArticleFilename

    updateMetaJson(_mainDir, mainArticleFilename, metaJsonFilename)
    metaJson = readMetaJson(_mainDir, metaJsonFilename)

    articleDirFromRoot = os.path.relpath(_mainDir, _rootDir)
    articleDirFromRootSplited = articleDirFromRoot.split("/")

    if _articleTopName in articleTopNames:
        tmplPrevNext, tmplArticleInfo, tmplRelatedArticles = processForEachArticle(articleDirFromRoot, _articleTopName, tmplPrevNext, tmplArticleInfo, tmplRelatedArticles, _dfArticleTopTitles, _dfKeywordsArticles, metaJson, rootDirFromArticle)
    # if len(articleDirFromRootSplited) == 3 and articleDirFromRootSplited[0] == "blog":
    #     tmplPrevNext, tmplArticleInfo, tmplRelatedArticles = processForEachArticle(articleDirFromRoot, "blog", tmplPrevNext, tmplArticleInfo, tmplRelatedArticles, _dfArticleTopTitles, _dfKeywordsArticles, metaJson, rootDirFromArticle)
    # elif len(articleDirFromRootSplited) == 3 and articleDirFromRootSplited[0] == "study":
    #     tmplPrevNext, tmplArticleInfo, tmplRelatedArticles = processForEachArticle(articleDirFromRoot, "study", tmplPrevNext, tmplArticleInfo, tmplRelatedArticles, _dfArticleTopTitles, _dfKeywordsArticles, metaJson, rootDirFromArticle)
    else:
        tmplPrevNext = ""
        tmplHead = tmplHead.replace('<link rel="stylesheet" href="rootDir/css/prev-next.css">', '')
        tmplHead = tmplHead.replace('<link rel="stylesheet" href="rootDir/css/related-articles.css">', '')
        tmplRelatedArticles = ""

    soup, articleBody, mainArticle = readMainArticleHtml(mainPath)
    sideLi = makeSideLi(articleBody)
    tmplHead, tmplArticleInfo = updateArticleMetainfo(soup, metaJson, tmplHead, tmplArticleInfo)


    if _isAdsNecessary == 0 :
        tmplAdMain = ""
        tmplAdSide = ""
        # tmplHead = tmplHead.replace('<link rel="stylesheet" href="rootDir/css/ad.css">', '')

    if _isSideMenuNecessary == 0:
        tmplHead = tmplHead.replace('<link rel="stylesheet" href="rootDir/css/sidemenu.css">', '')
        tmplHeaderArticleNavStart = ""
        tmplHeaderArticleNavEnd = ""
        tmplSideMenuStart = ""
        tmplSideMenuMainStart = ""
        tmplSideMenuIndexStart = ""
        sideLi = ""
        tmplSideMenuIndexEnd = ""
        tmplSideMenuForm = ""
        tmplSideMenuMainEnd = ""
        tmplSideMenuEnd = ""

    if _isArticleDatetimeNecessary == 0:
        tmplArticleInfo = ""

    tmplHead = tmplHead.replace('rootDir', rootDirFromArticle)
    tmplHeaderSiteNav = tmplHeaderSiteNav.replace('rootDir', rootDirFromArticle)
    tmplFooterMain = tmplFooterMain.replace('rootDir', rootDirFromArticle)
    tmplPrevNext = tmplPrevNext.replace('rootDir', rootDirFromArticle)

    merged = (tmplHtmlStart
            +tmplHead
            +tmplBodyStart
            +tmplHeaderStart
            +tmplHeaderSiteNav
            +tmplHeaderArticleNavStart
            +sideLi
            +tmplHeaderArticleNavEnd
            +tmplHeaderEnd
            +tmplMainStart
            +tmplArticleStart
            +tmplPrevNext
            +tmplArticleInfo
            +tmplTyporaStart
            +mainArticle
            +tmplTyporaEnd
            +tmplPrevNext
            +tmplRelatedArticles
            +tmplArticleEnd
            +tmplSideMenuStart
            +tmplSideMenuMainStart
            +tmplSideMenuIndexStart
            +sideLi
            +tmplSideMenuIndexEnd
            +tmplSideMenuForm
            +tmplAdSide
            +tmplSideMenuMainEnd
            +tmplSideMenuEnd
            +tmplMainEnd
            +tmplAdMain
            +tmplFooterStart
            +tmplFooterMain
            +tmplAdSearch
            +tmplFooterEnd
            +tmplBodyEnd
            +tmplHtmlEnd )
    # merged = merged.replace("<li><p>", "<li>").replace("</p>\n</li>","</li>")

    f = open(_mainDir+outputFilename, 'w')
    f.write(merged)
    f.close()

    print("[Success] converted for " + _mainDir)

    return metaJson["update-datetime"]





# ==============================================================================================================

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("[Error] do as followings:")
        print("python3 convert_to_index.py [root-dir] [article-top-name] [article-dir] [isAdsNecessary(1/0)] [isSideMenuNecessary(1/0)] [isArticleDatetimeNecessary(1/0)]")
        print("python3 convert_to_index.py ../public blog ../public/blog/2021/hogehoge 0 1 1")
        print("python3 convert_to_index.py ../public none ../public 0 0 1")

    else:
        rootDir, articleTopName, mainDir, isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary = getSysArgv(sys.argv)
        dfArticleTopTitles, dfKeywordsArticles = readArticleDfsWithCheck(rootDir, articleTopName, mainDir)
        mainProcess(rootDir, articleTopName, mainDir, isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary, dfArticleTopTitles, dfKeywordsArticles)


