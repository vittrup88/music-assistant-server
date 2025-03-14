"""DR Lyd [Denmark] Music Provider for Music Assistant."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType, MediaType, ProviderFeature
from music_assistant_models.errors import MediaNotFoundError
from music_assistant_models.media_items import (
    BrowseFolder,
    MediaItemType,
    MediaItemTypeOrItemMapping,
    Podcast,
    PodcastEpisode,
    Radio,
    SearchResults,
)

from music_assistant.models.music_provider import MusicProvider

from .helpers import DrLydApi
from .parsers import (
    get_stream_details_episode_podcast,
    get_stream_details_radio,
    parse_podcast_episode_result,
    parse_podcast_series_result,
    parse_radio,
)

if TYPE_CHECKING:
    from music_assistant_models.config_entries import ConfigValueType, ProviderConfig
    from music_assistant_models.provider import ProviderManifest
    from music_assistant_models.streamdetails import StreamDetails

    from music_assistant.mass import MusicAssistant
    from music_assistant.models import ProviderInstanceType

# CONFIG
CONF_DRLYD_APIKEY = "drlydapikey"


async def setup(
    mass: MusicAssistant, manifest: ProviderManifest, config: ProviderConfig
) -> ProviderInstanceType:
    """Initialize provider(instance) with given configuration."""
    return DkDrLydMusicprovider(mass, manifest, config)


async def get_config_entries(
    mass: MusicAssistant,
    instance_id: str | None = None,
    action: str | None = None,
    values: dict[str, ConfigValueType] | None = None,
) -> tuple[ConfigEntry, ...]:
    """
    Return Config entries to setup this provider.

    instance_id: id of an existing provider instance (None if new instance setup).
    action: [optional] action key called from config entries UI.
    values: the (intermediate) raw values for config entries sent with the action.
    """
    # ruff: noqa: ARG001
    # Config Entries are used to configure the Music Provider if needed.
    # See the models of ConfigEntry and ConfigValueType for more information what is supported.
    # The ConfigEntry is a dataclass that represents a single configuration entry.
    # The ConfigValueType is an Enum that represents the type of value that
    # can be stored in a ConfigEntry.
    # If your provider does not need any configuration, you can return an empty tuple.

    # We support flow-like configuration where you can have multiple steps of configuration
    # using the 'action' parameter to distinguish between the different steps.
    # The 'values' parameter contains the raw values of the config entries that were filled in
    # by the user in the UI. This is a dictionary with the key being the config entry id
    # and the value being the actual value filled in by the user.

    # For authentication flows where the user needs to be redirected to a login page
    # or some other external service, we have a simple helper that can help you with those steps
    # and a callback url that you can use to redirect the user back to the Music Assistant UI.
    # See for example the Deezer provider for an example of how to use this.
    return (
        ConfigEntry(
            key=CONF_DRLYD_APIKEY,
            type=ConfigEntryType.STRING,
            label="DRLYD X-APIKEY",
            required=True,
            description="X-APIKEY used for DRLYD",
        ),
    )


class DkDrLydMusicprovider(MusicProvider):
    """DR Lyd [Denmark] Music provider."""

    _drlydapi: DrLydApi
    _radio_stream_cache: dict[str, StreamDetails] = {}

    @property
    def supported_features(self) -> set[ProviderFeature]:
        """Return the features supported by this Provider."""
        return {
            ProviderFeature.BROWSE,
            ProviderFeature.SEARCH,
            # ProviderFeature.RECOMMENDATIONS,
            # ProviderFeature.LIBRARY_RADIOS,
            # ProviderFeature.LIBRARY_PODCASTS,
        }

    async def handle_async_init(self) -> None:
        """Handle async initialization of the provider."""
        self._drlydapi = DrLydApi(
            self.mass.http_session, str(self.config.get_value(CONF_DRLYD_APIKEY))
        )

    @property
    def is_streaming_provider(self) -> bool:
        """Return True if the provider is a streaming provider."""
        return True

    async def search(
        self,
        search_query: str,
        media_types: list[MediaType],
        limit: int = 5,
    ) -> SearchResults:
        """Perform search on musicprovider.

        :param search_query: Search query.
        :param media_types: A list of media_types to include.
        :param limit: Number of items to return in the search (per type).
        """
        # OPTIONAL
        # Will only be called if you reported the SEARCH feature in the supported_features.
        # It allows searching your provider for media items.
        # See the model for SearchResults for more information on what to return, but
        # in general you should return a list of MediaItems for each media type.
        searchresult = SearchResults()

        podcast_series_result = await self._drlydapi.search_podcast_series(
            search_query=search_query
        )
        if podcast_series_result and len(podcast_series_result) > 0:
            podcasts: Sequence[Podcast] = [
                parse_podcast_series_result(
                    series_result=item,
                    lookup_key=self.lookup_key,
                    domain=self.domain,
                    instance_id=self.instance_id,
                )
                for item in podcast_series_result
            ]
            searchresult.podcasts = podcasts

        return searchresult

    async def get_radio(self, prov_radio_id: str) -> Radio:
        """Get full radio details by id."""
        # Get full details of a single Radio station.
        # Mandatory only if you reported LIBRARY_RADIOS in the supported_features.
        radio_schedule = await self._drlydapi.get_radio_schedule(channel_id=prov_radio_id)
        if not radio_schedule:
            raise MediaNotFoundError(f"Radio station {prov_radio_id} not found")
        return parse_radio(
            radio_schedule=radio_schedule,
            lookup_key=self.lookup_key,
            domain=self.domain,
            instance_id=self.instance_id,
        )

    async def get_podcast(self, prov_podcast_id: str) -> Podcast:
        """Get full audiobook details by id."""
        series_result = await self._drlydapi.get_series(prov_podcast_id)
        return parse_podcast_series_result(
            series_result=series_result,
            lookup_key=self.lookup_key,
            domain=self.domain,
            instance_id=self.instance_id,
        )

    async def get_podcast_episode(self, prov_episode_id: str) -> PodcastEpisode:
        """Get (full) podcast episode details by id."""
        episode_result = await self._drlydapi.get_episode(prov_episode_id)
        return parse_podcast_episode_result(
            episode_result=episode_result,
            lookup_key=self.lookup_key,
            domain=self.domain,
            instance_id=self.instance_id,
        )

    async def get_podcast_episodes(
        self,
        prov_podcast_id: str,
    ) -> AsyncGenerator[PodcastEpisode, None]:
        """Get all PodcastEpisodes for given podcast id."""
        episode_results = await self._drlydapi.get_episodes(prov_podcast_id)
        for episode_result in episode_results:
            yield parse_podcast_episode_result(
                episode_result, self.lookup_key, self.domain, self.instance_id
            )

    async def get_stream_details(self, item_id: str, media_type: MediaType) -> StreamDetails:
        """Get streamdetails for a track/radio."""
        # Get stream details for a track or radio.
        # Implementing this method is MANDATORY to allow playback.
        # The StreamDetails contain info how Music Assistant can play the track.
        # item_id will always be a track or radio id. Later, when/if MA supports
        # podcasts or audiobooks, this may as well be an episode or chapter id.
        # You should return a StreamDetails object here with the info as accurate as possible
        # to allow Music Assistant to process the audio using ffmpeg.

        if media_type == MediaType.RADIO:
            radio_schedule = await self._drlydapi.get_radio_schedule(channel_id=item_id)

            if not radio_schedule:
                raise MediaNotFoundError(f"Radio station {item_id} not found")

            stream_details = get_stream_details_radio(
                radio_schedule=radio_schedule, item_id=item_id, instance_id=self.instance_id
            )
            self._radio_stream_cache[item_id] = stream_details
            return stream_details

        elif media_type == MediaType.PODCAST_EPISODE:
            episode_result = await self._drlydapi.get_episode(episode_id=item_id)

            if not episode_result:
                raise MediaNotFoundError(f"Podcast Episode {item_id} not found")

            return get_stream_details_episode_podcast(
                episode_result=episode_result, item_id=item_id, instance_id=self.instance_id
            )

        raise MediaNotFoundError(f"Media {item_id} not found")

    async def on_played(
        self,
        media_type: MediaType,
        prov_item_id: str,
        fully_played: bool,
        position: int,
        media_item: MediaItemType,
        is_playing: bool = False,
    ) -> None:
        """
        Handle callback when a (playable) media item has been played.

        This is called by the Queue controller when;
            - a track has been fully played
            - a track has been stopped (or skipped) after being played
            - every 30s when a track is playing

        Fully played is True when the track has been played to the end.

        Position is the last known position of the track in seconds, to sync resume state.
        When fully_played is set to false and position is 0,
        the user marked the item as unplayed in the UI.

        is_playing is True when the track is currently playing.

        media_item is the full media item details of the played/playing track.
        """
        # This is an OPTIONAL callback that is called when an item has been streamed.
        # You can use this e.g. for playback reporting or statistics.

        if is_playing:
            if media_type == MediaType.RADIO:
                stream_details = self._radio_stream_cache[prov_item_id]

                radio_schedule = await self._drlydapi.get_radio_schedule(channel_id=prov_item_id)

                if not radio_schedule:
                    raise MediaNotFoundError(f"Radio station {prov_item_id} not found")

                new_stream_details = get_stream_details_radio(
                    radio_schedule=radio_schedule,
                    item_id=prov_item_id,
                    instance_id=self.instance_id,
                )

                stream_details.stream_title = new_stream_details.stream_title

    async def browse(self, path: str) -> Sequence[MediaItemTypeOrItemMapping]:
        """Browse this provider's items.

        :param path: The path to browse, (e.g. provider_id://artists).
        """
        part_parts = path.split("://")[1].split("/")
        subpath = part_parts[0] if part_parts else ""

        if not subpath:
            # return main listing
            return [
                BrowseFolder(
                    item_id="radio",
                    provider=self.domain,
                    path=path + "radio",
                    name="radio",
                ),
            ]

        if subpath == "radio":
            return await self.get_radio_stations()

        return []

    async def get_radio_stations(self) -> Sequence[Radio]:
        """Get radio stations."""
        radio_schedules = await self._drlydapi.get_radio_schedules()
        return [
            parse_radio(
                radio_schedule=radio_schedule,
                lookup_key=self.lookup_key,
                domain=self.domain,
                instance_id=self.instance_id,
            )
            for radio_schedule in radio_schedules
        ]
