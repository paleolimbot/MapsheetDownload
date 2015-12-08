'''
Created on Sep 26, 2013

@author: Dewey Dunnington <dewey@fishandwhistle.net>
'''
from __future__ import division

__MAP_SERIES_N_OF_80 = (("910", "780", "560", "340", "120"), #Series row 10 and 11
                      (None, "781", "561", "341", "121"))

__MAP_250K = (("D", "C", "B", "A"),
            ("E", "F", "G", "H"),
            ("L", "K", "J", "I"),
            ("M", "N", "O", "P"))
__MAP_250K_N_OF_68 = (("B", "A"),
                    ("C", "D"),
                    ("F", "E"),
                    ("G", "H"))
__MAP_50K = ((4, 3, 2, 1),
            (5, 6, 7, 8),
            (12, 11, 10, 9),
            (13, 14, 15, 16))



def __indexXY(value, valueMap):
    for y in range(len(valueMap)):
        xVals = valueMap[y]
        for x in range(len(xVals)):
            if xVals[x] == value:
                return x, y
    return None

def __widthAndOffset250(lat):
    if lat >= 80.0:
        #width is 8 degrees north of 80th parallel, grid starts 8 degrees east of 144 west
        width = 8.0
        offset = 8.0
    elif lat >= 68.0:
        width = 4.0
        offset = 0
    else:
        width = 2.0
        offset = 0
    return width, offset

def __widthAndOffsetSeries(lat):
    if lat >= 80.0:
        #width is 16 degrees north of 80th parallel, grid starts 8 degrees east of 144 west
        width = 16.0
        offset = 8.0
    else:
        width = 8.0
        offset = 0
    return width, offset 

def __mapsPerSeries(tile250kY):
    if tile250kY >= 28:
        #2 maps per series north of 68
        return 2
    else:
        return 4

def __tileSeriesY(lat):
    return int((lat - 40) / 4.0)

def __tileSeriesX(lon, lat):
    width, offset = __widthAndOffsetSeries(lat)
    return int((lon + (144 - offset)) / width)

def __tileSeries(lon, lat):
    return (__tileSeriesX(lon, lat), __tileSeriesY(lat))

def __boundsSeries(tile):
    minlat = tile[1] * 4.0 + 40
    width, offset = __widthAndOffsetSeries(minlat)
    minlon = -144 + tile[0] * width + offset
    return (minlon, minlon + width, minlat, minlat + 4.0)

def __ntsIdSeries(tile):
    if tile[1] >= 10 and tile[0] <= 4:
        return __MAP_SERIES_N_OF_80[tile[1]-10][tile[0]]
    else:
        seriesRow = str(tile[1])
        seriesX = 11 - tile[0]
        seriesColumn = str(seriesX)
        if len(seriesColumn) == 1:
            seriesColumn = "0" + seriesColumn
        return seriesColumn + seriesRow

def __tileSeriesById(series):
    if len(series) >= 2:
        result = __indexXY(series, __MAP_SERIES_N_OF_80)
        if result is not None:
            seriesX = result[0]
            seriesY = result[1] + 10
        else:
            seriesY = int(series[-1:])
            seriesX = 11 - int(series[:-1])
        return (seriesX, seriesY)
    else:
        return None

def __validTileSeries(tile):
    if tile[1] == 0:
        if 7 <= tile[0] <= 11:
            return True
    elif tile[1] == 1:
        if 6 <= tile[0] <= 11 or tile[0] == 1 or tile[0] == 2:
            return True
    elif 2 <= tile[1] <= 4:
        if 0 <= tile[0] <= 11:
            return True
    elif 5 <= tile[1] <= 8:
        if 0 <= tile[0] <= 10:
            return True
    elif tile[1] == 9:
        if 0 <= tile[0] <= 9:
            return True
    elif tile[1] == 10:
        if 0 <= tile[0] <= 4:
            return True
    elif tile[1] == 11:
        if 1 <= tile[0] <= 4:
            return True
    return False


def __tileSeriesFromTile250(tile250k):
    mapsPerSeries = __mapsPerSeries(tile250k[1])
    tileX = int(tile250k[0] / mapsPerSeries)
    tileY = int(tile250k[1] / 4.0)
    return tileX, tileY

def __tile250Y(lat):
    return int(lat-40.0)

def __tile250X(lon, lat):
    width, offset = __widthAndOffset250(lat)
    return int((lon + (144 - offset)) / width)

def __tile250(lon, lat):
    return __tile250X(lon, lat), __tile250Y(lat)   

def __bounds250(tile):
    minlat = tile[1] + 40.0
    width, offset = __widthAndOffset250(minlat)
    minlon = -144.0 + offset + (tile[0] * width)
    maxlat = minlat + 1.0
    maxlon = minlon + width
    return (minlon, maxlon, minlat, maxlat)

def __ntsId250(tile250k):
    seriesX, seriesY = __tileSeriesFromTile250(tile250k)
    seriesNumber = __ntsIdSeries((seriesX, seriesY))
    seriesMinYTile = int(seriesY * 4)
    yTileInSeries = tile250k[1] - seriesMinYTile
    
    mapsPerSeries = __mapsPerSeries(tile250k[1])
    seriesMinXTile = int(seriesX * mapsPerSeries)
    xTileInSeries = tile250k[0] - seriesMinXTile
    
    if seriesY >= 10:
        areaLetter = __MAP_250K_N_OF_68[yTileInSeries][xTileInSeries]
        return seriesNumber, areaLetter
    
    if seriesY >= 7:
        areaLetter = __MAP_250K_N_OF_68[yTileInSeries][xTileInSeries]
    else:
        areaLetter = __MAP_250K[yTileInSeries][xTileInSeries]
    seriesRow = str(seriesY)
    seriesX = 11 - seriesX
    seriesColumn = str(seriesX)
    if len(seriesColumn) == 1:
        seriesColumn = "0" + seriesColumn
    seriesNumber = seriesColumn + seriesRow
    return seriesNumber, areaLetter

def __tile250ById(ntsId):
    if len(ntsId) < 2:
        raise ValueError, "Not enough arguments in ntsId to create 50k tile"
    seriesTile = __tileSeriesById(ntsId[0])
    area = ntsId[1].upper()
    if seriesTile is not None:
        seriesX, seriesY = seriesTile
        if seriesY >= 7:
            valueMap = __MAP_250K_N_OF_68
        else:
            valueMap = __MAP_250K
        result = __indexXY(area, valueMap)
        if result is not None:
            tileY = seriesY * 4 + result[1]
            mapsPerSeries = __mapsPerSeries(tileY)
            tileX = seriesX * mapsPerSeries + result[0]
            return tileX, tileY
        else:
            raise ValueError, "Invalid area passed to __tile250ById()"

    else:
        raise ValueError, "Invalid series passed to __tile250ById()"

def __tiles250ByTileSeries(tileSeries):
    minYTile = tileSeries[1] * 4
    mapsPerSeries = __mapsPerSeries(minYTile)
    minXTile = tileSeries[0] * mapsPerSeries
    outList = []
    for tileX in range(minXTile, minXTile+4):
        for tileY in range(minYTile, minYTile+4):
            outList.append((tileX, tileY))
    return outList

def __tile50ById(ntsId):
    tile250k = __tile250ById(ntsId)
    if len(ntsId) < 3:
        raise ValueError, "Not enough arguments in ntsId to create 50k tile"
    result = __indexXY(int(ntsId[2]), __MAP_50K)
    if result is not None:
        tileY = int(tile250k[1] * 4 + result[1])
        tileX = int(tile250k[0] * 4 + result[0])
        return tileX, tileY
    else:
        raise ValueError, "Invalid mapsheet passed to __tile250ById()"

def __tile250FromTile50(tile50k):
    tileX = int(tile50k[0] / 4.0)
    tileY = int(tile50k[1] / 4.0)
    return tileX, tileY


def __tile50Y(lat):
    tile250kY = __tile250Y(lat)
    latDiff = lat - (tile250kY * 1.0 + 40.0)
    plusTilesY = int(4.0 * latDiff) #height of area is always 1 degree
    return 4 * tile250kY + plusTilesY

def __tile50X(lon, lat):
    tile250kX = __tile250X(lon, lat)
    width, offset = __widthAndOffset250(lat)
    lonDiff = lon - (-144.0 + offset + (tile250kX * width))
    plusTilesX = int(4.0 * lonDiff / width)
    return 4 * tile250kX + plusTilesX
    

def __tile50(lon, lat):
    return __tile50X(lon, lat), __tile50Y(lat)

def __ntsId50From250KTile(tile250k, plusTilesX, plusTilesY):
    ntsId250k = __ntsId250(tile250k)
    idInt = __MAP_50K[plusTilesY][plusTilesX]
    if idInt >= 10:
        return ntsId250k[0], ntsId250k[1], str(idInt)
    else:
        return ntsId250k[0], ntsId250k[1], "0" + str(idInt)

def __bounds50(tile50k, tile250k=None, returnId=False):
    if tile250k is None:
        tile250k = __tile250FromTile50(tile50k)
    minXTile = tile250k[0] * 4
    minYTile = tile250k[1] * 4
    plusTilesX = tile50k[0] - minXTile
    plusTilesY = tile50k[1] - minYTile
    if returnId:
        return __ntsId50From250KTile(tile250k, plusTilesX, plusTilesY)
    else:
        bounds250k = __bounds250(tile250k)
        height = (bounds250k[3]-bounds250k[2]) / 4.0
        width = (bounds250k[1]-bounds250k[0]) / 4.0
        latDiff = plusTilesY * height
        lonDiff = plusTilesX * width
        minlat = bounds250k[2] + latDiff
        minlon = bounds250k[0] + lonDiff
        return (minlon, minlon+width, minlat, minlat+height)
    
def __ntsId50(tile50k, tile250k=None):
    return __bounds50(tile50k, tile250k, True)    

def __tiles50ByTile250(tile250k):
    minXTile = tile250k[0] * 4
    minYTile = tile250k[1] * 4
    outList = []
    for tileX in range(minXTile, minXTile+4):
        for tileY in range(minYTile, minYTile+4):
            outList.append((tileX, tileY))
    return outList

SCALE_SERIES = 0
SCALE_250K = 1
SCALE_50K = 2
BOUNDS = (-144, -48, 40, 88)

def validTile(scale, tile):
    if tile is None:
        return False
    if len(tile) == 0:
        return False
    
    if scale == SCALE_SERIES:
        return __validTileSeries(tile)
    elif scale == SCALE_250K:
        return validTile(SCALE_SERIES, __tileSeriesFromTile250(tile))
    elif scale == SCALE_50K:
        return validTile(SCALE_250K, __tile250FromTile50(tile))

def tileByPoint(scale, point):
    if scale == SCALE_SERIES:
        tile = __tileSeries(point[0], point[1])
    elif scale == SCALE_250K:
        tile = __tile250(point[0], point[1])
    elif scale == SCALE_50K:
        tile = __tile50(point[0], point[1])
    else:
        raise ValueError, "No such scale constant"
    if validTile(scale, tile):
        return tile
    else:
        return None

def ntsId(scale, tile):
    if scale == SCALE_SERIES:
        return (__ntsIdSeries(tile),)
    elif scale == SCALE_250K:
        return __ntsId250(tile)
    elif scale == SCALE_50K:
        return __ntsId50(tile)
    else:
        raise ValueError, "No such scale constant"
    
def ntsStringId(scale, tile):
    if scale == SCALE_SERIES:
        return __ntsIdSeries(tile)
    elif scale == SCALE_250K:
        ntsId = __ntsId250(tile)
    elif scale == SCALE_50K:
        ntsId = __ntsId50(tile)
    else:
        raise ValueError, "No such scale constant"
    return "-".join(ntsId)

def tile(scale, tile):
    if scale == SCALE_SERIES:
        return __boundsSeries(tile)
    elif scale == SCALE_250K:
        return __bounds250(tile)
    elif scale == SCALE_50K:
        return __bounds50(tile)
    else:
        raise ValueError, "No such scale constant"

def tileById(ntsStringId):
    ntsId = ntsStringId.split("-")
    if len(ntsId) == 1:
        scale = SCALE_SERIES
        tile = __tileSeriesById(ntsId[0])
    elif len(ntsId) == 2:
        scale = SCALE_250K
        tile = __tile250ById(ntsId)
    elif len(ntsId) >= 3:
        scale = SCALE_50K
        tile = __tile50ById(ntsId)
    if validTile(scale, tile):
        return tile
    else:
        return None

def tileXAt(scale, point):
    if scale == SCALE_SERIES:
        return __tileSeriesX(point[0], point[1])
    elif scale == SCALE_250K:
        return __tile250X(point[0], point[1])
    elif scale == SCALE_50K:
        return __tile50X(point[0], point[1])
    else:
        raise ValueError, "No such scale constant"

def tileYAt(scale, lat):
    if scale == SCALE_SERIES:
        return __tileSeriesY(lat)
    elif scale == SCALE_250K:
        return __tile250Y(lat)
    elif scale == SCALE_50K:
        return __tile50Y(lat)
    else:
        raise ValueError, "No such scale constant"


def __loadTiles(scale, minx, miny, maxx, maxy, tilesList):
    
    tileMin = (tileXAt(scale, (minx, miny)), tileYAt(scale, miny))
    tileMax = (tileXAt(scale, (maxx, maxy)), tileYAt(scale, maxy))
    
    for tileX in range(tileMin[0], tileMax[0]+1):
        for tileY in range(tileMin[1], tileMax[1]+1):
            tile = (tileX, tileY)
            if validTile(scale, tile):
                tilesList.append(tile)
    
def tilesBy(scale, bounds):
    minx = max(bounds[0], -144.0)
    miny = max(bounds[2], 40.0)
    maxx = min(bounds[1], -48.0)
    maxy = min(bounds[3], 88.0)

    containsAbove80 = maxy > 80.0
    containsAbove68 = containsAbove80 or maxy > 68.0 or miny > 68.0
    containsBelow68 = miny < 68.0
    containsBelow80 = miny < 80.0
    
    tiles = []
    if containsAbove80:
        if containsBelow80:
            __loadTiles(scale, minx, 80, maxx, maxy, tiles)
        else:
            __loadTiles(scale, minx, miny, maxx, maxy, tiles)
            return tiles
    if containsAbove68:
        tempmaxy = maxy
        tempminy = miny
        if containsAbove80:
            tempmaxy = 79.99
        if containsBelow68:
            tempminy = 68
        __loadTiles(scale, minx, tempminy, maxx, tempmaxy, tiles)
    if containsBelow68:
        tempmaxy = maxy
        if containsAbove68:
            tempmaxy = 67.99
        __loadTiles(scale, minx, miny, maxx, tempmaxy, tiles)
    return tiles

if __name__ == "__main__":
    totest = []
    totest.append((-129.61, 51.17)) #102P
    totest.append((-95.07, 56.44)) #054D
    totest.append((-119.9, 70.02)) #087F
    totest.append((-125.6, 79.1)) #099G
    totest.append((-81.7, 82.7)) #340F
    totest.append((-72.7, 87.9)) #341H
    totest.append((-64.4, 45.07)) #021H01
    for index in range(len(totest)):
        lon, lat = totest[index]
        print "Series tiles"
        tilea = tileByPoint(SCALE_SERIES, (lon, lat))
        antsId = ntsStringId(SCALE_SERIES, tilea)
        bounds = tile(SCALE_SERIES, tilea)
        print lat, lon, tilea, antsId, bounds
        print "Backwards Test", tileById(antsId)
        print "250k tiles"
        tilea = tileByPoint(SCALE_250K, (lon, lat))
        antsId = ntsStringId(SCALE_250K, tilea)
        bounds = tile(SCALE_250K, tilea)
        print lat, lon, tilea, antsId, bounds
        print "Backwards Test", tileById(antsId)
        print "50k tiles"
        tilea = tileByPoint(SCALE_50K, (lon, lat))
        antsId = ntsStringId(SCALE_50K, tilea)
        bounds = tile(SCALE_50K, tilea)
        print lat, lon, tilea, antsId, bounds
        print "Backwards Test", tileById(antsId)
        print ""
    #test bounds
    tiles = tilesBy(SCALE_50K, (-114.4, -108.2, 67.7, 69.5+12))
    tiles.sort(key=lambda obj: ntsStringId(SCALE_50K, obj))

    print tiles

    
