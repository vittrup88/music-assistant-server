"""Helpers for DR Lyd [Denmark] Music Provider."""

import os
import urllib.parse

from music_assistant_models.enums import ContentType, ImageType, LinkType, MediaType, StreamType
from music_assistant_models.media_items import (
    AudioFormat,
    ItemMapping,
    MediaItemImage,
    MediaItemLink,
    Podcast,
    PodcastEpisode,
    ProviderMapping,
    Radio,
    UniqueList,
)
from music_assistant_models.streamdetails import StreamDetails

from .helpers import (
    BASE_IMAGESCALER_DRASSETS_URL,
    RADIO_ICONS,
    EpisodeResult,
    RadioSchedule,
    SeriesResult,
)


def parse_radio(
    radio_schedule: RadioSchedule,
    lookup_key: str,
    domain: str,
    instance_id: str,
) -> Radio:
    """Translate DR Radio Schedule to MA Radio."""
    radio = Radio(
        item_id=radio_schedule.channel.slug,
        provider=domain,
        name=radio_schedule.channel.title,
        provider_mappings={
            ProviderMapping(
                item_id=radio_schedule.channel.slug,
                provider_domain=domain,
                provider_instance=instance_id,
            )
        },
    )
    radio.metadata.links = {
        MediaItemLink(type=LinkType.WEBSITE, url=radio_schedule.channel.presentation_url)
    }

    images: UniqueList[MediaItemImage] = UniqueList()

    icon = RADIO_ICONS.get(radio_schedule.channel.slug)
    if icon:
        absolute_path = os.path.dirname(os.path.abspath(__file__))
        icon_absolute_path = os.path.join(absolute_path, icon)
        images.append(
            MediaItemImage(
                type=ImageType.THUMB,
                path=icon_absolute_path,
                provider=lookup_key,
                remotely_accessible=False,
            )
        )
        images.append(
            MediaItemImage(
                provider=lookup_key,
                type=ImageType.LOGO,
                path=icon_absolute_path,
                remotely_accessible=False,
            )
        )

    banner_url = None
    for image_asset in radio_schedule.image_assets:
        if image_asset.target == "Default" and image_asset.ratio == "16:9":
            banner_url = (
                BASE_IMAGESCALER_DRASSETS_URL
                + "/?protocol=https&server=api.dr.dk&file="
                + urllib.parse.quote_plus("/radio/v4/images/raw/" + image_asset.id)
            )

    if banner_url is not None:
        images.append(
            MediaItemImage(
                provider=lookup_key,
                type=ImageType.BANNER,
                path=banner_url,
                remotely_accessible=True,
            )
        )
        images.append(
            MediaItemImage(
                provider=lookup_key,
                type=ImageType.LANDSCAPE,
                path=banner_url,
                remotely_accessible=True,
            )
        )

    radio.metadata.images = images
    if radio_schedule.channel.presentation_url:
        links: set[MediaItemLink] = set()
        links.add(MediaItemLink(type=LinkType.WEBSITE, url=radio_schedule.channel.presentation_url))
        radio.metadata.links = links
    # if radioSchedule.title:
    #    radio.metadata.label = radioSchedule.title
    # if radioSchedule.description:
    #    radio.metadata.description = radioSchedule.description
    # radio.metadata.description = channel.medium_description
    # radio.metadata.genres = [cat.name for cat in channel.categories]

    return radio


def get_stream_details_radio(
    radio_schedule: RadioSchedule, item_id: str, instance_id: str
) -> StreamDetails:
    """Translate DR Radio Schedule to MA Stream Details."""
    stream_type: StreamType = StreamType.HTTP
    path: str | None = None
    bitrate: int = 0

    for audio_asset in radio_schedule.audio_assets:
        if audio_asset.format == "HLS":
            stream_type = StreamType.HLS
            path = audio_asset.url
            break

        if audio_asset.format == "ICY":
            stream_type = StreamType.ICY
            asset_bitrate: int = 0 if audio_asset.bitrate is None else audio_asset.bitrate
            if asset_bitrate > bitrate:
                bitrate = asset_bitrate
                path = audio_asset.url

    stream_title: str | None = None
    if radio_schedule.title:
        stream_title = radio_schedule.title

    return StreamDetails(
        provider=instance_id,
        item_id=item_id,
        audio_format=AudioFormat(
            # provide details here about sample rate etc. if known
            # set content type to unknown to let ffmpeg guess the codec/container
            content_type=ContentType.UNKNOWN,
        ),
        media_type=MediaType.RADIO,
        # streamtype defines how the stream is provided
        # for most providers this will be HTTP but you can also use CUSTOM
        # to provide a custom stream generator in get_audio_stream.
        stream_type=stream_type,
        # explore the StreamDetails model and StreamType enum for more options
        # but the above should be the mandatory fields to set.
        allow_seek=False,
        # set allow_seek to True if the stream may be seeked
        can_seek=False,
        # set can_seek to True if the stream supports seeking
        path=path,
        stream_title=stream_title,
    )


def parse_podcast_series_result(
    series_result: SeriesResult, lookup_key: str, domain: str, instance_id: str
) -> Podcast:
    """Translate DR Series Result to MA Podcast."""
    podcast = Podcast(
        item_id=series_result.slug,
        name=series_result.title,
        total_episodes=series_result.number_of_episodes,
        # sort_name=tags.album_sort,
        # publisher=tags.tags.get("publisher"),
        publisher="DR",
        provider=lookup_key,
        provider_mappings={
            ProviderMapping(
                item_id=series_result.slug,
                provider_domain=domain,
                provider_instance=instance_id,
            )
        },
    )

    images: UniqueList[MediaItemImage] = UniqueList()
    for image_asset in series_result.image_assets:
        imageurl = (
            BASE_IMAGESCALER_DRASSETS_URL
            + "/?protocol=https&server=api.dr.dk&file="
            + urllib.parse.quote_plus("/radio/v4/images/raw/" + image_asset.id)
        )

        if image_asset.target == "Default" and image_asset.ratio == "16:9":
            images.append(
                MediaItemImage(
                    provider=lookup_key,
                    type=ImageType.BANNER,
                    path=imageurl,
                    remotely_accessible=True,
                )
            )
            images.append(
                MediaItemImage(
                    provider=lookup_key,
                    type=ImageType.LANDSCAPE,
                    path=imageurl,
                    remotely_accessible=True,
                )
            )
        if image_asset.target == "Podcast":
            images.append(
                MediaItemImage(
                    provider=lookup_key,
                    type=ImageType.THUMB,
                    path=imageurl,
                    remotely_accessible=True,
                )
            )

    podcast.metadata.images = images
    return podcast


def parse_podcast_episode_result(
    episode_result: EpisodeResult, lookup_key: str, domain: str, instance_id: str
) -> PodcastEpisode:
    """Translate DR Episode Result to MA Podcast Episode."""
    content_type: ContentType = ContentType.UNKNOWN
    url: str | None = None
    bitrate: int = 0

    for audio_asset in episode_result.audio_assets:
        if audio_asset.format.lower() == "mp4":
            content_type = ContentType.MP4
            asset_bitrate: int = 0 if audio_asset.bitrate is None else audio_asset.bitrate
            if asset_bitrate > bitrate:
                bitrate = asset_bitrate
                url = audio_asset.url

    podcast_episode = PodcastEpisode(
        item_id=episode_result.slug,
        name=episode_result.title,
        duration=int(episode_result.duration_milliseconds / 1000),
        position=episode_result.order,
        podcast=ItemMapping(
            item_id=episode_result.series.slug,
            provider=lookup_key,
            name=episode_result.series.title,
            media_type=MediaType.PODCAST,
        ),
        provider=lookup_key,
        provider_mappings={
            ProviderMapping(
                item_id=episode_result.slug,
                provider_domain=domain,
                provider_instance=instance_id,
                audio_format=AudioFormat(content_type=content_type, bit_rate=bitrate),
                url=url,
            )
        },
    )

    images: UniqueList[MediaItemImage] = UniqueList()
    for image_asset in episode_result.image_assets:
        imageurl = (
            BASE_IMAGESCALER_DRASSETS_URL
            + "/?protocol=https&server=api.dr.dk&file="
            + urllib.parse.quote_plus("/radio/v4/images/raw/" + image_asset.id)
        )

        if image_asset.target.lower() == "default" and image_asset.ratio == "16:9":
            images.append(
                MediaItemImage(
                    provider=lookup_key,
                    type=ImageType.BANNER,
                    path=imageurl,
                    remotely_accessible=True,
                )
            )
            images.append(
                MediaItemImage(
                    provider=lookup_key,
                    type=ImageType.LANDSCAPE,
                    path=imageurl,
                    remotely_accessible=True,
                )
            )
        if image_asset.target.lower() == "podcast":
            images.append(
                MediaItemImage(
                    provider=lookup_key,
                    type=ImageType.THUMB,
                    path=imageurl,
                    remotely_accessible=True,
                )
            )

    podcast_episode.metadata.images = images
    podcast_episode.metadata.description = episode_result.description

    return podcast_episode


def get_stream_details_episode_podcast(
    episode_result: EpisodeResult, item_id: str, instance_id: str
) -> StreamDetails:
    """Translate DR Episode Result to MA Stream Details."""
    stream_type: StreamType = StreamType.HTTP
    path: str | None = None
    bitrate: int = 0

    for audio_asset in episode_result.audio_assets:
        if audio_asset.format.lower() == "mp4":
            stream_type = StreamType.HTTP
            asset_bitrate: int = 0 if audio_asset.bitrate is None else audio_asset.bitrate
            if asset_bitrate > bitrate:
                bitrate = asset_bitrate
                path = audio_asset.url

    stream_title: str | None = None
    if episode_result.title:
        stream_title = episode_result.title

    return StreamDetails(
        provider=instance_id,
        item_id=item_id,
        duration=int(episode_result.duration_milliseconds / 1000),
        audio_format=AudioFormat(
            # provide details here about sample rate etc. if known
            # set content type to unknown to let ffmpeg guess the codec/container
            content_type=ContentType.UNKNOWN,
        ),
        media_type=MediaType.PODCAST_EPISODE,
        # streamtype defines how the stream is provided
        # for most providers this will be HTTP but you can also use CUSTOM
        # to provide a custom stream generator in get_audio_stream.
        stream_type=stream_type,
        # explore the StreamDetails model and StreamType enum for more options
        # but the above should be the mandatory fields to set.
        allow_seek=True,
        # set allow_seek to True if the stream may be seeked
        can_seek=True,
        # set can_seek to True if the stream supports seeking
        path=path,
        stream_title=stream_title,
    )
