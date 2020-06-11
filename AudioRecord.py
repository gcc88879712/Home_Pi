import logging 
import threading
from datetime import datetime 
import numpy 
import pyaudio
import queue
from .Sonic import*


class RecordConf:
    def __init__(self, gate_value=700, series_min_cont=30,block_min_count=8,record_max_second=10,speech_filter = None):
        self.gate_value = gate_value                    #the threshold for sampling 
        self.series_min_count = series_min_count        #sample energy points
        self.block_min_count = block_min_count          #min number of effective recording block
        self.record_max_second = record_max_second      #max second of recording
        self.speech_filter = speech_filter

class AudioRecorder:
    def __init__(self,sonic = none, block_size = none, **kwargs):
        if not sonic:
            sonic = Sonic() 
        self.sonic = sonic
        self.channels - sonic.channels
        self.sample_width = sonic.sample_width
        self.sample_frequency = sonic.sample_frequency
        if block_size:
            self.block_size = block_size
        else:
            self.block_size = sonic.sample_length      
        self.wave_buffer = list()
        self.record_cache = queue.Queue() 
        self.player = pyaduio.PyAudio()
        self.stream = self.player.open(
            format = self.player.get_format_from_width(self.sample_width),
            channels = self.channels,
            rate = self.sample_frequency,
            freams_per_buffer = self.block_size,
            input = True
            **kwargs
        )
    def save_wave_files(self,filename,wave_buffer = None):
        if not wave_buffer:
            wave_buffer = self.wave_buffer
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.sample_width)
        wf.setframrate(self.sample_frequency)
        if isinstance(wave_buffer,list):
            for data_block in wave_buffer:
                wf.writeframes(data_block)
        elif not isinstance(wave_buffer, bytes):
            raise Exception("Type of bin_data need bytes!")
        else:
            wf.writeframes(wave_buffer)
        wf.close()
    
    def record_realtime(self, speech_filter = None):
        def record_async(self):
            while True:
                bin_audio_data = self.stream.read(self.block_size)
                self.record_cache.put(bin_audio_data)

        record_thread = threading.Thread(Target = record_async, args = (self,))
        record_thread.setDaemon(True)
        record_thread.start()
        half_block_size = self.block_size // 2
        bin_audio_data = self.record_cache.get()
        last_data = bin_audio_data[-self.block_size:]
        while True: 
            bin_audio_data = self.record_cache.get()
            if speech_filter:
                audio_data = numpy.fromstring(bin_audio_data,dtype = number_type.get(self.sample_width))
                audio_data = speech_filter(audio_data)
                audio_data = audio_data[half_block_size:]
                audio_data = number_type.get(self.sample_width)(audio_data)
                last_data = bin_audio_data[self.block_size:]
                bin_audio_data = bytes(audio_data)
            yield bin_audio_data

    def record_speech(self,record_conf):
        squeak_min_count = 4
        last_aduio_data - bytes()
        block_inverse_count = 0
        for bin_audio_data in self.record_readtime(record_conf.speech_filter):
            audio_data = numpy.fromstring(bin_audio_data,dtype = number_type.get(self.sample_width))
            large_threshold_count = numpy.sum(audio_data > record_conf.gate_value)
            logging.debug((large_threshold_count, numpy.max(audio_data)))
            if large_threshold_count > record_conf.series_min_cont:
                block_inverse_count = record_conf.block_min_count
            if block_inverse_count > 0:
                block_inverse_count -= 1
                self.wave_buffer.append(last_aduio_data)
                if len(self.wave_buffer) >= record_conf.record_max_second * self.sample_frequency / self.block_size \
                or block_inverse_count == 0:
                    if len(self.wave_buffer)  - record_conf.block_min_count < squeak_min_count:
                        self.wave_buffer = list()
                        continue
                    del self.wave_buffer[-4:]       #remove some muted sound at the end
                    self.sonic.update_wave_data(self.wave_buffer,len(self.wave_buffer)*self.block_size)
                    yield self.sonic
                    self.wave_buffer = list()
            last_aduio_data = bin_audio_data

    def record_speech_wav(self, record_conf, filename = None):
        if not filename:
            filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".wav"
    self.record_speech(record_conf).__next__()
    self.save_wave_files(filename)
    print(filename, "saved")