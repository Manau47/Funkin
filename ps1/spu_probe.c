/* CD-to-SPU VAGi streaming probe; audio data is supplied locally at build time. */
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <psxapi.h>
#include <psxetc.h>
#include <psxgpu.h>
#include <psxpad.h>
#include <psxspu.h>
#include <psxcd.h>

#include "stream.h"

#define SCREEN_W 320
#define SCREEN_H 240
#define WEEK2_SPOOKY_DISPLAY_W 65u
#define WEEK2_SPOOKY_DISPLAY_H 76u
#define WEEK3_SCENE_ZOOM_Q8 384u
#define WEEK3_CHARACTER_REFERENCE_ZOOM_Q8 640u
#define RAM_BUFFER_SIZE 0x18000u
#define REFILL_THRESHOLD (24u * 2048u)
#define DUMMY_BLOCK_ADDR 0x1000u
#define STREAM_BUFFER_ADDR 0x1010u
#define SPU_RAM_SIZE 0x80000u
#define CD_SECTOR_SIZE 2048u
#define MAX_WAIT_FRAMES 600u
#define TEST_BPM 120u
#ifndef TEST_CHANNELS
#define TEST_CHANNELS 2u
#endif
#ifndef TEST_NO_LOOP
#define TEST_NO_LOOP 0
#endif
#ifndef TEST_TOTAL_SAMPLES
#define TEST_TOTAL_SAMPLES 0u
#endif
#define TEST_VOICE_VOLUME 0x2fffu
#define TEST_INSTRUMENT_VOLUME 0x2fffu
#define SONG_MIX_VOLUME 0x2800u
#define MUSIC_SPAN_GAIN 0x2800u
#if TEST_PLAYABLE_BOPEEBO
#define SFX_POOL_VOLUME_BUDGET 0x3000u
#else
#define SFX_POOL_VOLUME_BUDGET 0x1800u
#endif
#define SFX_SPU_ADDR 0x10000u
#define SFX_FIRST_VOICE 4u
#define SFX_VOICE_COUNT 4u
#define SFX_BUSY_FRAMES 9u
#define SFX_AUTO_DURING_COUNT 4u
#define SFX_AUTO_DURING_START_SAMPLES (2u * 43008u)
#define MENU_SFX_SPURAM_ADDR 0x22000u
#define MENU_SFX_FIRST_VOICE 8u
#define MENU_SFX_VOICE_COUNT 3u
#define MENU_MUSIC_CHANNELS 4u

#if TEST_BOPEEBO_4CH && !TEST_PLAYABLE_BOPEEBO
#include "bopeebo_sfx_data.h"
#endif
#if TEST_PLAYABLE_BOPEEBO
#include "week4_catalog.h"
#include "bopeebo_visual_data.h"
#include "bf_sing_pose_data.h"
#include "week2_bf_overlay_data.h"
#include "week4_visual_data.h"
#include "menu_audio_data.h"
#include "week5_catalog.h"
#include "week5_visual_data.h"
#ifndef BOPEEBO_WEEK5_UPPER_CROWD_DETAIL_Q8
#define BOPEEBO_WEEK5_UPPER_CROWD_DETAIL_Q8 256u
#endif
#ifndef BOPEEBO_WEEK5_ESCALATOR_DETAIL_Q8
#define BOPEEBO_WEEK5_ESCALATOR_DETAIL_Q8 256u
#endif
#include "week6_catalog.h"
#include "week6_visual_data.h"
#include "week7_catalog.h"
#include "week7_visual_data.h"
#include "weekend1_catalog.h"
#include "weekend1_visual_data.h"
#define BOPEEBO_CHART_RATE PS1_CHART_RATE
#define GAME_WINDOW_SAMPLES ((uint32_t)(BOPEEBO_CHART_RATE * 160u / 1000u))
#define GAME_MAX_PRIMS 220u
/* Worst chart frame: 8 receptors + 3 textured quads for each of 58 holds
   and 1 for each of 44 taps, plus stage/characters/HUD/judgement = ~234.
   Keep explicit headroom so late HUD feedback is not silently dropped. */
/* Keep dedicated headroom beyond the busiest chart frame for HUD portraits,
   judgement art, and the optional QA sheet. A full note field must not drop
   these later screen-space elements. */
#define VISUAL_MAX_PRIMS 640u
#define VISUAL_HUD_RESERVED_PRIMS 32u
#define VISUAL_WORLD_PRIM_LIMIT (VISUAL_MAX_PRIMS - VISUAL_HUD_RESERVED_PRIMS)
#define BOPEEBO_BPM 100u
#define MENU_BPM_CENTI 10200u /* freakyMenu-metadata.json, 102 BPM */
#define WEEK2_CAMERA_ZOOM_Q8_4_3 BOPEEBO_STAGE_CAMERA_ZOOM_Q8 /* match Week 1 camera zoom */
/* Keep the Week 2 room behind the singers, but crop farther into its source
   art and lower the room slightly. This adds overscan around the 4:3 viewport
   while keeping the scene window and lightning overlay on one transform. */
#define WEEK2_BACKGROUND_ZOOM_Q8 576u
#define WEEK2_BACKGROUND_X_OFFSET 46
#define WEEK2_BACKGROUND_Y_OFFSET 85
#define WEEK2_BACKGROUND_TINT 192u
#define WEEK2_EARLY_OPPONENT_CAMERA_LOWER_WORLD 5
#define GAME_SCROLL_PIXELS_PER_SECOND 176u
#define CAMERA_FOCUS_TIME_MS 600u /* official FocusCamera default: four steps at 100 BPM */
#ifndef GAME_DAD_LANES_DEFAULT
#define GAME_DAD_LANES_DEFAULT 1
#endif
#ifndef GAME_DIAGNOSTICS_DEFAULT
#define GAME_DIAGNOSTICS_DEFAULT 0
#endif
#ifndef GAME_STARTUP_MAIN_MARKER
#define GAME_STARTUP_MAIN_MARKER 0
#endif
#ifndef GAME_SCENE_DEMO_DEFAULT
#define GAME_SCENE_DEMO_DEFAULT 0
#endif
#ifndef GAME_WEEK4_COMPOSITION_EDITOR
#define GAME_WEEK4_COMPOSITION_EDITOR 0
#endif
#ifndef GAME_WEEK5_COMPOSITION_EDITOR
#define GAME_WEEK5_COMPOSITION_EDITOR 0
#endif
#ifndef GAME_HEALTH_BAR_TEST_DEFAULT
#define GAME_HEALTH_BAR_TEST_DEFAULT 0
#endif
#ifndef GAME_ARROW_DIAGNOSTIC_DEFAULT
#define GAME_ARROW_DIAGNOSTIC_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_TEST_DEFAULT
#define GAME_JUDGEMENT_TEST_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_VISUAL_TEST_DEFAULT
#define GAME_JUDGEMENT_VISUAL_TEST_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_SOLID_PROBE_DEFAULT
#define GAME_JUDGEMENT_SOLID_PROBE_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_TEXTURE_PROBE_DEFAULT
#define GAME_JUDGEMENT_TEXTURE_PROBE_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_CLUT_PROBE_DEFAULT
#define GAME_JUDGEMENT_CLUT_PROBE_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_POPUP_CLUT_PROBE_DEFAULT
#define GAME_JUDGEMENT_POPUP_CLUT_PROBE_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_POPUP_CLUT_RELOCATE_PROBE_DEFAULT
#define GAME_JUDGEMENT_POPUP_CLUT_RELOCATE_PROBE_DEFAULT 0
#endif
#ifndef GAME_JUDGEMENT_POPUP_CLUT_SLOT_PROBE_DEFAULT
#define GAME_JUDGEMENT_POPUP_CLUT_SLOT_PROBE_DEFAULT 0
#endif

typedef struct {
	int16_t first_center_x;
	int16_t receptor_y;
	int16_t lane_step;
	uint8_t arrow_size;
	uint8_t top_clip;
	uint8_t lane_group;
} NoteGroupLayout;

typedef enum {
	SCREEN_TITLE,
	SCREEN_MAIN_MENU,
	SCREEN_FREEPLAY,
	SCREEN_GAMEPLAY,
	SCREEN_PAUSE,
	SCREEN_GAME_OVER,
	SCREEN_COUNTDOWN
} GameScreen;
static GameScreen game_screen = SCREEN_TITLE;
static uint32_t menu_ticks;
static uint32_t freeplay_dj_start_frame;
static int freeplay_dj_frame_loaded = -1;
static bool menu_dj_vram_loaded;
static bool menu_visuals_loaded;
static bool week2_visuals_loaded;
static bool week3_visuals_loaded;
static unsigned week3_train_song_index = UINT_MAX;
static unsigned week3_train_last_beat = UINT_MAX;
static int week3_train_cooldown;
static bool week3_train_moving;
static uint32_t week3_train_start_sample;
static uint32_t week3_train_random_state;
static unsigned week3_gf_hair_state;
static uint32_t week3_gf_hair_start_sample;
static unsigned week3_light_last_beat = UINT_MAX;
static unsigned week3_light_color_index;
static uint32_t week3_light_random_state;
static uint32_t week3_light_clut_upload;
static bool week4_visuals_loaded;
static const BopeeboVisualPage week4_far_dancer_page = { 896, 0, 1 };
static const BopeeboVisualPage week5_spare_visual_page = { 896, 0, 1 };

static const BopeeboVisualPage *week5_visual_page_info(unsigned logical_page, bool evil_mall)
{
	/* Background alternatives share physical page 0. Character pages are
	   always resident during Week 5; Xmas/Evil prop pages lease the same final
	   physical slots because the variants are mutually exclusive. */
	if (logical_page < 2u) return &bopeebo_visual_page_table[0];
	if (logical_page >= BOPEEBO_WEEK5_COMMON_FIRST_PAGE &&
		logical_page < BOPEEBO_WEEK5_COMMON_FIRST_PAGE + BOPEEBO_WEEK5_COMMON_PAGE_COUNT)
		return &bopeebo_visual_page_table[logical_page - 1u];
	unsigned variant_slot = 1u + BOPEEBO_WEEK5_COMMON_PAGE_COUNT;
	if (evil_mall) {
		if (logical_page >= BOPEEBO_WEEK5_EVIL_FIRST_PAGE &&
			logical_page < BOPEEBO_WEEK5_EVIL_FIRST_PAGE + BOPEEBO_WEEK5_EVIL_PAGE_COUNT)
			return &bopeebo_visual_page_table[variant_slot];
	} else if (logical_page >= BOPEEBO_WEEK5_XMAS_FIRST_PAGE &&
		logical_page < BOPEEBO_WEEK5_XMAS_FIRST_PAGE + BOPEEBO_WEEK5_XMAS_PAGE_COUNT) {
		unsigned variant_page = logical_page - BOPEEBO_WEEK5_XMAS_FIRST_PAGE;
		if (variant_page == 0u) return &bopeebo_visual_page_table[variant_slot];
		if (variant_page == 1u) return &week5_spare_visual_page;
		if (variant_page == 2u) return &bopeebo_visual_page_table[8];
	}
	return 0;
}

static const BopeeboVisualPage *week4_visual_page_info(unsigned logical_page)
{
	/* W4 page 7 borrows the menu/logo 8bpp slot while gameplay owns VRAM.
	   Page 8 is the far-dancer atlas in the spare top-right page. The far-limo
	   frames are packed into W4 page 7 so the BF atlas at base page 7 stays live. */
	if (logical_page == 7u) return &bopeebo_visual_page_table[8];
	if (logical_page == 8u) return &week4_far_dancer_page;
	if (logical_page >= BOPEEBO_VIS