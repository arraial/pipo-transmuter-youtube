#!usr/bin/env python3

### Test Suite ###
TEST_ENVIRONMENT = "test"

### MusicQueue  ###
SHORT_TIMEOUT = 5  # seconds
MEDIUM_TIMEOUT = 10  # seconds
LONG_TIMEOUT = 20  # seconds
TIME_TO_FETCH_MUSIC = 8  # seconds
EMPTY_MUSIC = ""

### Player ###

# Youtube
YOUTUBE_URL_NO_HTTPS = "http://www.youtube.com/watch?v=1V_xRb0x9aw"
YOUTUBE_URL_HTTPS = "https://www.youtube.com/watch?v=1V_xRb0x9aw"
YOUTUBE_URL_1 = "https://www.youtube.com/watch?v=1V_xRb0x9aw"
YOUTUBE_URL_2 = "https://www.youtube.com/watch?v=imSefM4GPpE"
YOUTUBE_URL_3 = "https://www.youtube.com/watch?v=04mfKJWDSzI"
YOUTUBE_URL_4 = "https://www.youtube.com/watch?v=04WuoQMhhxw"
YOUTUBE_URL_5 = "https://www.youtube.com/watch?v=LFTE4W--Htk"
YOUTUBE_URL_SINGLE_ELEMENT_LIST = [
    YOUTUBE_URL_1,
]
YOUTUBE_URL_SIMPLE_LIST = [
    YOUTUBE_URL_1,
    YOUTUBE_URL_2,
    YOUTUBE_URL_3,
]
YOUTUBE_URL_COMPLEX_LIST = [
    YOUTUBE_URL_1,
    YOUTUBE_URL_2,
    YOUTUBE_URL_3,
    YOUTUBE_URL_4,
    YOUTUBE_URL_5,
]
YOUTUBE_PLAYLIST_CONTENT_1 = "https://www.youtube.com/watch?v=ZtKX0NBpYgs"
YOUTUBE_PLAYLIST_SOURCE_1 = (
    "https://www.youtube.com/playlist?list=PL6_qhP3eWX5O0ELIV_eJzf6cJ4Yix5D7U"
)
YOUTUBE_PLAYLIST_1 = "https://www.youtube.com/watch?v=ZtKX0NBpYgs&list=PL6_qhP3eWX5O0ELIV_eJzf6cJ4Yix5D7U"
YOUTUBE_PLAYLIST_SOURCE_2 = (
    "https://www.youtube.com/playlist?list=PLhpLyZ-aL82gssiK-uYP71UD5vgm_T-ZK"
)
YOUTUBE_PLAYLIST_2 = "https://www.youtube.com/watch?v=sgLvV2pX9V0&list=PLhpLyZ-aL82gssiK-uYP71UD5vgm_T-ZK"
YOUTUBE_PLAYLIST_SOURCE_3 = (
    "https://www.youtube.com/playlist?list=PLh_2AL0cs37xUwRGScAmHpCY_vxKlgqRB"
)
YOUTUBE_PLAYLIST_3 = "https://www.youtube.com/watch?v=_-uMPb63e8U&list=PLh_2AL0cs37xUwRGScAmHpCY_vxKlgqRB"
YOUTUBE_QUERY_0 = ""
YOUTUBE_QUERY_1 = "yellow submarine"
YOUTUBE_QUERY_SOURCE_1 = (
    "https://www.youtube.com/watch?v=m2uTFF_3MaA"  # The Beatles - Yellow Submarine
)
YOUTUBE_QUERY_2 = "eye of the tiger"
YOUTUBE_QUERY_SOURCE_2 = (
    "https://www.youtube.com/watch?v=btPJPFnesV4"  # Survivor - Eye Of The Tiger
)
