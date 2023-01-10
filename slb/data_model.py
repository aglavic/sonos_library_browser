"""
Dataclasses for Sonos items
"""
from dataclasses import dataclass, fields

import soco


@dataclass
class Track:
    artist: str
    album: str
    title: str
    position: str
    duration: str
    album_art: str
    uri: str

    @classmethod
    def from_dict(cls, env):
        flds = [f.name for f in fields(cls)]
        return cls(**{k: v for k, v in env.items() if k in flds})


@dataclass
class SonosSpeaker:
    ip_address: str
    name: str
    room: str
    reference: soco.SoCo


@dataclass
class SonosGroup:
    label: str
    coordinator: soco.SoCo
    reference: soco.groups.ZoneGroup

    def now_playing(self) -> Track:
        return Track.from_dict(self.coordinator.get_current_track_info())


@dataclass
class SonosSystem:
    speakers: list[SonosSpeaker]

    @property
    def reference(self) -> soco.SoCo:
        return self.speakers[0].reference.group.coordinator

    @property
    def groups(self) -> list[SonosGroup]:
        out = []
        for item in self.reference.all_groups:
            group = SonosGroup(item.short_label, item.coordinator, item)
            out.append(group)
        return out

    def now_playing(self):
        output = []
        for g in self.groups:
            t = g.now_playing()
            output.append((g, t))
        return output
