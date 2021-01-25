import click
from typing import List
from .segment import Segment
from ..extractors.hls.ext.xkey import XKey
from ..extractors.hls.ext.xmedia import XMedia
from ..extractors.hls.ext.xdaterange import XDateRange
from ..extractors.hls.ext.xstream_inf import XStreamInf
from ..extractors.hls.ext.xprogram_date_time import XProgramDateTime


class Stream:
    '''
    自适应流的具体实现，HLS/DASH等，为了下载对应的流，
    每一条流应当具有以下基本属性：
    - 名称
    - 分段链接列表
    - 分辨率
    - 码率
    - 时长
    - 编码
    一些可选的属性
    - 语言
    '''
    def __init__(self, name: str, stream_type: str):
        self.name = name
        self.segments = [] # type: List[Segment]
        self.duration = 0.0
        self.filesize = 0
        self.lang = ''
        # <---解析过程中需要设置的属性--->
        self.program_id = None # type: int
        self.bandwidth = None # type: int
        self.average_bandwidth = None # type: int
        self.size = None # type: int
        self.fps = None # type: int
        self.resolution = None # type: str
        self.codecs = None # type: str
        self.quality = None # type: str
        self.stream_type = None # type: str
        self.xkeys = [] # type: List[XKey]
        self.xmedias = [] # type: List[XMedia]
        # 初始化默认设定流类型
        self.set_straem_type(stream_type)
        # 初始化默认设定一个分段
        self.append_segment()

    def segments_extend(self, segments: List[Segment]):
        '''
        由#EXT-X-DISCONTINUITY引起的合并 需要更新一下新增分段的文件名
        '''
        offset = len(self.segments)
        for segment in segments:
            segment.add_offset_for_name(offset)
        self.segments.extend(segments)

    def set_name(self, name: str):
        self.name = name
        return self

    def set_tag(self, tag: str):
        self.tag = tag

    def calc(self):
        self.calc_duration()
        self.calc_filesize()

    def calc_duration(self):
        for segment in self.segments:
            self.duration += segment.duration

    def calc_filesize(self):
        for segment in self.segments:
            self.filesize += segment.filesize
        self.filesize = self.filesize / 1024 / 1024

    def read_stream_header(self):
        '''
        读取一部分数据 获取流的信息
        '''
        pass

    def dump_segments(self):
        '''
        将全部分段保存到本地
        '''
        click.secho(
            f'dump {len(self.segments)} segments\n\t'
            f'duration -> {self.duration:.2f}s\n\t'
            f'filesize -> {self.filesize:.2f}MB'
        )

    def append_segment(self):
        '''
        新增一个分段
        '''
        segment = Segment().set_index(len(self.segments)).set_suffix('.ts').set_folder(self.name)
        self.segments.append(segment)

    def set_straem_type(self, stream_type: str):
        self.stream_type = stream_type

    def set_xstream_inf(self, line: str):
        self.xstream_inf = XStreamInf().set_attrs_from_line(line)

    def set_url(self, home_url: str, base_url: str, line: str):
        if line.startswith('http://') or line.startswith('https://') or line.startswith('ftp://'):
            self.origin_url = line
        elif line.startswith('/'):
            self.origin_url = f'{home_url}/{line}'
        else:
            self.origin_url = f'{base_url}/{line}'

    def set_key(self, home_url: str, base_url: str, line: str):
        self.xkeys.append(XKey().set_key(home_url, base_url, line))

    def set_media(self, home_url: str, base_url: str, line: str):
        self.xmedia = XMedia().set_attrs_from_line(line)
        self.xmedia.uri = self.set_origin_url(home_url, base_url, self.xmedia.uri)

    def set_origin_url(self, home_url: str, base_url: str, uri: str):
        # 某些标签 应该被视作一个新的Stream 所以要设置其对应的原始链接
        if uri.startswith('http://') or uri.startswith('https://') or uri.startswith('ftp://'):
            self.origin_url = uri
        elif uri.startswith('/'):
            self.origin_url = f'{home_url}/{uri}'
        else:
            self.origin_url = f'{base_url}/{uri}'
        return self.origin_url

    def set_daterange(self, line: str):
        self.xdaterange = XDateRange().set_attrs_from_line(line)

    def set_xprogram_date_time(self, line: str):
        self.xprogram_date_time = XProgramDateTime().set_attrs_from_line(line)