#!/usr/bin/python
from pygpx import GPX, datetime_iso
from pexif import *
from datetime import timedelta
import sys
import os

force_mode = False
utc_corr = timedelta()

def parse_in_trkseg(trackseg, e_date):
    found = False
    i = 0
    l = len(trackseg.trkpts)
    #Start Point
    spt = trackseg.trkpts[0]
    for i in range(l - 1):
        fpt = trackseg.trkpts[i + 1]
        if spt.time + utc_corr <= e_date <= fpt.time + utc_corr:
            print "Found between %d-th and %d-th of %d points" % (i + 1, i + 2, l)
            #Position linear interpolation
            dt_pt = (fpt.time) - (spt.time)
            dt_ed = e_date - (spt.time + utc_corr)
            k = float(dt_ed.seconds)/float(dt_pt.seconds)
            print "dShoot Time K=", k
            dl_pt = fpt.lon - spt.lon
            #print "dLon on PT=", dl_pt
            dl_ed = dl_pt * k
            #print "dLon on IM=", dl_ed
            
            result = []
            result.append(spt.lon + dl_ed)
            
            dl_pt = fpt.lat - spt.lat
            #print "dLat on PT=", dl_pt
            dl_ed = dl_pt * k
            #print "dLat on IM=", dl_ed
            
            result.append(spt.lat + dl_ed)
            
            return result
            break
        spt = fpt
    if not found:
        return None

def parse_in_gpx(gpx, e_date):
    found = False    
    i = 0
    for i in range(len(gpx.tracks)):
        sd = gpx.tracks[i].start_time() + utc_corr
        fd = gpx.tracks[i].end_time() + utc_corr
        if sd <= e_date <= fd:
            print "Found in %d-th track: [%s --> %s]" % (i + 1, \
                gpx.tracks[i].start_time() + utc_corr, \
                gpx.tracks[i].end_time() + utc_corr)
            found = True
            break
        
    if found:
        if len(gpx.tracks[i].trksegs[0].trkpts) > 0:
            return parse_in_trkseg(gpx.tracks[i].trksegs[0], e_date)
        else:
            return None
    else:
        return None
    
def read_opts():
    global force_mode        
    cntr = 1;
    for i in range(cntr, len(sys.argv)):
        if sys.argv[i][0] <> "-":
            break
        cntr += 1
        for j in range(1, len(sys.argv[i])):
            if sys.argv[i][j] == "f":
                print "force mode is ON"
                force_mode = True
            #if sys.argv[i][j] == "r":
            #    print "recurce mode is ON"
            #    recur_mode = True
    return cntr

def edit_img(gpx, file_path):
    file_name = os.path.basename(file_path)
    try:
        jpg = JpegFile.fromFile(file_path)
        print "Processing `%s'..." % (file_name)
    except:
        print >> sys.stderr, "File `%s' is not image or broken" % (file_name)
        return False
    
    #Getting images datetime attribute
    exif = jpg.get_exif()
    ifd = exif.get_primary()

    if ifd.has_key(GPSIFD):
        print "`%s' already has gps tag" % (file_name)
        if not force_mode:
            return False
    
    try:
        date = ifd.__getattr__("DateTime")
        for entry in ifd.entries:
            tag, exif_type, data = entry
            if ifd.isifd(data):
                date = data.__getattr__("DateTimeOriginal")
                if date:
                    break
    except:
        print >> sys.stderr, "Image File `%s' has wrong attributes" % (file_name)
        return False
    exif_date = datetime_iso(date)
    
    #Selecting tracking period
    print "Looking for `%s' exif date:" % (file_name), exif_date
    lonlat = parse_in_gpx(gpx, exif_date)
    if lonlat:
        print "Seems it was at LonLat:", lonlat
        jpg.set_geo(lonlat[1], lonlat[0])
        jpg.writeFile(file_path)
        print "..Done"
    else:
        print "No one track found =( ..."    
    return True

def main():
    global utc_corr
    if len(sys.argv) < 3:
        print "Usage: trackimap [options] <gpx_file> <+|-UTC> [img_file(s)|dir]"
        print "\tOption: -f - force rewrite geotags"
        print "\tExample: gpx2jpg -f file.gpx +4 im_dir/*.jpg"
        print """\tNote: 1) When gpx2jpg meet folder it try to go recursive
        2) GPX file written in UTC Zulu time. If your camera time was 
        setted to another time zone then setup correction for gpx"""
        return
    
    arg_ind = read_opts()
   
    try:
        gpx = GPX(open(sys.argv[arg_ind]))
    except:
        print sys.stderr, "Can't open GPX file!"
        return
    arg_ind += 1
    
    #Check gpx UTC correction
    utc_corr = timedelta()
    if ((arg_ind) < len(sys.argv)):
        arg_c = sys.argv[arg_ind][0]
        if (arg_c == "+") or (arg_c == "-") or (arg_c == "0"):
            if arg_c <> 0:
                utc_corr = timedelta(hours=int(sys.argv[arg_ind]))
                arg_ind += 1
        else:
            print >> sys.stderr, "Error: You did not set UTC shift!"
            return
        
    print "GPX opened: [%s --> %s]" % ( \
        gpx.tracks[0].start_time()                 + utc_corr, \
        gpx.tracks[len(gpx.tracks) - 1].end_time() + utc_corr)
    
    #Check if there's no img files - set this folder
    if (arg_ind) == len(sys.argv):
        sys.argv.append(".")
    
    #TODO Recurse
    fileList = []
    for i in range(arg_ind, len(sys.argv)):
        #Triing to load file
        if os.path.isdir(sys.argv[i]):
            rootdir = sys.argv[i]
            for root, subFolders, files in os.walk(rootdir):
                for file in files:
                    fileList.append(os.path.join(root,file))
        else:
            fileList.append(sys.argv[i])
            
    for imgs in fileList:
        if not edit_img(gpx, imgs):
            continue

if __name__ == "__main__":
    main()
