import dropbox
import os
import zipfile
import tempfile
import contextlib
import datetime
import os
import six
import sys
import time
import shutil
import glob
import codecs
import chardet
import io
from lxml import etree
import re
from convertSrt2JSON import ConvertSrt2JSON

class DropboxManager(object):

    def __init__(self, course_folder, rename=True, default_attempts=3):

        self.course_folder = os.path.realpath(course_folder)
        self.rename = rename
        self.default_attempts = default_attempts
        # Get your access_token at Dropbox developer website
        access_token=os.getenv("DROPBOX_ACCESS_TOKEN")
        if not access_token:
            raise ValueError('You need to set a DROPBOX_ACCESS_TOKEN environment variable with your ACCESS TOKEN')
        self.dbx = dropbox.Dropbox(access_token)

    def download_folder(self, remote_folder):
        dbx = self.dbx
        dirpath = tempfile.mkdtemp()
        print "Using temp folder "+dirpath
        for entry in dbx.files_list_folder(remote_folder).entries:
            file_path = remote_folder+"/"+entry.name
            tmp_file = open(dirpath+"/"+entry.name, 'wb')
            datafile = self.download(file_path)
            tmp_file.write(datafile)
            tmp_file.close()
        return dirpath

    def process_srt(self, srt_folder):
        dirpath = self.download_folder(srt_folder)
        es = ConvertSrt2JSON(srcdir=dirpath, destdir=self.course_folder+"/static")
        es.runConversion()
        shutil.rmtree(dirpath)

    def process_html(self, html_folder):
        dirpath = self.download_folder(html_folder)
        for data in glob.glob(dirpath+"/*.html"):
            shutil.move(data, self.course_folder+"/html/"+os.path.basename(data))
        shutil.rmtree(dirpath)

    def process_assessment(self, assessment_folder):
        dirpath = self.download_folder(assessment_folder)
        for data in glob.glob(dirpath+"/*.xml"):
            shutil.move(data, self.course_folder+"/vertical/"+os.path.basename(data))
        shutil.rmtree(dirpath)

    def process_quiz(self, quiz_folder):
        dirpath = self.download_folder(quiz_folder)
        rename = self.rename
        for filename in os.listdir(dirpath):
            file_extension = os.path.splitext(filename)[1]

            if file_extension == ".zip":
                with zipfile.ZipFile(dirpath+"/"+filename, "r") as z:
                    print "extracting "+str(z)+ " to"+self.course_folder
                    z.extractall(self.course_folder+"/problem")
                for data in glob.glob(self.course_folder+"/problem/*.png"):
                    os.remove(self.course_folder+"/static/images/"+os.path.basename(data))
                    shutil.move(data, self.course_folder+"/static/images/")
                for data in glob.glob(self.course_folder+"/problem/*.jpg"):
                    os.remove(self.course_folder+"/static/images/"+os.path.basename(data))
                    shutil.move(data, self.course_folder+"/static/images/")
            elif file_extension == ".xml":
                shutil.move(filename, self.course_folder+"/problem/")
            elif file_extension == ".png" or file_extension == "jpg":
                os.remove(self.course_folder+"/static/images/"+os.path.basename(filename))
                shutil.move(filename, self.course_folder+"/static/images/")

        for filename in glob.glob(self.course_folder+"/problem/*.xml"):
            self.removeBOM(filename)
            problem_file = filename
            problem = etree.parse(source=problem_file).getroot()
            problem_url_name = os.path.splitext(os.path.basename(filename))[0]
            url_name = self.course_folder+"/vertical/"+problem_url_name.split("_")[0]
            verticalfile=self.course_folder+"/vertical/"+problem_url_name.split("_")[0].upper()+".xml"
            parser = etree.XMLParser(remove_blank_text=True)
            vertical = etree.parse(source=verticalfile, parser=parser).getroot()
            xpath = './/problem[url_name="'+problem_url_name+'"]'
            vproblems = vertical.findall(xpath)
            if (len(vproblems) == 0):
                problem_ref = etree.Element(
                    "problem", attrib={})
                problem_ref.set("url_name",problem_url_name)
                vertical.append(problem_ref)
                self.sortchildrenby(vertical, 'url_name')
                with open(verticalfile, "w") as file:
                    file.write(etree.tostring(vertical, pretty_print=True))
            if self.rename:
                display_name=problem.get("display_name")
                if not display_name or display_name == "":
                    problemname=os.path.splitext(os.path.basename(filename))[0].split("_")[1]
                    problemname = int(problemname)
                    display_name = "Quiz "+str(problemname)
                    problem.set("display_name", display_name)
            if self.default_attempts and "max_attempts" not in problem.attrib.keys():
                problem.set("max_attempts", self.default_attempts)

            if not self.rename:
                problem.set("display_name", vertical.get("display_name"))

            problem_content=etree.tostring(problem)
            problem_content = re.sub(r'<p>{immagine - ([^}]*)}</p>',r'<div class="graph"><img style="max-width:100%" class="jpg" src="/static/images/\1" /></div>',problem_content)
            problem_content = re.sub(r'{image - ([^}]*)}',r'<div class="graph"><img style="max-width:100%" class="jpg" src="/static/images/\1" /></div>',problem_content)
            #rewrite file problem
            with open(problem_file, "w") as file:
                file.write(problem_content)

        shutil.rmtree(dirpath)

    def sortchildrenby(self, parent, attr):
        parent[:] = sorted(parent, key=lambda child: child.get(attr))

    def removeBOM(self, path):

        bytes = min(32, os.path.getsize(path))
        raw = open(path, 'rb').read(bytes)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            result = chardet.detect(raw)
            print "Encoding in "+ str(path)+" " + str(result)
            encoding = result['encoding']
        if 'utf-8' not in encoding :
            return
        with io.open(path, "r", encoding=encoding) as file:
            filedata = file.read()

        with open(path, "w") as file:
            file.write(filedata.encode("utf-8"))

    def download(self, path):
        """Download a file.
        Return the bytes of the file, or None if it doesn't exist.
        """
        dbx = self.dbx
        while '//' in path:
            path = path.replace('//', '/')
        with stopwatch('download'):
            try:
                md, res = dbx.files_download(path)
            except dropbox.exceptions.HttpError as err:
                print('*** HTTP error', err)
                return None
        data = res.content
        print(len(data), 'bytes; md:', md)
        return data


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))
