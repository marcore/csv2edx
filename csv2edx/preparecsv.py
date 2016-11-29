#!/bin/python

import csv
from shutil import move
from os import remove
from glob import glob
from timeit import itertools





class PrepareCsv(object):
    '''
    Take a csv files and prepare it to pass to csv2edx.convert.
    Basically preserve only columns needed for csv2edx as indicated by columns option and creates
    (if columns < 5) a column in 4th position for url_name automatically (see edxUrlName)

    '''

    def __init__(self,
                 fn,
                 cols2preserve=[],
                 verbose=False):
        self.fn=fn
        self.cols=cols2preserve
        self.verbose=verbose

    def prepare(self):
        fn=self.fn
        tmpfile=self.addEmptyElements(fn)
        shiftNeeded=False
        if (len(self.cols)<5):
            tmpfile=self.addMissedCoding(tmpfile)
            self.addNewColum2Preserve(tmpfile)
            shiftNeeded=True
            if self.verbose:
                print "Cols2preserve : "+str(self.cols)
        tmpfile=self.removeUnusedColums(tmpfile)

        if (shiftNeeded):
            tmpfile=self.shiftColumCodeToThird(tmpfile)

        tmpfile=self.stripEmptyRows(tmpfile)



        preparedFileName=fn+".PREPARED"
        move(tmpfile,preparedFileName)

        if not self.verbose:
            self.cleanTmp(fn)

        return preparedFileName

    def edxUrlName(self,chapterName,sequentialName,verticalName):
        return "W"+chapterName[0]+"M"+sequentialName[0]+verticalName[:2]

    def addNewColum2Preserve(self,filename):
        cols2preserve=[i+1 for i in self.cols]
        cols2preserve.insert(0, 0)
        self.cols=cols2preserve

    def addEmptyElements(self,filename):
        newfilename=filename+"_tmp"
        input = open(filename, 'rb')
        output = open(newfilename, 'wb')
        if self.verbose:
            print "Reading "+filename+" and writing to "+newfilename
        writer = csv.writer(output,delimiter='\t')
        previous_row=[]
        for counter,row in enumerate(csv.reader(input,delimiter='\t')):
                if (self.verbose):
                    print "process row :" +str(row)
                if not all(field=='' for field in row):
                    new_row=[]
                    for idx,col in enumerate(row):

                        if (any(col)):
                            new_row.insert(idx,col)
                        else:
                            if (idx!=self.cols[-1]): # automatic inser only for chapter and sequencial name column
                                try:
                                    new_row.insert(idx,previous_row[idx])
                                except IndexError:
                                    print 'Skipped empty elements for :'+str(row)
                            else:
                                new_row.insert(idx,"") #empty col for video
                    previous_row=new_row

                    writer.writerow(new_row)
        input.close()
        output.close()
        return newfilename
    def removeUnusedColums(self,filename):
        newfilename=filename+"_tmp"
        input = open(filename, 'rb')
        output = open(newfilename, 'wb')
        if self.verbose:
            print "Reading "+filename+" and writing to "+newfilename
        writer = csv.writer(output,delimiter='\t')

        for counter,row in enumerate(csv.reader(input,delimiter='\t')):
            if (counter>0):        #skip csv header
                new_row = [col for idx, col in enumerate(row) if idx in self.cols]
                writer.writerow(new_row)
        input.close()
        output.close()
        return newfilename
    def shiftColumCodeToThird(self,filename):
        newfilename=filename+"_tmp"
        input = open(filename, 'rb')
        output = open(newfilename, 'wb')
        if self.verbose:
            print "Reading "+filename+" and writing to "+newfilename
        writer = csv.writer(output,delimiter='\t')

        for counter,row in enumerate(csv.reader(input,delimiter='\t')):
            new_row=[]
            for idx,col in enumerate(row):
                colempty=""
                try:
                    colempty=row[4]
                except IndexError:
                    print 'Set last column to :'+colempty
                new_row=[row[1],row[2],row[3],row[0],colempty]

            writer.writerow(new_row)
        input.close()
        output.close()
        return newfilename

    def stripEmptyRows(self,filename):
        newfilename=filename+"_tmp"
        input = open(filename, 'rb')
        output = open(newfilename, 'wb')
        if self.verbose:
            print "Reading "+filename+" and writing to "+newfilename
        writer = csv.writer(output,delimiter='\t')
        for row in csv.reader(input,delimiter='\t'):
            if any(field.strip() for field in row):
                writer.writerow(row)
        input.close()
        output.close()
        return newfilename

    def addMissedCoding(self,filename):
        newfilename=filename+"_tmp"
        input = open(filename, 'rb')
        output = open(newfilename, 'wb')
        if self.verbose:
            print "Reading "+filename+" and writing to "+newfilename
        writer = csv.writer(output,delimiter='\t')
        new_row=[]
        for counter,row in enumerate(csv.reader(input,delimiter='\t')):
            if self.verbose:
                print "addMissedCoding-Processing "+str(row)
                new_row=row
                code=row[0]+"$"+row[2]+"$"+row[4]#self.edxUrlName(row[0],row[1],row[2])
                #new_row.insert(3,code)
                new_row.insert(0,code)
                writer.writerow(new_row)
        input.close()
        output.close()
        return newfilename

    def cleanTmp(self,c):
        for fl in glob(c+"_tmp*"):
            remove(fl)
