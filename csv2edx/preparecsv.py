#!/bin/python

import csv
from shutil import move
from os import remove
from glob import glob

MATE_ORIGINAL="mate/MOOCs Mate albero materia - riepilogo.tsv"
FISICA_ORIGINAL="fisica/fisica-1.tsv"

COURSES=[MATE_ORIGINAL,FISICA_ORIGINAL]
COLUMNS_NEEDED={MATE_ORIGINAL:[0,1,2,4,8],FISICA_ORIGINAL:[0,1,2,6]}
deleteTmpFiles=True

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
        tmpfile=self.removeUnusedColums(fn)
        tmpfile=self.stripEmptyRows(tmpfile)
        tmpfile=self.addEmptyElements(tmpfile)
        tmpfile=self.addMissedCoding(tmpfile)
        
        preparedFileName=fn+".PREPARED"
        move(tmpfile,preparedFileName)
        
        if not self.verbose:
            self.cleanTmp(fn)
            
        return preparedFileName
        
    def edxUrlName(self,chapterName,sequentialName,verticalName):
        return "W"+chapterName[0]+"M"+sequentialName[0]+verticalName[:2]
    
    def addEmptyElements(self,filename):
        newfilename=filename+"_tmp"
        input = open(filename, 'rb')
        output = open(newfilename, 'wb')
        if self.verbose:
            print "Reading "+filename+" and writing to "+newfilename
        writer = csv.writer(output,delimiter='\t')
        previous_row=[]
        for counter,row in enumerate(csv.reader(input,delimiter='\t')):    
                new_row=[]
                for idx,col in enumerate(row):
                    
                    if (any(col)):                    
                        new_row.insert(idx,col)
                    else:
                        if (idx<=2): # automatic inser only for chapter and sequencial name column
                            new_row.insert(idx,previous_row[idx])
                        
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
                new_row=row
                if (len(row)<5):   #missed code and maybe url video
                    code=self.edxUrlName(row[0],row[1],row[2])
                    new_row.insert(3,code)
                    
                writer.writerow(new_row)
        input.close()
        output.close()
        return newfilename

    def cleanTmp(self,c):
        if (deleteTmpFiles):
            for fl in glob(c+"_tmp*"):
                remove(fl)
            

    