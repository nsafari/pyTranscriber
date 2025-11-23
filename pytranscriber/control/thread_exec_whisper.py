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

from pytranscriber.control.ctr_whisper import CtrWhisper
from pytranscriber.control.thread_exec_generic import ThreadExecGeneric
from pytranscriber.util.util import MyUtil
import traceback


class Thread_Exec_Whisper(ThreadExecGeneric):

    def run(self):
        CtrWhisper.init()
        super()._loopSelectedFiles()
        self.running = False

    def _run_engine_for_media(self, index, langCode):
        import os
        sourceFile = self.obj_transcription_parameters.listFiles[index]
        outputFiles = self._generatePathOutputFile(sourceFile)
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

        fOutput = None
        try:
            fOutput = CtrWhisper.generate_subtitles(source_path=sourceFile,
                                                              outputSRT=outputFileSRT,
                                                              outputDOCX=outputFileDOCX,
                                                              src_language=langCode,
                                                              model=self.obj_transcription_parameters.get_model_whisper())
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

            if self.obj_transcription_parameters.boolOpenOutputFilesAuto:
                #open both SRT and DOCX output files
                try:
                    MyUtil.open_file(outputFileDOCX)
                    MyUtil.open_file(outputFileSRT)
                except Exception as e:
                    # Don't fail the whole process if opening files fails
                    pass