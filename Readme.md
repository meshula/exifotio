ExifOTIO scans a directory for image files with EXIF data.

Each image found in that directory is sorted by time.

The time of the first image is recorded as the epoch for the track, as a julian date in the track's metadata.

Each image is treated as a media source whose duration is the shutter time.

THe images are concatenated as clips on the track, sequentially, and save as an OTIO file.

To use exifotio, you will need to have already installed the exifread package, and OpenTimelineIO.

To run exifotio, supply the directory to inspect, and the name of the output file.

BSD 3-clause, copyright 2017 by Nick Porcino.


