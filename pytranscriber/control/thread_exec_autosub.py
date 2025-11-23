'''
   (C) 2025 Raryel C. Souza
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from pathlib import Path
from pytranscriber.util.srtparser import SRTParser
from pytranscriber.util.util import MyUtil
from pytranscriber.control.ctr_autosub import Ctr_Autosub
import os
import traceback


class Thread_Exec_Autosub(QThread):
    signalLockGUI = pyqtSignal()
    signalResetGUIAfterCancel = pyqtSignal()
    signalResetGUIAfterSuccess = pyqtSignal()
    signalProgress = pyqtSignal(str, int)
    signalProgressFileYofN = pyqtSignal(str)
    signalErrorMsg = pyqtSignal(str)

    def __init__(self, objParamAutosub):
        self.objParamAutosub = objParamAutosub
        self.running = True
        QThread.__init__(self)

    def __updateProgressFileYofN(self, currentIndex, countFiles ):
        self.signalProgressFileYofN.emit("File " + str(currentIndex+1) + " of " +str(countFiles))

    def listenerProgress(self, string, percent):
        self.signalProgress.emit(string, percent)

    def __generatePathOutputFile(self, sourceFile):
        #extract the filename without extension from the path
        base = os.path.basename(sourceFile)
        #[0] is filename, [1] is file extension
        fileName = os.path.splitext(base)[0]

        #the output file has same name as input file, located on output Folder
        #with extension .srt and .docx
        pathOutputFolder = Path(self.objParamAutosub.outputFolder)
        outputFileSRT = pathOutputFolder / (fileName + ".srt")
        outputFileDOCX = pathOutputFolder / (fileName + ".docx")
        return [outputFileSRT, outputFileDOCX]

    def __runAutosubForMedia(self, index, langCode):
        sourceFile = self.objParamAutosub.listFiles[index]
        outputFiles = self.__generatePathOutputFile(sourceFile)
        outputFileSRT = outputFiles[0]
        outputFileDOCX = outputFiles[1]

        # Check if output files already exist - skip if they do
        if os.path.exists(outputFileSRT) and os.path.exists(outputFileDOCX):
            file_name = os.path.basename(sourceFile)
            self.listenerProgress(f"Skipping {file_name} (already processed)", 100)
            self.signalProgressFileYofN.emit(f"File {index+1}: {file_name} - SKIPPED (already exists)")
            return

        # Show current file being processed
        file_name = os.path.basename(sourceFile)
        self.signalProgressFileYofN.emit(f"File {index+1}: Processing {file_name}...")
        self.listenerProgress(f"Processing: {file_name}", 0)

        #run autosub
        fOutput = None
        try:
            fOutput = Ctr_Autosub.generate_subtitles(source_path = sourceFile,
                                        output = outputFileSRT,
                                        src_language = langCode,
                                        listener_progress = self.listenerProgress, proxies=self.objParamAutosub.proxies)
        except Exception as e:
            error_msg = f"""Error processing {file_name}:\n{traceback.format_exc()}\n\nContinuing with next file..."""
            self.signalErrorMsg.emit(error_msg)  # Emit the full traceback
            # Continue processing other files even if this one fails
            return

        #if nothing was returned
        if not fOutput:
            self.signalErrorMsg.emit(f"Error! Unable to generate subtitles for {file_name}. Continuing with next file...")
        elif fOutput != -1:
            #if the operation was not canceled

            #updated the progress message
            self.listenerProgress(f"Finished: {file_name}", 100)

            #parses the .srt subtitle file and export text to .docx file
            try:
                SRTParser.extractTextFromSRT(str(outputFileSRT))
            except Exception as e:
                self.signalErrorMsg.emit(f"Warning: Could not extract text from {file_name}: {str(e)}")

            if self.objParamAutosub.boolOpenOutputFilesAuto:
                #open both SRT and DOCX output files
                try:
                    MyUtil.open_file(outputFileDOCX)
                    MyUtil.open_file(outputFileSRT)
                except Exception as e:
                    # Don't fail the whole process if opening files fails
                    pass

    def __loopSelectedFiles(self):
        self.signalLockGUI.emit()

        langCode = self.objParamAutosub.langCode

        #if output directory does not exist, creates it
        pathOutputFolder = Path(self.objParamAutosub.outputFolder)

        if not os.path.exists(pathOutputFolder):
            os.mkdir(pathOutputFolder)
        #if there the output file is not a directory
        if not os.path.isdir(pathOutputFolder):
            #force the user to select a different output directory
            self.signalErrorMsg.emit("Error! Invalid output folder. Please choose another one.")
        else:
            #go ahead with autosub process
            nFiles = len(self.objParamAutosub.listFiles)
            successful = 0
            skipped = 0
            failed = 0
            
            self.signalProgressFileYofN.emit(f"Starting batch processing of {nFiles} file(s)...")
            
            for i in range(nFiles):
                #does not continue the loop if user clicked cancel button
                if not Ctr_Autosub.is_operation_canceled():
                    self.__updateProgressFileYofN(i, nFiles)
                    
                    sourceFile = self.objParamAutosub.listFiles[i]
                    outputFiles = self.__generatePathOutputFile(sourceFile)
                    
                    # Check if already processed
                    was_already_processed = os.path.exists(outputFiles[0]) and os.path.exists(outputFiles[1])
                    
                    self.__runAutosubForMedia(i, langCode)
                    
                    # Count results after processing
                    if was_already_processed:
                        skipped += 1
                    elif os.path.exists(outputFiles[0]) and os.path.exists(outputFiles[1]):
                        successful += 1
                    else:
                        failed += 1
                else:
                    break

            #if operation is canceled does not clear the file list
            if Ctr_Autosub.is_operation_canceled():
                self.signalResetGUIAfterCancel.emit()
            else:
                # Show summary
                summary = f"Batch processing complete!\n\nSuccessful: {successful}\nSkipped: {skipped}\nFailed: {failed}\nTotal: {nFiles}"
                if failed > 0:
                    self.signalErrorMsg.emit(summary)
                else:
                    self.signalProgressFileYofN.emit(summary)
                self.signalResetGUIAfterSuccess.emit()


    def run(self):
        Ctr_Autosub.init()
        self.__loopSelectedFiles()
        self.running = False

    def cancel(self):
       Ctr_Autosub.cancel_operation()
