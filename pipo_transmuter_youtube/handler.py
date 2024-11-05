import re
import httpx
import yt_dlp
from enum import StrEnum
import logging
from typing import Iterator, Optional
from dataclasses import dataclass

from requests.utils import requote_uri

from pipo_transmuter_youtube.config import settings


class YoutubeOperations(StrEnum):
    """Youtube operation types."""

    URL = "url"
    PLAYLIST = "playlist"
    QUERY = "query"


class YoutubeHandler:
    """Handles youtube url music."""

    @staticmethod
    def parse_playlist(url: str) -> Iterator[str]:
        try:
            with yt_dlp.YoutubeDL(
                settings.player.source.youtube.playlist_parser_config
            ) as ydl:
                playlist_id = ydl.extract_info(url=url, download=False).get("id")
                playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                for url in ydl.extract_info(url=playlist_url, download=False).get(
                    "entries"
                ):
                    yield url.get("url")
        except yt_dlp.utils.DownloadError:
            logging.getLogger(__name__).exception(
                "Unable to obtain information from youtube"
            )

    @staticmethod
    def get_audio(query: str) -> Optional[str]:
        """Obtain a youtube audio url.

        Given a query or a youtube url obtains the best quality audio url.
        Retries fetching audio url in case of error, waiting between attempts.

        Parameters
        ----------
        query : str
            Youtube video url or query.

        Returns
        -------
        Optional[str]
            Youtube audio url or None if no audio url was found.
        """
        logging.getLogger(__name__).debug(
            "Trying to obtain youtube audio url %s", query
        )
        url = None
        if query:
            logging.getLogger(__name__).debug(
                "Attempting to obtain youtube audio url %s", query
            )
            try:
                with yt_dlp.YoutubeDL(
                    settings.player.source.youtube.downloader_config
                ) as ydl:
                    url = ydl.extract_info(url=query, download=False).get("url", None)
            except Exception:
                logging.getLogger(__name__).warning(
                    "Unable to obtain audio url %s",
                    query,
                    exc_info=True,
                )
            if url:
                logging.getLogger(__name__).info(
                    "Obtained audio url for query '%s'", query
                )
                return url
        logging.getLogger(__name__).warning("Unable to obtain audio url %s", query)
        return None


class YoutubeQueryHandler:
    """Youtube query handler.

    Handles youtube search queries. Exposes no accept condition therefore should only be
    used as terminal handler.
    """

    @staticmethod
    def encode_url(url: str) -> str:
        return requote_uri(url)

    @staticmethod
    async def url_from_query(query: str) -> Optional[str]:
        """Get youtube audio url based on search query.

        Perform a youtube query to obtain the related video with the most views.

        Parameters
        ----------
        query : str
            Word query to search.

        Returns
        -------
        Optional[str]
            Youtube video url best matching query, None if no video found.
        """
        url = None
        if query:
            uri = YoutubeQueryHandler.encode_url(
                f"https://www.youtube.com/results?search_query={query}"
            )
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        uri, timeout=settings.player.source.youtube.query_timeout
                    )
                    video_id = re.search(r"watch\?v=(\S{11})", response.text).group(1)
                    url = (
                        f"https://www.youtube.com/watch?v={video_id}"
                        if video_id
                        else None
                    )
                except httpx.TimeoutException:
                    logging.getLogger(__name__).exception(
                        "Unable to search for query: %s", query
                    )
        return url
