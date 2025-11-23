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

from abc import ABC, abstractmethod
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from pathlib import Path
from pytranscriber.control.ctr_engine import CtrEngine
import os

class ThreadExecGeneric(QThread):
    signalLockGUI = pyqtSignal()
    signalResetGUIAfterCancel = pyqtSignal()
    signalResetGUIAfterSuccess = pyqtSignal()
    signalProgress = pyqtSignal(str, int)
    signalProgressFileYofN = pyqtSignal(str)
    signalErrorMsg = pyqtSignal(str)

    def __init__(self, obj_transcription_parameters):
        self.obj_transcription_parameters = obj_transcription_parameters
        self.running = True
        QThread.__init__(self)

    def listenerProgress(self, string, percent):
        self.signalProgress.emit(string, percent)

    def _loopSelectedFiles(self):
        self.signalLockGUI.emit()
        #MessageUtil.show_info_message("loop selected files")

        langCode = self.obj_transcription_parameters.langCode

        #if output directory does not exist, creates it
        pathOutputFolder = Path(self.obj_transcription_parameters.outputFolder)

        if not os.path.exists(pathOutputFolder):
            os.mkdir(pathOutputFolder)
        #if there the output file is not a directory
        if not os.path.isdir(pathOutputFolder):
            #force the user to select a different output directory
            self.signalErrorMsg.emit("Error! Invalid output folder. Please choose another one.")
        else:
            #go ahead with autosub process
            nFiles = len(self.obj_transcription_parameters.listFiles)
            successful = 0
            skipped = 0
            failed = 0
            
            self.signalProgressFileYofN.emit(f"Starting batch processing of {nFiles} file(s)...")
            
            for i in range(nFiles):
                #does not continue the loop if user clicked cancel button
                if not CtrEngine.is_operation_canceled():
                    self._updateProgressFileYofN(i, nFiles)
                    
                    sourceFile = self.obj_transcription_parameters.listFiles[i]
                    outputFiles = self._generatePathOutputFile(sourceFile)
                    
                    # Check if already processed
                    was_already_processed = os.path.exists(outputFiles[0]) and os.path.exists(outputFiles[1])
                    
                    #MessageUtil.show_info_message("run engine for media")
                    self._run_engine_for_media(i, langCode)
                    
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
            if CtrEngine.is_operation_canceled():
                self.signalResetGUIAfterCancel.emit()
            else:
                # Show summary
                summary = f"Batch processing complete!\n\nSuccessful: {successful}\nSkipped: {skipped}\nFailed: {failed}\nTotal: {nFiles}"
                if failed > 0:
                    self.signalErrorMsg.emit(summary)
                else:
                    self.signalProgressFileYofN.emit(summary)
                self.signalResetGUIAfterSuccess.emit()

    @abstractmethod
    def _run_engine_for_media(self, index, langCode):
        pass

    def _updateProgressFileYofN(self, currentIndex, countFiles):
        self.signalProgressFileYofN.emit("File " + str(currentIndex + 1) + " of " + str(countFiles))

    def _generatePathOutputFile(self, sourceFile):
        # extract the filename without extension from the path
        base = os.path.basename(sourceFile)
        # [0] is filename, [1] is file extension
        fileName = os.path.splitext(base)[0]

        # the output file has same name as input file, located on output Folder
        # with extension .srt and .docx
        pathOutputFolder = Path(self.obj_transcription_parameters.outputFolder)
        outputFileSRT = pathOutputFolder / (fileName + ".srt")
        outputFileDOCX = pathOutputFolder / (fileName + ".docx")
        return [outputFileSRT, outputFileDOCX]

    @staticmethod
    def cancel():
        CtrEngine.cancel_operation()
