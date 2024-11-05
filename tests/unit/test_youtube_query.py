import pytest

import tests.constants
from pipo_transmuter_youtube.handler import YoutubeQueryHandler


@pytest.mark.unit
@pytest.mark.youtube
class TestYoutubeQuerySource:
    @pytest.fixture(scope="function", autouse=True)
    def music_handler(self, mocker):
        return YoutubeQueryHandler()

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("/", "/"),
            ("//", "//"),
            (" ", "%20"),
            ("á", "%C3%A1"),
            ("ç", "%C3%A7"),
            ("ö", "%C3%B6"),
        ],
    )
    def test_url_encoding(self, music_handler, url, expected):
        assert music_handler.encode_url(url) == expected

    async def test_empty_query(self, music_handler):
        music = await music_handler.url_from_query("")
        assert music == None

    @pytest.mark.parametrize(
        "query",
        [
            tests.constants.YOUTUBE_QUERY_1,
            tests.constants.YOUTUBE_QUERY_2,
        ],
    )
    @pytest.mark.asyncio
    async def test_query(self, music_handler, query):
        music = await music_handler.url_from_query(query)
        assert music
