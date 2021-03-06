#!/usr/bin/python
import xbundle
import preparecsv
import os
import csv
import re
import sys
import optparse
from path import path    # needs path.py
from lxml import etree
from urlparse import urlparse, parse_qs
from dropbox_manager import DropboxManager
import ConfigParser

CONFIG_FILENAME = 'csv2edx.cfg'


class csv2edx(object):

    '''
    csv2edx convert a csv file to standard xml format files for edx

    A pre-parse phase can be activated with flag "pre-parse" if the csv file contains extra columns not needed.
    Columns needed are [CHAPTERNAME,SEQUENTIALNAME,VERTICALNAME,LINK]. At this moment LINK is a link to youtube video as currently
    only video vertical are supported

    The script can be run from any directory and generated files outputs to currently directory
    '''

    DescriptorTags = ['course', 'chapter', 'sequential', 'vertical', 'html', 'problem', 'video',
                      'conditional', 'combinedopenended', 'randomize']

    def __init__(self,
                 fn,  # input csv filename
                 verbose=False,
                 prepare_csv=False,  # true if csv need a pre-parse phase
                 cols2preserve=[],
                 transcript_enabled=False,
                 output_fn="",
                 output_dir='',
                 do_merge=False,
                 imurl='images',
                 do_images=True,
                 courseconf=[],
                 dropboxconf=[]):

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

        self.transcript_enabled = transcript_enabled

        self.verbose = verbose

        self.fn = fn
        self.prepare_csv = prepare_csv
        if prepare_csv:
            self.pcsv = preparecsv.PrepareCsv(fn, cols2preserve, verbose)
            preparedFileName = self.pcsv.prepare()

            if (verbose):
                print "Colums to preserve : " + str(self.pcsv.cols)
                print "Prepared file : " + str(preparedFileName)

            self.fn = preparedFileName

        if output_fn is None or not output_fn:
            if fn.endswith('.csv'):
                output_fn = fn[:-4] + '.xbundle'
            else:
                output_fn = fn + '.xbundle'
        self.output_fn = output_fn
        self.config = {}
        for i in courseconf:
            self.config[i[0]] = i[1]

        self.dropbox_config = {}
        for i in dropboxconf:
            self.dropbox_config[i[0]] = i[1]

    def convert(self):

        self.csv2xbundle()
        self.xb.save(self.output_fn)
        print "xbundle generated (%s): " % self.output_fn
        tags = ['chapter', 'sequential', 'problem', 'video']
        for tag in tags:
            print "    %s: %d" % (tag, len(self.xb.course.findall('.//%s' % tag)))
        self.xb.export_to_directory(self.output_dir, xml_only=True)
        print "Course exported to %s/" % self.output_dir

        if self.do_merge and self.xb.overwrite_files:
            self.merge_course()

    def video_id(self, value):
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

        course = etree.Element("course", attrib={})
        for k in self.config.keys():
            course.set(k, self.config.get(k))

        with open(self.fn, 'rb') as f:
            reader = csv.reader(f, delimiter='\t')

            currentChapter = etree.Element("chapter", attrib={})
            changedChapter = False
            currentSequential = etree.Element("sequential", attrib={})
            for counter, row in enumerate(reader):
                currentVertical = etree.Element("vertical", attrib={})
                video = etree.Element("video", attrib={})
                if (self.verbose):
                    print "process row :" + str(row)
                item_id = row[3]
                isVideo = (self.video_id(row[4]) != None)
                if (self.verbose):
                    print "the row isVideo ?" + str(isVideo)
                for idx, col in enumerate(row):
                    col = col.decode('utf-8', 'xmlcharrefreplace')
                    if idx == 0:

                        if col != currentChapter.get("display_name"):
                            changedChapter = True
                            currentChapter = etree.Element("chapter")
                            currentChapter.set("display_name", col)
                            chapterSeq = ""
                            try:
                                indexSeparator = item_id.index("$")
                                chapterSeq = item_id[:indexSeparator]
                                chapterSeq = chapterSeq.replace("$", "")
                            except ValueError:
                                chapterSeq = item_id[:2]
                            currentChapter.set("url_name", chapterSeq)
                        else:
                            changedChapter = False
                    elif idx == 1:
                        if col != currentSequential.get("display_name"):
                            sequentialurlname = ""
                            try:
                                indexSeparator = item_id.index("$")
                                indexSeparator = item_id.index("$", indexSeparator+1)
                                sequentialurlname = item_id[:indexSeparator]
                                sequentialurlname = sequentialurlname.replace("$", "")
                            except ValueError:
                                matching = re.search('W\d{1,2}M\d{1,2}', item_id)
                                if matching:
                                    sequentialurlname = matching.group(0)
                                else:
                                    sequentialurlname = item_id[:4]


                            currentSequential = etree.Element(
                                "sequential", attrib={"display_name": col})
                            try:
                                previousSequential = etree.parse(
                                    source=self.output_dir + "/sequential/" + sequentialurlname + ".xml").getroot()
                                for a in previousSequential.attrib.keys():
                                    currentSequential.set(
                                        a, previousSequential.get(a))
                            except IOError:
                                print 'Can\'t read existing sequential in :' + sequentialurlname
                            currentSequential.set("display_name", col)
                            currentSequential.set(
                                "url_name", sequentialurlname)
                            currentChapter.append(currentSequential)
                    elif idx == 2:
                        currentVertical.set("display_name", col)
                    elif idx == 3:
                        col = col.replace("$", "")
                        currentVertical.set("url_name", col)
                        url_name_video = col + "_video"
                        if (isVideo):
                            video = etree.Element("video", attrib={})
                            video.set(
                                "display_name", currentVertical.get("display_name"))
                            video.set("url_name", url_name_video)
                            if (self.transcript_enabled):
                                video = self.addTranscriptVideo(video, col)

                    elif idx == 4:
                        if ("|" in col):
                            lecture_elements = col.split("|")
                            count_video = 0
                            for l in lecture_elements:
                                if self.video_id(l):
                                    count_video = count_video+1

                            if (self.verbose):
                                    print "Vertical has multiple elements  :" + str(lecture_elements)
                            for counter, vu in enumerate(lecture_elements):
                                if (self.verbose):
                                    print "processing element  :" + str(vu)
                                currentVertical = self.processLectureElement(currentVertical, vu, url_name_video, (counter+1),(count_video>1))

                        else:
                            #normal processing
                            currentVertical = self.processLectureElement(currentVertical, col, url_name_video, 0, False)

                if (self.verbose):
                    print "Aggiungo vertical" + etree.tostring(currentVertical, pretty_print=True) + " al sequential corrente"
                currentSequential.append(currentVertical)
                if (self.verbose):
                    print "Risultato : " + etree.tostring(currentSequential, pretty_print=True)
                    print "Capitolo attuale: " + etree.tostring(currentChapter, pretty_print=True)
                if (changedChapter):
                    if (self.verbose):
                        print "Aggiungo capitolo" + etree.tostring(currentChapter, pretty_print=True)
                    course.append(currentChapter)

        return course

    def processLectureElement(self, currentVertical, lecture_element, url_name_element,counter, multipleVideos):
        isVideo = (self.video_id(lecture_element.strip()) != None)
        display_name =  currentVertical.get("display_name")
        if isVideo:
            newVideoItem = etree.Element(
                "video", attrib={})
            if (counter > 0 and multipleVideos):
                display_name = display_name + " - Parte " + self.int_to_roman(counter)
            newVideoItem.set("display_name",  display_name)
            url_name =  url_name_element
            if (counter > 0 and multipleVideos):
                url_name = url_name  + self.int_to_roman(counter)
            newVideoItem.set(
                "url_name", url_name)
            newVideo_ID = self.video_id(lecture_element.strip())
            newVideoItem.set(
                "youtube", "1.0:" + str(newVideo_ID))
            newVideoItem.set("sub", str(newVideo_ID))
            if (self.transcript_enabled):
                newVideoItem = self.addTranscriptVideo(
                    newVideoItem, url_name)
            currentVertical.append(newVideoItem)
        else:
            if "forum" in lecture_element:
                discussionName = currentVertical.get("display_name")
                if ":" in lecture_element:
                    discussionName= lecture_element.split(":")[1]
                discussionItem = etree.Element("discussion", attrib={})
                discussionItem.set("url_name", currentVertical.get("url_name"))
                discussionItem.set("display_name", discussionName)
                discussionItem.set("discussion_target", discussionName)
                currentVertical.append(discussionItem)
            elif "html" in lecture_element or (lecture_element=="" and self.existsHtmlFile(currentVertical.get("url_name"))):
                htmlItem = etree.Element("html", attrib={})
                htmlItem.set("url_name", currentVertical.get("url_name"))
                htmlItem.set("filename", currentVertical.get("url_name"))
                htmlItem.set("display_name", currentVertical.get("display_name"))
                currentVertical.append(htmlItem)

        return currentVertical

    def existsHtmlFile(self, filename):
        html_file_path=self.output_dir + "/html/" + filename+ ".html"
        print "Check exists : "+str(html_file_path)
        return os.path.isfile(html_file_path)

    def addTranscriptVideo(self, video, col):
        transcriptPath = "/static/track/" + col + ".pdf"
        video.set("download_track", "true")
        video.set("track", transcriptPath)
        track = etree.Element("track", attrib={})
        track.set("src", transcriptPath)
        video.append(track)
        return video

    def csv2xbundle(self):
        '''
        Convert csv to and edx bundle file.
        '''
        xml = self.createXBundle()
        self.xml = xml
        no_overwrite = ['course'] if self.do_merge else []
        if (self.verbose):
            print "No overwrite:" + str(no_overwrite)
        xb = xbundle.XBundle(force_studio_format=True, keep_urls=True,
                             no_overwrite=no_overwrite)
        # ['sequential', 'vertical', 'conditional']
        xb.KeepTogetherTags = ['video', 'html']
        xb.DefaultOrg = "Polimi"
        xb.DefaultSemester = "2014_T1"
        course = xml.find('.')
        if (self.verbose):
            print "Bundle:" + etree.tostring(xml)
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
                    # wasn't in old course, move it there
                    oldcourse.append(chapter)
                    newchapters.append(chapter.get('url_name'))
                self.xb.write_xml_file(oldfn, oldcourse, force_overwrite=True)
                os.unlink(fn)
                print "    added new chapters %s" % newchapters

    def int_to_roman(self, input):
        """ Convert an integer to a Roman numeral. """

        if not isinstance(input, type(1)):
            raise TypeError, "expected integer, got %s" % type(input)
        if not 0 < input < 4000:
            raise ValueError, "Argument must be between 1 and 3999"
        ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
        nums = ('M',  'CM', 'D', 'CD', 'C', 'XC',
                'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
        result = []
        for i in range(len(ints)):
            count = int(input / ints[i])
            result.append(nums[i] * count)
            input -= ints[i] * count
        return ''.join(result)

    def copyQuiz(self):

        quiz_folder = self.dropbox_config.get("quiz_folder")
        rename = self.dropbox_config.get("rename", True)
        default_attempts = self.dropbox_config.get("default_attempts", 3)
        if quiz_folder:
            dr = DropboxManager(self.output_dir,rename, default_attempts)
            dr.process_quiz(quiz_folder)
        else:
            print "No quiz_folder configurated in csv2edx.cfg file"

    def copyAndConvertSrt(self):

        srt_folder = self.dropbox_config.get("srt_folder")
        if srt_folder:
            dr = DropboxManager(self.output_dir)
            dr.process_srt(srt_folder)
        else:
            print "No srt_folder configurated in csv2edx.cfg file"

    def copyHtml(self):

        html_folder = self.dropbox_config.get("html_folder")
        if html_folder:
            dr = DropboxManager(self.output_dir)
            dr.process_html(html_folder)
        else:
            print "No html_folder configurated in csv2edx.cfg file"

    def copyAssessment(self):

        vertical_assessment_folder = self.dropbox_config.get("vertical_assessment_folder")
        if vertical_assessment_folder:
            dr = DropboxManager(self.output_dir)
            dr.process_assessment(vertical_assessment_folder)
        else:
            print "No html_folder configurated in csv2edx.cfg file"

def CommandLine():
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILENAME)

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
    parser.add_option("-t", "--transcript-enabled",
                      action="store_true",
                      dest="transcript_enabled",
                      default=False,
                      help="Add track element in video for download transcript",)
    (opts, args) = parser.parse_args()

    if len(args) < 1:
        parser.error('wrong number of arguments')
        sys.exit(0)
    if (opts.prepare_csv and len(opts.cols2preserve) == 0):
        parser.error(
            'You need to specify colums to preserve with option -c if you want to prepare csv with option -p')
        sys.exit(0)

    fn = args[0]

    cols = map(int, opts.cols2preserve.split(","))
    c = csv2edx(fn, verbose=opts.verbose, output_fn=opts.output_fn,
                output_dir=opts.output_dir,
                do_merge=opts.merge,
                prepare_csv=opts.prepare_csv,
                cols2preserve=cols,
                transcript_enabled=opts.transcript_enabled,
                courseconf=config.items("course"),
                dropboxconf=config.items("dropbox"),
                )
    c.convert()
    c.copyHtml()
    c.copyQuiz()
    c.copyAssessment()
    c.copyAndConvertSrt()
