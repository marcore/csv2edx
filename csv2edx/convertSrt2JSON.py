import json
import os, sys ,re
import pysrt

DEFAULT_REGEX="^[W|I][0-9A-Za-z]{5}([^-]*)?-"

class ConvertSrt2JSON(object):

    def __init__(self,srcdir='',destdir='',filter_regex=DEFAULT_REGEX):
        self.srcdir = srcdir
        self.destdir = destdir
        self.filter_regex=filter_regex

    def convertFile(self,srcfile,destfile):
        video_id=srcfile
        subs = pysrt.open(srcfile)
        data={"start":[],"end":[],"text":[]}
        print "Converting file " + str(srcfile)
        for s in subs:
            start=s.start.minutes*60000+s.start.seconds*1000+s.start.milliseconds
            end=s.end.minutes*60000+s.end.seconds*1000+s.end.milliseconds
            text=s.text
            data["start"].append(start)
            data["end"].append(end)
            data["text"].append(text)
        if len(data["start"]) == 0:
            print "###### WARNING: something goes wrong with " + str(srcfile)
        with open(destfile, 'w') as outfile:
            json.dump(data, outfile)

    def runConversion(self):
        for i in os.listdir(str(self.srcdir)):
            if i.endswith(".srt"):
                filename="subs_"+re.sub(self.filter_regex,"",i)+".sjson"
                self.convertFile(self.srcdir+"/"+i,self.destdir+"/"+filename)
