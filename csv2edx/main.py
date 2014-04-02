#!/usr/bin/python
import xbundle
import preparecsv
import os
import csv
import sys
import optparse
from path import path    # needs path.py
from lxml import etree
from urlparse import urlparse, parse_qs


class csv2edx(object):
    '''
    csv2edx convert a csv file to standard xml format files for edx
    
    A pre-parse phase can be activated with flag "pre-parse" if the csv file contains extra columns not needed.
    Columns needed are [CHAPTERNAME,SEQUENTIALNAME,VERTICALNAME,LINK]. At this moment LINK is a link to youtube video as currently 
    only video vertical are supported
    
    The script can be run from any directory and generated files outputs to currently directory
    '''
    
    DescriptorTags = ['course','chapter','sequential','vertical','html','problem','video',
                      'conditional', 'combinedopenended', 'randomize' ]

    
    def __init__(self,
                 fn, #input csv filename 
                 verbose=False,
                 prepare_csv=False, # true if csv need a pre-parse phase
                 cols2preserve=[],
                 output_fn="",
                 output_dir='',
                 do_merge=False,
                 imurl='images',
                 do_images=True):

        if not output_dir:
            output_dir = os.path.abspath('.')
        self.output_dir = path(output_dir)
        imdir = self.output_dir / 'static/images'
        
        if do_images:    # make directories only if do_images
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
            if not os.path.exists(self.output_dir / 'static'):
                os.mkdir(self.output_dir / 'static')
            if not os.path.exists(imdir):
                os.mkdir(imdir)
        
        self.do_merge = do_merge
        
        self.verbose=verbose
        
        self.fn=fn
        if prepare_csv :
            self.pcsv=preparecsv.PrepareCsv(fn,cols2preserve,verbose)
            preparedFileName=self.pcsv.prepare()
            
            if (verbose):
                print "Colums to preserve : "+str(cols2preserve)
                print "Prepared file : "+str(preparedFileName)
           
            self.fn=preparedFileName
        
        if output_fn is None or not output_fn:
            if fn.endswith('.csv'):
                output_fn = fn[:-4]+'.xbundle'
            else:
                output_fn = fn + '.xbundle'
        self.output_fn = output_fn

        
        
        
    def convert(self):
        
        self.csv2xbundle()
        self.xb.save(self.output_fn)
        print "xbundle generated (%s): " % self.output_fn 
        tags = ['chapter', 'sequential', 'problem', 'html','video']
        for tag in tags:
            print "    %s: %d" % (tag, len(self.xb.course.findall('.//%s' % tag)))
        self.xb.export_to_directory(self.output_dir, xml_only=True)
        print "Course exported to %s/" % self.output_dir

        if self.do_merge and self.xb.overwrite_files:
            self.merge_course() 
    
    def video_id(self,value):
        """
        Examples:
        - http://youtu.be/SA2iWivDJiE
        - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
        - http://www.youtube.com/embed/SA2iWivDJiE
        - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
        """
        query = urlparse(value)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        # fail?
        return None

    def createXBundle(self):
       
        course=etree.Element("course", attrib={})
        
        with open(self.fn, 'rb') as f:
            reader = csv.reader(f,delimiter='\t')
            
            currentChapter=etree.Element("chapter", attrib={})
            changedChapter=False
            currentSequential=etree.Element("sequential", attrib={})
            for counter,row in enumerate(reader):
                currentVertical=etree.Element("vertical", attrib={})
                video=etree.Element("video", attrib={})
                item_id=row[3]
               
                for idx,col in enumerate(row):
                    col=col.decode('utf-8', 'xmlcharrefreplace')
                    if idx == 0 :
                        
                        if col != currentChapter.get("display_name"):
                            changedChapter=True
                            currentChapter=etree.Element("chapter")
                            currentChapter.set("display_name",col)
                            currentChapter.set("url_name",item_id[:2])
                        else:
                            changedChapter=False
                    elif idx == 1 :
                        if col != currentSequential.get("display_name"):
                            currentSequential=etree.Element("sequential", attrib={"display_name":col})
                            currentSequential.set("url_name",item_id[:4])
                            currentChapter.append(currentSequential)
                    elif idx == 2 :
                        currentVertical.set("display_name",col)
                    elif idx == 3 :
                        
                        video=etree.Element("video", attrib={})
                        currentVertical.set("url_name",col)
                        video.set("url_name",col+"_video")
                    elif idx == 4 :
                        video_id=self.video_id(col)
                        video.set("youtube","1.0:"+video_id)
                        currentVertical.append(video)
                if (changedChapter):
                    
                    course.append(currentChapter)
                else:
                    currentSequential.append(currentVertical)
                
         
        return course               
    
    
    def csv2xbundle(self):
        '''
        Convert csv to and edx bundle file.
        '''
        xml=self.createXBundle()
        self.xml=xml
        no_overwrite = ['course'] if self.do_merge else []
        xb = xbundle.XBundle(force_studio_format=True, keep_urls=True,
                             no_overwrite=no_overwrite)
        xb.KeepTogetherTags =['video'] # ['sequential', 'vertical', 'conditional']
        xb.DefaultOrg="Polimi"
        xb.DefaultSemester="2014_T1"
        course = xml.find('.')
        if (self.verbose):
            print "Bundle:"+etree.tostring(xml)        
        if course is not None:
            xb.set_course(course)
        self.xb = xb
        return xb
        
    def merge_course(self):
        print "    merging files %s" % self.xb.overwrite_files
        for fn in self.xb.overwrite_files:
            if str(fn).endswith('course.xml.new'):
                # course.xml shouldn't need merging
                os.unlink(fn)
            else:
                newcourse = etree.parse(open(fn)).getroot()
                oldfn = fn[:-4]
                oldcourse = etree.parse(open(oldfn)).getroot()
                oldchapters = [x.get('url_name') for x in oldcourse]
                newchapters = []
                for chapter in newcourse:
                    if chapter.get('url_name') in oldchapters:
                        continue        # already in old course, skip
                    oldcourse.append(chapter)    # wasn't in old course, move it there
                    newchapters.append(chapter.get('url_name'))
                self.xb.write_xml_file(oldfn, oldcourse, force_overwrite=True)
                os.unlink(fn)
                print "    added new chapters %s" % newchapters
          
          
            
def CommandLine():
    parser = optparse.OptionParser(usage="usage: %prog [options] filename.csv",
                                   version="%prog 1.0")
    parser.add_option('-v', '--verbose', 
                      dest='verbose', 
                      default=False, action='store_true',
                      help='verbose error messages')
    parser.add_option("-o", "--output-xbundle",
                      action="store",
                      dest="output_fn",
                      default="",
                      help="Filename for output xbundle file",)
    parser.add_option("-d", "--output-directory",
                      action="store",
                      dest="output_dir",
                      default="course",
                      help="Directory name for output course XML files",)
    parser.add_option("-m", "--merge-chapters",
                      action="store_true",
                      dest="merge",
                      default=False,
                      help="merge chapters into existing course directory",)
    parser.add_option("-p", "--prepare-csv",
                      action="store_true",
                      dest="prepare_csv",
                      default=False,
                      help="Prepare csv file to be in the csv2edx format",)
    parser.add_option("-c", "--cols2preserve",
                      action="store",
                      dest="cols2preserve",
                      default="",
                      help="Columns to preserve in the final format of csv file (see -p option)",)
    (opts, args) = parser.parse_args()

    if len(args)<1:
        parser.error('wrong number of arguments')
        sys.exit(0)
    if (opts.prepare_csv and len(opts.cols2preserve)==0):
        parser.error('You need to specify colums to preserve with option -c if you want to prepare csv with option -p')
        sys.exit(0)
    
    fn = args[0]

    cols=map(int,opts.cols2preserve.split(","))
    c = csv2edx(fn, verbose=opts.verbose, output_fn=opts.output_fn,
                  output_dir=opts.output_dir,
                  do_merge=opts.merge,
                  prepare_csv=opts.prepare_csv,
                  cols2preserve=cols
        )
    c.convert()