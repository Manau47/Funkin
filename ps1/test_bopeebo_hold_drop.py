"""Focused host checks for the playable probe's hold-release rules."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "ps1" / "spu_probe.c").read_text(encoding="utf-8")
RATE = 43_008


def release_is_miss(remaining_samples: int, rate: int = RATE) -> bool:
    """Mirror the source's strict 160 ms threshold using integer sample math."""
    return rate > 0 and remaining_samples * 1000 > rate * 160


class HoldState:
    def __init__(self):
        self.active = True
        self.bf_muted = False
        self.dad_audible = True
        self.instrumental_audible = True
        self.drops = 0
        self.sfx = 0
        self.score = 0
        self.combo = 4

    def update(self, remaining_samples: int, released: bool):
        if not self.active:
            return
        if remaining_samples <= 0:
            self.active = False
        elif released:
            if release_is_miss(remaining_samples):
                self.drops += 1
                self.sfx += 1
                self.bf_muted = True
                self.score -= remaining_samples * 125 // RATE
                self.combo = 0
            self.active = False

    def successful_bf_hit(self):
        self.bf_muted = False


class HoldDropTests(unittest.TestCase):
    def test_full_hold_completes_without_drop(self):
        state = HoldState()
        state.update(0, released=True)
        self.assertFalse(state.active)
        self.assertEqual((state.drops, state.sfx), (0, 0))
        self.assertFalse(state.bf_muted)

    def test_early_release_mutes_bf_once_and_preserves_other_stems(self):
        state = HoldState()
        state.update(RATE, released=True)  # 1 s remains
        state.update(RATE - 1, released=True)  # later frames cannot retrigger
        self.assertEqual((state.drops, state.sfx), (1, 1))
        self.assertEqual(state.score, -125)
        self.assertEqual(state.combo, 0)
        self.assertTrue(state.bf_muted)
        self.assertTrue(state.dad_audible)
        self.assertTrue(state.instrumental_audible)

    def test_release_at_or_inside_final_160ms_is_tolerated(self):
        threshold = RATE * 160 // 1000
        self.assertFalse(release_is_miss(threshold))
        self.assertFalse(release_is_miss(threshold - 1))
        self.assertTrue(release_is_miss(threshold + 1))
        state = HoldState()
        state.update(threshold, released=True)
        self.assertEqual((state.drops, state.sfx), (0, 0))
        self.assertFalse(state.bf_muted)

    def test_next_successful_bf_hit_restores_voice(self):
        state = HoldState()
        state.update(2 * RATE, released=True)
        self.assertTrue(state.bf_muted)
        state.successful_bf_hit()
        self.assertFalse(state.bf_muted)

    def test_c_source_uses_one_shot_release_path_and_separate_bf_mute(self):
        self.assertIn("(uint64_t)remaining_samples * 1000u > (uint64_t)rate * 160u", SOURCE)
        self.assertIn("if (hold_release_is_miss(remaining, rate))\n\t\t\t\t\tgame_hold_drop(remaining, rate);", SOURCE)
        self.assertIn("active_hold[lane] = -1;", SOURCE)
        self.assertIn("SPU_CH_VOL_L(3) = (voices_muted", SOURCE)
        self.assertIn("|| bf_miss_silenced", SOURCE)
        self.assertIn("bf_miss_silenced = false;", SOURCE)
        self.assertIn("SPU_CH_VOL_L(2)", SOURCE)
        self.assertIn("SPU_CH_VOL_R(2)", SOURCE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
