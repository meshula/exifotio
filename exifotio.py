#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from os import walk
import os
import math
import sys
import logging
import datetime
import collections

import jdutil
import exifread
import opentimelineio as otio
from opentimelineio import opentime


logging.basicConfig(level=logging.INFO)


class ImageRef():
    """
    Information on a discovered image file
    """

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.time_stamp = 0.0

    def __lt__(self, other):
         return self.time_stamp < other.time_stamp

def main(srcpath, outfile):
    '''
    Find all the files in a path and extract the julian date of any pictures found
    '''
    srcpath = '/'.join(srcpath.split('\\'))
    candidate_files = []

    print "Scanning directory: ", srcpath

    for (dirpath, dirnames, filenames) in walk(srcpath):
        for file in filenames:
            fullpath = os.path.join(dirpath, file)
            candidate_files.append('/'.join(fullpath.split('\\')))
        break # only ingest the first directory found. TODO: make a track per directory

    refs = []

    print "Reading EXIF data"

    file_count = 0
    max_files = 1000

    for path in candidate_files:
        fh = open(path, "rb")
        tags = exifread.process_file(fh, details=False)
        fh.close()

        if 'EXIF DateTimeOriginal' in tags:
            rpath = os.path.relpath(path, srcpath)
            ref = ImageRef(path.split('/')[-1], rpath)

            datestr = tags['EXIF DateTimeOriginal'].values
            datestrs = datestr.split(' ')
            cal = datestrs[0].split(':')
            hr = datestrs[1].split(':')
            dto = datetime.datetime(int(cal[0]), int(cal[1]), int(cal[2]), int(hr[0]), int(hr[1]), int(hr[2]))
            julian = jdutil.datetime_to_jd(dto)

            ref.time_stamp = julian

            if 'EXIF ExposureTime' in tags:
                et = tags['EXIF ExposureTime'].values[0]
                ref.exposure_time = float(et.num) / float(et.den)
            else:
                ref.exposure_time = 1.0/100.0 # arbitrary

            refs.append(ref)

        file_count += 1
        if file_count > max_files:
            break

    refs.sort()

    epoch = refs[0].time_stamp

    for ref in refs:
        print (ref.time_stamp - epoch) * 24 * 3600, ref.path

    timeline = otio.schema.Timeline()
    timeline.name = "Photos" # TODO pass the time line name
    track = otio.schema.Sequence()
    track.name = "Photo track" # TODO make a track per day
    track.metadata = { "epoch": epoch }
    timeline.tracks.append(track)

    for i, ref in enumerate(refs):
        next_i = min(i+1, len(refs)-1)
        ts = (ref.time_stamp - epoch) * 24.0 * 3600.0 # seconds
        ts_next = (refs[next_i].time_stamp - epoch) * 24.0 * 3600.0
        duration = ts_next - ts

        # exposure time is already in seconds
        image_time = opentime.TimeRange(
            opentime.RationalTime(ts, 1),
            opentime.RationalTime(ref.exposure_time, 1.0))

        media_reference = otio.media_reference.External(
            target_url="file://" + ref.path,
            available_range = image_time)
        media_reference.name = ref.name

        clip = otio.schema.Clip(name=ref.name)
        clip.media_reference = media_reference
        clip.source_range = opentime.TimeRange(opentime.RationalTime(0, 1.0), opentime.RationalTime(duration, 1.0))
        track.append(clip)

    otio.adapters.write_to_file(timeline, outfile)



def usage():
    print("Usage: exifotio.py <dirpath> <outfile>")

if __name__ == "__main__":

    if len(sys.argv) != 3:
        usage()
    else:
        main(sys.argv[1], sys.argv[2])