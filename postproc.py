import shutil
import numpy as np
import matplotlib.pyplot as plt 
import pyfits as py
import argparse
import ConfigParser
import glob, sys, datetime, getopt
import os
import subprocess
import diffimg
import easyaccess
import numpy as np
import HTML
###FOR TESTING PURPOSES###
### 475914 475915 475916 476960 476961 476962 482859 482860 482861 ###
###SEASON= 46###
#Read User input#
def image(text, url):
    return "<center>%s</center><img src='%s'>" % (text, url)

print "Read user input"

### WE NEED EXPLIST TO ENSURE ALL EXPOSURE NUMBERS ARE ACCOUNTED FOR ###
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('--expnums', metavar='e',type=int, nargs='+', help='List of Exposures', default= [476960])

parser.add_argument('--outputdir', metavar='d', type=str, help='Directory location of output files', default= "testevent")

parser.add_argument('--season', help='season is required', default=107, type=int)

parser.add_argument('--mjdtrigger', type = float, help= 'Input MJD Trigger', default = 0)

args = parser.parse_args()
expnums = args.expnums
print args.expnums
print args.outputdir

outdir = str(args.outputdir)

if not os.path.exists(outdir):
    os.mkdir(outdir) 

if not os.path.exists(outdir + '/' + 'stamps'):
    os.mkdir(outdir + '/' + 'stamps')

if not os.path.exists(outdir + '/' + 'plots'):
    os.mkdir(outdir + '/' + 'plots')

outplots = outdir + '/' + 'plots'
outstamps = outdir + '/' + 'stamps'

print "Read environment variables"

forcedir = os.environ["TOPDIR_SNFORCEPHOTO_IMAGES"]

season= os.environ["SEASON"]
run = "dp"+str(season)

#print season

#Read Config File#

print "Read config file"

config = ConfigParser.ConfigParser()
inifile = config.read('./postproc.ini')[0]

expdir = config.get('data', 'exp')
ncore = config.get('GWFORCE', 'ncore')
numepochs_min = config.get('GWFORCE', 'numepochs_min')
writeDB = config.get('GWFORCE', 'writeDB')

format= config.get('GWmakeDataFiles', 'format')
numepochs_min = config.get('GWmakeDataFiles', 'numepochs_min')
trigger = config.get('GWmakeDataFiles', '2nite_trigger')
outFile_stdoutreal = config.get('GWmakeDataFiles-real', 'outFile_stdout')
outDir_datareal = config.get('GWmakeDataFiles-real', 'outDir_data')
outFile_stdoutfake = config.get('GWmakeDataFiles-fake', 'outFile_stdout')
outDir_datafake = config.get('GWmakeDataFiles-fake', 'outDir_data')
fakeversion = config.get('GWmakeDataFiles-fake', 'version')


print "Check RUNMON outputs"

#expnumlist = args.expnums
### Query this from database ###

#Read in and locate files#
for expnum in args.expnums: 
    e=str(expnum)
    print "Check dir content for exposure " +e
    d= expdir+"/*/"+e+"/"+run
    runmonlog=d+"RUNMON*.LOG"
    nfiles= len(glob.glob(runmonlog))
    if nfiles != 1:
        print "runmonlog for exposure" + e + " not found"
        sys.exit(1)
###Think about what to do in the case that the file is not found###
    psf= forcedir+"/*/*"+e+"*.psf"
    diff = forcedir+"/*/*"+e+"*_diff.fits"
    diffmh = forcedir+"/*/*"+e+"*_diff_mh.fits"

    for filetype in (psf, diff, diffmh):
        if len(glob.glob(filetype)) == 0 :
            print "files not found"

print "Run GWFORCE"

#run "gwforce" section#
#forcePhoto_master.pl     \
#   -season         107   \
#   -numepochs_min  0     \
#   -ncore          4     \
#   -writeDB 

a= 'forcePhoto_master.pl ' + ' -season ' +str(season) + ' -numepochs_min ' +numepochs_min + ' -ncore ' +ncore

if writeDB == "on":
    a = a+ ' -writeDB ' 

print a
subprocess.call(a, shell=True)


####run "gwhostmatch" section (if time allows)#


print "Run GWmakeDataFiles - real"

#run "Gwmakedatafiles" section#

#makeDataFiles_fromSNforce \
#   -format snana \
#   -season 201     \
#   -numepochs_min 0 \
#   -2nite_trigger iz \
#   -outFile_stdout  makeDataFiles_real.stdout  \
#   -outDir_data   GWevent2_numepoch1_iz_real_text \

b= 'makeDataFiles_fromSNforce' + ' -format ' +format + ' -numepochs_min ' +numepochs_min + ' -2nite_trigger ' +trigger + ' -outFile_stdout ' +outFile_stdoutreal + ' -outDir_data ' +outDir_datareal

print b 
subprocess.call(b, shell=True)

print "Run GWmakeDataFiles - fake"

b= 'makeDataFiles_fromSNforce' + ' -format ' +format + ' -numepochs_min ' +numepochs_min + ' -2nite_trigger ' +trigger + ' -outFile_stdout ' +outFile_stdoutfake + ' -outDir_data ' +outDir_datafake + ' -fakeVersion ' +fakeversion

print b
subprocess.call(b, shell=True)


#Produce Truth Table for Fakes#
explist=','.join(map(str,expnums))

# the database where diffimg outputs are stored                                 
db='destest'
schema = 'marcelle'

# the query you want to run to get the truth table data                         
query='select distinct SNFAKE_ID, EXPNUM, CCDNUM, TRUEMAG, TRUEFLUXCNT, FLUXCNT, BAND, NITE, MJD from '+ schema +'.SNFAKEIMG where EXPNUM IN ('+explist+') order by SNFAKE_ID'

# the file where you want to save the truth table                               
filename= config.get('GWmakeDataFiles-fake', 'fake_input')

connection=easyaccess.connect(db)
connection.query_and_save(query,filename)
connection.close()

### FOR THE FIRST RUN EXIT HERE TO LEARN NAMES OF VALUES WE NEED###

exit 

print "Plot efficiency"

#Make plots Section#
###Plot1 Efficiency Plot ###
###Plot5 Magerror Distribution ###
###Plots should include all bands###

reals = diffimg.DataSet(outDir_datareal, label = 'reals')
fakes = diffimg.DataSet(outDir_datafake, label = 'fakes')
###Need to generate fakes input on own###
fakes.get_fakes_input(config.get('GWmakeDataFiles-fake', 'fake_input'))
truth = fakes.fakes_input

rdatag = reals.set_mask(PHOTFLAG_bit=4096)
fdatag = fakes.set_mask(PHOTFLAG_bit=4096)

bins = bins = np.arange(17,25,0.5)

###Generalize code to handle all bands/any combo of bands###

fmaski = (fdatag.BAND=='i')
fmaskz = (fdatag.BAND=='z')
tmaski = (truth.BAND == 'i')
tmaskz = (truth.BAND == 'z')

f_ihist, bin_edges = np.histogram(fdatag.SIMMAG[fmaski],bins=bins)
f_zhist, bin_edges = np.histogram(fdatag.SIMMAG[fmaskz],bins=bins)

t_ihist, bin_edges = np.histogram(truth.TRUEMAG[tmaski], bins=bins)
t_zhist, bin_edges = np.histogram(truth.TRUEMAG[tmaskz], bins=bins)

plt.figure()
plt.plot(bins[1:], f_ihist*100.0/t_ihist, label= 'i-band', lw=4, color='orange')
plt.plot(bins[1:], f_zhist*100.0/t_zhist,label='z-band',lw=4,color='darkblue')
plt.scatter(bins[1:], f_ihist*100.0/t_ihist,lw=4,color='orange')
plt.scatter(bins[1:], f_zhist*100.0/t_zhist,lw=4,color='darkblue')
plt.title('Efficiency: Blue = z  Orange = i')
plt.xlabel('Magnitude')
plt.ylabel('Percent Found')
plt.savefig(outplots + '/'+'efficiency.pdf')
plt.clf()

print "Plot DeltaMag/MAGERR histogram"

#Histogram of DeltaMag/MAGERR#

deltai = fdatag.MAG[fmaski] - fdatag.SIMMAG[fmaski]
deltaz = fdatag.MAG[fmaskz] - fdatag.SIMMAG[fmaskz]
deltaiovererr = deltai/(fdatag.MAGERR[fmaski])
deltazovererr = deltaz/(fdatag.MAGERR[fmaskz])
bins2 = np.arange(-30,30,.1)
iweights = np.ones_like(deltaiovererr)/float(len(deltaiovererr))
zweights = np.ones_like(deltazovererr)/float(len(deltazovererr))

deltaiovererr_hist, bin_edges= np.histogram(deltaiovererr, weights= iweights, bins=bins2)
deltazovererr_hist, bin_edges= np.histogram(deltazovererr, weights= zweights, bins=bins2)

plt.figure()
plt.plot(bins2[1:], deltaiovererr_hist, label= 'i-band', lw=3, color='orange')
plt.plot(bins2[1:], deltazovererr_hist, label= 'z-band', lw=3, color='blue')
plt.title('Delta Mag over Mag Error')
plt.ylabel('Percent of Total')
plt.savefig(outplots +'/'+'DeltaoverERR.pdf')
plt.clf()

print "Number of candidates per ccd"
#Plot Candidates per CCD #

x = np.zeros(len(np.unique(reals.data.SNID)))
y = np.unique(reals.data.SNID)
for i in np.arange(len(x)):
    x[i] =reals.data.CCDNUM[reals.data.SNID==y[i]][1]

plt.hist(x, bins= np.arange(min(reals.data.CCDNUM), max(reals.data.CCDNUM) +2 ,1), color='orange')
plt.title('Hist of real candidates per CCD')
plt.ylabel('Number of Real Candidates')
plt.xlabel('CCD Number')
plt.savefig(outplots +'/'+'Hist_of_real_candidates_per_CCD.pdf')
plt.clf()

x = np.zeros(len(np.unique(fakes.data.SNID)))
y = np.unique(fakes.data.SNID)
for i in np.arange(len(x)):
    x[i] =fakes.data.CCDNUM[fakes.data.SNID==y[i]][1]


plt.hist(x, bins= np.arange(min(reals.data.CCDNUM), max(reals.data.CCDNUM) +2,1),color = 'orange')
plt.title('Hist of fake candidates per CCD')
plt.ylabel('Number of Fake Candidates')
plt.xlabel('CCD Number')
plt.savefig(outplots +'/'+'Hist_of_fake_candidates_per_CCD.pdf')
plt.clf()

print "Save candidates info"
###Write data files for each candidate including info discussed###



rID= reals.data.SNID
urID= np.unique(rID)
numofcan = len(urID)
realss = reals.data

f1= open(str(outdir)+'/'+'allcandidates.txt', 'w')
header1 = 'SNID, ' + ' RA, ' + ' DEC, ' + ' CandType,' +  ' NumEpochs, ' + ' NumEpochsml, ' + ' LatestNiteml' 
f1.write(header1)
for i in range(0,numofcan):
    Cand =(reals.data.SNID == urID[i])
    #Making Plot of Flux vs MJD for each Candidate#
    Flux = realss.FLUXCAL 
    MJD = realss.MJD
    Fluxerr = realss.FLUXCALERR
    plt.scatter(MJD[Cand],Flux[Cand], color = 'red')
    plt.errorbar(MJD[Cand],Flux[Cand], yerr=FluxErr[Cand], ls = 'none')
    plt.xlabel('MJD')
    plt.ylabel('Flux')
    plt.title('Flux vs. MJD for candidate' + str(int(urID[i])))
    plt.savefig(outdir + '/plots/lightcurves/FluxvsMJD_for_cand_' + str(int(urID[i])) + '.pdf')
    plt.clf()             
    #Finished Making plot of Flux vs MJD for each Candidate#
    line = str(urID[i]) + ", " + str(reals.data.RA[Cand][1]) + ", " + str(reals.data.DEC[Cand][1]) + ", " + str(reals.data.CandType[Cand][1]) + ", " + str(reals.data.NumEpochs[Cand][1]) + ", " + str(reals.data.NumEpochsml[Cand][1]) + ", " + str(reals.data.LatestNiteml[Cand][1]) + "\n"
    table1 = np.array([[int(urID[i]),reals.data.RA[Cand][1],reals.data.DEC[Cand][1],int(reals.data.CandType[Cand][1]),int(reals.data.NumEpochs[Cand][1]),int(reals.data.NumEpochsml[Cand][1]),int(reals.data.LatestNiteml[Cand][1])]])
    print table1
    f1.write(line)
    filename = 'Candidate_'+str(int(urID[i])) + '.txt'
    htmlfilename = 'Candidate_'+str(int(urID[i])) + '.html'
    header ='BAND ' + 'x ' + 'y ' + 'Mag ' + 'Nite ' + 'MJD ' + 'Season ' + 'Object ' + 'Exposure ' + 'Field ' + 'CCDNUM'
    nobs = len(reals.data.BAND[Cand])
    seasoncol = np.ones((nobs,), dtype = np.int)*int(season)
    print seasoncol
    table = np.column_stack((reals.data.BAND[Cand], reals.data.XPIX[Cand], reals.data.YPIX[Cand], reals.data.MAG[Cand], reals.data.NITE[Cand], reals.data.MJD[Cand], seasoncol))
    np.savetxt(str(outdir)+'/'+filename, table, fmt = '%s', header = header)
    htmlcode = HTML.table(table.tolist(),header_row = header.split(' '))
    htmlcode1 = HTML.table(table1.tolist(), header_row = header1.split(', '))
    f = open(str(outdir)+ '/'+  htmlfilename, 'w')
    f.write(htmlcode1)
    f.write(htmlcode)
    #Collect Stamps for observations of this candidate#
    thiscand_stampsdir = outstamps  + '/' + str(int(urID[i]))
    if not os.path.exists(thiscand_stampsdir):
        os.mkdir(thiscand_stampsdir)
#Create Stamps_table with 8 columns and nobs rows all empty#
    stampstable = ([[None]*8])
    stampsheader = 'Filter, ' + 'Object ID, ' + 'Nite, ' + 'MJD, ' + 'Search, ' + 'Template, ' + 'Difference, ' + 'AutoScan Score,'
    for j in range(0,nobs):
        thisobs_nite = str(int(realss.NITE[Cand][j]))
        thisobs_band = realss.BAND[Cand][j]
        ccdnum = realss.CCDNUM[Cand][j]
#        expdir = "/data/des41.a/data/marcelle/diffimg/local-runs"
        thisobs_ID = realss.OBSID[Cand][j]
        a = expdir + '/' + thisobs_nite + '/*/dp' + str(season) + '/' + thisobs_band + '_' + str(ccdnum) + '/stamps*'
        print a
        thisobs_stampsdir = glob.glob(a)[0]
        print thisobs_stampsdir
        filenamediff = thisobs_stampsdir + '/diff' + str(thisobs_ID) + '.gif'
        filenamesrch = thisobs_stampsdir + '/srch' + str(thisobs_ID) + '.gif'
        filenametemp = thisobs_stampsdir + '/temp' + str(thisobs_ID) + '.gif' 
        shutil.copy(filenamediff, thiscand_stampsdir)
        shutil.copy(filenamesrch, thiscand_stampsdir)
#        shutil.copy(filenametemp, thiscand_stampsdir)
        path1 = thiscand_stampsdir + '/srch' + str(thisobs_ID) + '.gif'
        print path1
        search= image('', 'stamps/' + str(int(urID[i]))  + '/srch' + str(thisobs_ID) + '.gif')
        temp  = image('', 'stamps/' + str(int(urID[i])) + '/temp' + str(thisobs_ID) + '.gif')
        diff  = image('', 'stamps/' + str(int(urID[i])) + '/diff' + str(thisobs_ID) + '.gif')
#Replace in the empty spaces in table with values/pictures#
        stampstable[j][0] = realss.BAND[Cand][j]
        stampstable[j][1] = "Obs ID Goes here"
        stampstable[j][2] = realss.NITE[Cand][j]
        stampstable[j][3] = realss.MJD[Cand][j]
        stampstable[j][4] = search
        stampstable[j][5] = "temp goes here"
        stampstable[j][5] = temp
        stampstable[j][6] = diff
        stampstable[j][7] = realss.PHOTPROB[Cand][j]
        stampstable.append([None] * 8)
    htmlcode2 = HTML.table(stampstable, header_row= stampsheader.split(', '))
    f.write(htmlcode2)
                     
f1.close()  
    
print "SUCCESS"    





#Save output files in specific and organized directories#

###Setup a display of the search, template and difference images for each candidate. Automatically save for top n candidates. Give option to user to pick candidate by ID to display###
