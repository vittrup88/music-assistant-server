"""Helpers for DRLyd music provider."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aiohttp import ClientSession
from mashumaro import DataClassDictMixin, MissingField, field_options
from music_assistant_models.errors import InvalidDataError


@dataclass
class Channel(DataClassDictMixin):
    """Radio Channel Data."""

    title: str
    id: str
    slug: str
    type: str  # TODO enum?
    presentation_url: str = field(metadata=field_options(alias="presentationUrl"))


@dataclass
class AudioAsset(DataClassDictMixin):
    """Audio Data."""

    target: str
    is_stream_live: bool = field(metadata=field_options(alias="isStreamLive"))
    format: str
    url: str

    # optional fields
    bitrate: int | None = None


@dataclass
class ImageAsset(DataClassDictMixin):
    """Image Data."""

    id: str
    target: str
    ratio: str
    format: str
    blur_hash: str = field(metadata=field_options(alias="blurHash"))


@dataclass
class Series(DataClassDictMixin):
    """Podcast series data."""

    title: str
    id: str
    slug: str
    type: str  # TODO enum
    is_available_on_demand: bool = field(metadata=field_options(alias="isAvailableOnDemand"))

    # OPTIONAL
    presentation_url: str | None = field(
        default=None, metadata=field_options(alias="presentationUrl")
    )
    learn_id: str | None = field(default=None, metadata=field_options(alias="learnId"))


@dataclass
class RadioSchedule(DataClassDictMixin):
    """Radio Item."""

    type: str  # TODO enum
    duration_milliseconds: int = field(metadata=field_options(alias="durationMilliseconds"))
    # categories
    # productionNumber
    start_time: datetime = field(metadata=field_options(alias="startTime"))
    end_time: datetime = field(metadata=field_options(alias="endTime"))
    order: int
    channel: Channel
    audio_assets: list[AudioAsset] = field(metadata=field_options(alias="audioAssets"))
    is_available_on_demand: bool = field(metadata=field_options(alias="isAvailableOnDemand"))
    explicit_content: bool = field(metadata=field_options(alias="explicitContent"))
    slug: str
    title: str
    image_assets: list[ImageAsset] = field(metadata=field_options(alias="imageAssets"))

    # OPTIONAL
    learn_id: str | None = field(default=None, metadata=field_options(alias="learnId"))
    presentation_url: str | None = field(
        default=None, metadata=field_options(alias="presentationUrl")
    )
    series: Series | None = None
    description: str | None = None


@dataclass
class SeriesResult(DataClassDictMixin):
    """Podcast series item."""

    type: str  # TODO enum

    number_of_episodes: int = field(metadata=field_options(alias="numberOfEpisodes"))

    title: str
    id: str
    slug: str
    description: str

    presentation_url: str = field(metadata=field_options(alias="presentationUrl"))

    channel: Channel
    image_assets: list[ImageAsset] = field(metadata=field_options(alias="imageAssets"))

    # Optional
    punchline: str | None = None


@dataclass
class SeriesSearchResults(DataClassDictMixin):
    """Podcast series search result."""

    items: list[SeriesResult]


@dataclass
class EpisodeResult(DataClassDictMixin):
    """Podcast Episode item."""

    type: str  # TODO enum "Episode"

    # learnId: str
    duration_milliseconds: int = field(metadata=field_options(alias="durationMilliseconds"))
    categories: list[str]
    production_number: int = field(metadata=field_options(alias="productionNumber"))
    publish_time: str = field(metadata=field_options(alias="publishTime"))
    start_time: str = field(metadata=field_options(alias="startTime"))
    # presentationUrl: str

    series: Series
    channel: Channel
    audio_assets: list[AudioAsset] = field(metadata=field_options(alias="audioAssets"))

    order: int

    is_available_on_demand: bool = field(metadata=field_options(alias="isAvailableOnDemand"))
    explicit_content: bool = field(metadata=field_options(alias="explicitContent"))

    latest_publish_time: str = field(metadata=field_options(alias="latestPublishTime"))

    id: str
    slug: str
    title: str
    # punchline: str
    description: str

    image_assets: list[ImageAsset] = field(metadata=field_options(alias="imageAssets"))

    # Optional
    next_id: str | None = field(default=None, metadata=field_options(alias="nextId"))
    previous_id: str | None = field(default=None, metadata=field_options(alias="previousId"))


@dataclass
class SeriesEpisodeResult(DataClassDictMixin):
    """Podcast Episodes."""

    type: str  # TODO enum -  "type": "List"

    total_size: int = field(metadata=field_options(alias="totalSize"))
    offset: int
    limit: int
    self: str  # url - requested
    items: list[EpisodeResult]

    # Optional
    next: str | None = field(
        default=None, metadata=field_options(alias="learnId")
    )  # next url - paginate
    prev: str | None = field(
        default=None, metadata=field_options(alias="learnId")
    )  # prev url - paginate


RADIO_ICONS = {
    "p1": "assets/DRP1_logo_primaer_RGB.png",
    "p2": "assets/DRP2_logo_primaer_RGB.png",
    "p3": "assets/DRP3_logo_primaer_RGB.png",
    "p4bornholm": "assets/DRP4_logo_primaer_RGB.png",
    "p4esbjerg": "assets/DRP4_logo_primaer_RGB.png",
    "p4fyn": "assets/DRP4_logo_primaer_RGB.png",
    "p4kbh": "assets/DRP4_logo_primaer_RGB.png",
    "p4vest": "assets/DRP4_logo_primaer_RGB.png",
    "p4nord": "assets/DRP4_logo_primaer_RGB.png",
    "p4aarhus": "assets/DRP4_logo_primaer_RGB.png",
    "p4sjaelland": "assets/DRP4_logo_primaer_RGB.png",
    "p4syd": "assets/DRP4_logo_primaer_RGB.png",
    "p4trekanten": "assets/DRP4_logo_primaer_RGB.png",
    "p5bornholm": "assets/DRP5_logo_primaer_RGB.png",
    "p5esbjerg": "assets/DRP5_logo_primaer_RGB.png",
    "p5fyn": "assets/DRP5_logo_primaer_RGB.png",
    "p5kbh": "assets/DRP5_logo_primaer_RGB.png",
    "p5vest": "assets/DRP5_logo_primaer_RGB.png",
    "p5nord": "assets/DRP5_logo_primaer_RGB.png",
    "p5aarhus": "assets/DRP5_logo_primaer_RGB.png",
    "p5sjaelland": "assets/DRP5_logo_primaer_RGB.png",
    "p5syd": "assets/DRP5_logo_primaer_RGB.png",
    "p5trekanten": "assets/DRP5_logo_primaer_RGB.png",
    "p6beat": "assets/DRP6_logo_primaer_RGB.png",
    "p8jazz": "assets/DRP8_logo_primaer_RGB.png",
}


# TODO url encoder / path join
BASE_DRAPI_URL = "https://api.dr.dk"
RADIO_DRAPI_URL = BASE_DRAPI_URL + "/radio/v4/schedules/all/now"
RADIO_INDEXPOINTS_DRAPI_URL = BASE_DRAPI_URL + "/radio/v4/indexpoints/live"

BASE_DRASSETS_URL = "https://asset.dr.dk"
BASE_IMAGESCALER_DRASSETS_URL = BASE_DRASSETS_URL + "/imagescaler"

# https://api.dr.dk/radio/v4/indexpoints/live/p5kbh
# slug for channel id / name
# Will have data for what is playing

BASE_SEARCH_DRAPI_URL = BASE_DRAPI_URL + "/radio/v4/search"

BASE_SERIES_DRAPI_URI = "/radio/v4/series"
BASE_EPISODES_DRAPI_URI = "/radio/v4/episodes"

APIKEY_HEADERS = {"x-apikey": "6Wkh8s98Afx1ZAaTT4FuWODTmvWGDPpR"}


class DrLydApi:
    """DR Lyd api."""

    _session: ClientSession

    def __init__(self, session: ClientSession) -> None:
        """Init."""
        self._session = session

    async def get_radio_schedules(self) -> list[RadioSchedule]:
        """Get All Radio Schedules."""
        json_response = await self._call_api(RADIO_DRAPI_URL)

        radio_schedules = []
        for item in json_response:
            try:
                radio_schedule = RadioSchedule.from_dict(item)
                radio_schedules.append(radio_schedule)
            except MissingField as err:
                raise InvalidDataError from err
        return radio_schedules

    async def get_radio_schedule(self, channel_id: str) -> RadioSchedule | None:
        """Get Radio Schedule."""
        radio_schedules = await self.get_radio_schedules()
        for radio_schedule in radio_schedules:
            if radio_schedule.channel.slug == channel_id:
                return radio_schedule
        return None

    async def search_podcast_series(self, search_query: str) -> list[SeriesResult]:
        """Search Podcast Series."""
        url = (
            BASE_SEARCH_DRAPI_URL
            + "/series?categories=&channels=&offset=0&limit=10&q="
            + search_query
        )
        json_response = await self._call_api(url, headers=APIKEY_HEADERS)
        search_result = SeriesSearchResults.from_dict(json_response)
        return search_result.items

    async def get_series(self, slug_id: str) -> SeriesResult:
        """Get Series aka Podcast Series."""
        url = BASE_DRAPI_URL + BASE_SERIES_DRAPI_URI + "/" + slug_id
        json_response = await self._call_api(url, headers=APIKEY_HEADERS)
        return SeriesResult.from_dict(json_response)

    async def get_episodes(self, series_slug_id: str) -> list[EpisodeResult]:
        """Get Episodes."""
        url: str | None = (
            BASE_DRAPI_URL + BASE_SERIES_DRAPI_URI + "/" + series_slug_id + "/episodes?sort=desc"
        )
        episode_results: list[EpisodeResult] = []

        while url:
            json_response = await self._call_api(url, headers=APIKEY_HEADERS)
            series_episodes_result = SeriesEpisodeResult.from_dict(json_response)
            episode_results += series_episodes_result.items
            url = series_episodes_result.next

        return episode_results

    async def get_episode(self, episode_id: str) -> EpisodeResult:
        """Get Episode.

        episode_id : can be id or slugid
        """
        url = BASE_DRAPI_URL + BASE_EPISODES_DRAPI_URI + "/" + episode_id
        json_response = await self._call_api(url, headers=APIKEY_HEADERS)
        episode_result: EpisodeResult = EpisodeResult.from_dict(json_response)
        return episode_result

    async def _call_api(self, url: str, headers: Any | None = None) -> Any:
        url_response = await self._session.get(url, headers=headers)
        return await url_response.json()
