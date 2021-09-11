import glob
import subprocess
import json
import datetime
import articleListsMaker
import convert_to_index

def makeArticleDirs(_articleDirYears):
    _articleDirs = []
    for d in _articleDirYears:
        dirs = glob.glob(d+'**/', recursive=False)
        _articleDirs += dirs
    return _articleDirs

def makeAllArticleLists(_articleTopNames, _rootDir):
    for n in _articleTopNames:
        articleListsMaker.mainProcess(n, _rootDir)
    
def getSiteSettings(_jsonPath):
    _json = json.loads(open(_jsonPath, 'r').read())
    _rootDir = _json["rootDir"]
    _publicDirNames = _json["publicDirNames"]
    _articleTopNames = _json["articleTopNames"]
    _articleYears = _json["articleYears"]
    return _rootDir, _publicDirNames, _articleTopNames, _articleYears

# def getArticleTopNames(_jsonPath):
#     _json = json.loads(open(_jsonPath, 'r').read())
#     _articleTopNames = _json["articleTopNames"].split(",")
#     return _articleTopNames

def makeSitemapXml(_rootDir, _allPages):
    # _now = datetime.datetime.now().isoformat().split(".")[0]+"+09:00"
    xmlList = []
    xmlList.append('<?xml version="1.0" encoding="UTF-8"?>')
    xmlList.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">')
    xmlList.append('')
    for p in _allPages:
        _updateDatetime = p[2].split('_')[0]+'T'+p[2].split('_')[1].replace('-',':')+'+09:00'
        # print(_updateDatetime)
        xmlList.append('<url>')
        xmlList.append('  <loc>'+p[0]+'</loc>')
        xmlList.append('  <priority>'+p[1]+'</priority>')
        xmlList.append('  <lastmod>'+_updateDatetime+'</lastmod>')
        xmlList.append('  <changefreq>daily</changefreq>')
        xmlList.append('</url>')
    xmlList.append('')
    xmlList.append('</urlset>')
    xmlList.append('')
    xmlStr = "\n".join(xmlList)
    f = open(rootDir+"/sitemap.xml", 'w')
    f.write(xmlStr)
    f.close()
    print("[Success] sitemap was made!!")


def mainProcess(_rootDir,_topDirs,_publicDirs,_articleTopNames,_articleDirYearsDic):
    articleDirsDic = {}
    for k, v in _articleDirYearsDic.items():
        articleDirsDic.update([(k, makeArticleDirs(v))])
    # blogDirs = makeArticleDirs(_blogDirYears)
    # studyDirs = makeArticleDirs(_studyDirYears)

    makeAllArticleLists(_articleTopNames, _rootDir)
    allPages = []


    for d in _topDirs:
        isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary = 0,0,0
        dfArticleTopTitles, dfKeywordsArticles = None, None
        updateDatetime = convert_to_index.mainProcess(_rootDir, "none", d, isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary, dfArticleTopTitles, dfKeywordsArticles)
        allPages.append([d.replace(rootDir,"https://keitasumiya.net"), "1.0", updateDatetime])

    for d in _publicDirs:
        isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary = 0,1,1
        dfArticleTopTitles, dfKeywordsArticles = None, None
        updateDatetime = convert_to_index.mainProcess(_rootDir, "none", d, isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary, dfArticleTopTitles, dfKeywordsArticles)
        allPages.append([d.replace(rootDir,"https://keitasumiya.net"), "0.8", updateDatetime])

    for k, v in articleDirsDic.items():
        for d in v:
            isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary = 1,1,1
            dfArticleTopTitles, dfKeywordsArticles = convert_to_index.readArticleDfsWithCheck(_rootDir, k, d)
            updateDatetime = convert_to_index.mainProcess(_rootDir, k, d, isAdsNecessary, isSideMenuNecessary, isArticleDatetimeNecessary, dfArticleTopTitles, dfKeywordsArticles)
            allPages.append([d.replace(rootDir,"https://keitasumiya.net"), "0.7", updateDatetime])
    
    makeSitemapXml(rootDir, allPages)


# ==============================================================================================================

if __name__ == "__main__":
    rootDir, publicDirNames, articleTopNames, articleYears = getSiteSettings("convert_settings.json")
    topDirs = [rootDir+"/"]
    publicDirs = [rootDir+"/"+n+"/" for n in publicDirNames]    
    articleDirYearsDic = {}
    for a in articleTopNames:
        _dirs = [rootDir+"/"+a+"/"+y+"/" for y in articleYears[a]]
        articleDirYearsDic.update([(a, _dirs)])

    mainProcess(rootDir,topDirs,publicDirs,articleTopNames,articleDirYearsDic)


