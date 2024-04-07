from enum import Enum

#定义一个枚举类
class PageType(Enum):
    VIDEO ='video'
    IMAGE = 'image'
    CONTENT = 'content'
    DOCUMENT = 'document'
    JS = 'js'
    EXECUTABLE = 'executable'
    ARCHIVE = 'archive'
    AUDIO = 'audio'
    OTHER = 'other'

