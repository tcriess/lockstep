"""lockstep.dosound: the build-time Dosound player and the record stream of the constant-cost replay."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lockstep.dosound import DosoundError, Song, frames  # noqa: E402

# A0 at volume 12, then two more frames, a sweep of channel B's volume 0 -> 6 step 2, end.
TUNE = bytes([0, 0x1c, 1, 1, 8, 12, 0x82, 2,
              8, 0, 0x80, 0, 0x81, 9, 2, 6,
              0x82, 1, 7, 0x3f, 0xff, 0])


def test_frames():
    fr = frames(TUNE, delay_extra=0)
    assert fr == [[(0, 0x1c), (1, 1), (8, 12)], [],              # wait 2: the next frame is idle
                  [(8, 0), (9, 2)], [(9, 4)], [(9, 6)],          # sweep: one step per frame
                  [],                                            # its end closes the frame; wait 1
                  [(7, 0xff)]]                                   # R7: port bits forced to output


def test_wait_default_is_tracker_dl():
    # dosound-tracker: "dc.b $FF,$1 ; DL 2" = two frames per step
    assert frames(bytes([8, 1, 0xff, 1, 8, 2, 0xff, 0])) == [[(8, 1)], [], [(8, 2)]]
    assert frames(bytes([8, 1, 0xff, 1, 8, 2, 0xff, 0]), delay_extra=0) == [[(8, 1)], [(8, 2)]]


def test_no_end():
    with pytest.raises(DosoundError):
        frames(bytes([8, 1, 0x82, 1]))


def _replay(song: Song, n: int) -> list:
    """What the replay routine does, frame by frame: the reference for the record stream."""
    out, ptr, wait = [], 0, song.first_wait
    for _ in range(n):
        wait -= 1
        if wait == 0:
            gap, w = song.records[ptr]
            wait, ptr = gap, (ptr + 1) % len(song.records)
            out.append(list(w))
        else:
            out.append([])
    return out


@pytest.mark.parametrize("delay_extra", [0, 1])
def test_records_replay_frames_looping(delay_extra):
    data = TUNE[:-2] + bytes([0x82, 0x40, 9, 1, 0xff, 0])        # a long wait before the end
    fr = frames(data, delay_extra=delay_extra)
    song = Song(data, delay_extra=delay_extra)
    assert _replay(song, 3 * len(fr)) == fr * 3


def test_long_wait_split():
    data = bytes([8, 1, 0x82, 255, 0x82, 200, 8, 2, 0x82, 0])     # 455 frames between writes
    song = Song(data)
    assert all(g <= 255 for g, _ in song.records)
    fr = frames(data)
    assert _replay(song, 2 * len(fr)) == fr * 2


def test_cost_constant():
    song = Song(TUNE)
    assert song.cycles % 4 == 0 and song.k == 3
    assert ";@stall" in song.call()
