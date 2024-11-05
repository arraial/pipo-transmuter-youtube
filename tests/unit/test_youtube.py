import pytest

import pipo_transmuter_youtube
import tests.constants


@pytest.mark.wip
@pytest.mark.unit
@pytest.mark.query
class TestYoutubeSource:
    @pytest.fixture(scope="function", autouse=True)
    def music_handler(self, mocker):
        return pipo_transmuter_youtube.handler.YoutubeHandler()

    def test_empty_url(self, music_handler):
        assert not music_handler.get_audio("")

    @pytest.mark.parametrize(
        "url",
        [
            tests.constants.YOUTUBE_URL_1,
            tests.constants.YOUTUBE_URL_2,
            tests.constants.YOUTUBE_URL_3,
            tests.constants.YOUTUBE_URL_4,
            tests.constants.YOUTUBE_URL_5,
        ],
    )
    def test_url(self, music_handler, url):
        assert music_handler.get_audio(url)
