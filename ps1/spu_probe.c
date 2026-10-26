/* CD-to-SPU VAGi streaming probe; audio data is supplied locally at build time. */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
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
#include "bopeebo_chart.h"
#include "bopeebo_visual_data.h"
#include "menu_audio_data.h"
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
#define GAME_SCROLL_PIXELS_PER_SECOND 176u
#define CAMERA_FOCUS_TIME_MS 600u /* official FocusCamera default: four steps at 100 BPM */
#ifndef GAME_DAD_LANES_DEFAULT
#define GAME_DAD_LANES_DEFAULT 1
#endif
#ifndef GAME_DIAGNOSTICS_DEFAULT
#define GAME_DIAGNOSTICS_DEFAULT 0
#endif
#ifndef GAME_SCENE_DEMO_DEFAULT
#define GAME_SCENE_DEMO_DEFAULT 0
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
	SCREEN_PAUSE
} GameScreen;
static GameScreen game_screen = SCREEN_TITLE;
static uint32_t menu_ticks;
static bool menu_visuals_loaded;
static int menu_font_id = -1;
typedef struct { const char *song; const char *difficulty; } FreeplayEntry;
static const FreeplayEntry freeplay_catalog[] = {
	{ "BOPEEBO", "NORMAL" }
};

/* Separate geometry/state groups preserve the future two-player split. */
static const NoteGroupLayout note_groups[2] = {
	{ 24, 78, 18, 16, 24, 0 }, /* Dad/autoplay: 16px arrow edge aligns with action-safe x=16 */
	{ 176, 194, 32, 30, 100, 1 } /* BF/player: raised to leave clear lower margin */
};
static uint8_t game_note_state[BOPEEBO_NOTE_COUNT];
static int16_t active_hold[4] = { -1, -1, -1, -1 };
static uint32_t hold_last_sample[4];
static uint32_t receiver_flash_until[2][4];
static uint32_t hold_drops;
static int32_t score;
static uint32_t combo;
static uint32_t misses;
static uint32_t hits;
static uint16_t health_q8 = 256;
static bool bf_miss_silenced;
static uint8_t bf_visual_state;
static uint8_t bf_visual_lane;
static uint32_t bf_visual_start;
static uint32_t bf_visual_until;
static uint8_t dad_visual_lane;
static uint32_t dad_visual_start;
static uint32_t dad_visual_until;
static uint8_t last_judgement;
static uint32_t judgement_until;
static int32_t combo_popup_value = -1;
static uint32_t combo_popup_start_samples;
static uint32_t combo_popup_until;
static uint32_t last_judgement_delta_ms;
static bool judgement_drawn;
static uint16_t last_game_pressed;
#if GAME_JUDGEMENT_TEST_DEFAULT || GAME_JUDGEMENT_VISUAL_TEST_DEFAULT
static uint8_t judgement_test_next;
static uint8_t judgement_test_hits;
#endif
#if GAME_JUDGEMENT_TEST_DEFAULT
static int judgement_test_font_id = -1;
#endif
#if GAME_JUDGEMENT_VISUAL_TEST_DEFAULT
static int judgement_visual_font_id = -1;
#endif
static uint8_t camera_focus_display;
static bool camera_transitioning;
static bool dad_lanes_visible;
static bool diagnostics_visible;
static unsigned hud_display_health_percent;
static unsigned hud_actual_health_percent;
static int hud_health_boundary_x;
static int hud_dad_icon_x;
static int hud_bf_icon_x;
static POLY_F4 game_prims[GAME_MAX_PRIMS];
static unsigned game_prim_count;
static POLY_FT4 visual_prims[VISUAL_MAX_PRIMS];
static unsigned visual_prim_count;
static unsigned visual_prim_limit = VISUAL_MAX_PRIMS;
static unsigned visual_prim_high_water;
static unsigned visual_prim_rejected;
static unsigned gameplay_visual_prim_count;
static bool score_text_flushed;
typedef struct { uint8_t r, g, b; } GameColor;
static int hud_font_id = -1;
static int score_font_id = -1;
static int diagnostics_font_id = -1;

static bool hold_release_is_miss(uint32_t remaining_samples, uint32_t rate)
{
	return rate && (uint64_t)remaining_samples * 1000u > (uint64_t)rate * 160u;
}
#endif

typedef struct {
	uint32_t magic;
	uint32_t version;
	uint32_t interleave;
	uint32_t size;
	uint32_t sample_rate;
	uint16_t reserved[5];
	uint16_t channels;
	char name[16];
} VAG_Header;

typedef struct {
	int start_lba;
	int stream_length;
	int next_sector;
	volatile size_t refill_length;
	volatile int read_pending;
	volatile int read_error;
	volatile unsigned last_read_sectors;
	volatile unsigned total_requested_sectors;
	volatile unsigned total_received_sectors;
	volatile unsigned callbacks_received;
	volatile unsigned callbacks_complete;
	volatile unsigned callbacks_error;
	volatile int last_event;
	volatile uint8_t last_payload[4];
	volatile uint8_t last_sync_result[4];
	volatile int last_cdread_return;
	volatile int last_cdsync_return;
	volatile int error_cause;
	unsigned channels;
	bool loop;
	bool menu_music;
} StreamReadContext;

typedef struct {
	DISPENV display;
	DRAWENV draw;
} Frame;

static Frame frames[2];
static int draw_index;
static Stream_Context stream;
static StreamReadContext read_ctx;
static volatile unsigned underruns;
static volatile unsigned read_errors;
static int failure_code;
static bool stream_initialized;
#if TEST_CHANNELS >= 4
#define PAD_BYTES 34
static uint8_t pad_buffers[2][PAD_BYTES];
static uint16_t previous_pad_buttons = 0xffff;
static bool pad_was_connected;
static bool voices_muted;
static bool circle_down;
static uint16_t game_buttons;
static uint16_t game_pressed;
#endif
#if TEST_NO_LOOP
static bool song_finished;
#endif
#if TEST_BOPEEBO_4CH
static uint8_t pan_width = 5;
static uint8_t sfx_voice_cursor;
static uint32_t frame_counter;
static uint32_t sfx_voice_until_frame[SFX_VOICE_COUNT];
static bool sfx_voice_active[SFX_VOICE_COUNT];
static uint16_t sfx_voice_requested_volume[SFX_VOICE_COUNT];
static uint8_t sfx_random_state = 0x6du;
static unsigned sfx_last_voice = 0xffu;
static unsigned sfx_square_press_count;
static unsigned sfx_manual_trigger_count;
static unsigned sfx_auto_trigger_count;
static unsigned sfx_auto_during_count;
static uint32_t sfx_auto_during_next_frame;
static bool sfx_auto_during_started;
static bool sfx_square_down;
static size_t sfx_write_size;
static int sfx_transfer_completed;
static bool sfx_uploaded;
#endif
static void abort_cd_read(void);
static bool start_stream_from_disc(void);
#if TEST_PLAYABLE_BOPEEBO
static bool feed_stream(void);
static bool start_stream_file(const char *path, unsigned expected_channels,
	bool loop, bool menu_music);
static bool upload_menu_sfx(void);
static void play_menu_sfx(unsigned sound);
#endif

enum {
	SFX_KIND_PROBE_AUTO = 0,
	SFX_KIND_PROBE_MANUAL,
	SFX_KIND_MISS,
	SFX_KIND_GHOST_MISS
};

enum {
	FAIL_NOT_FOUND = 1,
	FAIL_HEADER_READ = 2,
	FAIL_HEADER_FORMAT = 3,
	FAIL_CD_COMMAND = 4,
	FAIL_CD_READ = 5,
	FAIL_BUFFER_TIMEOUT = 6,
	FAIL_STREAM_START = 7,
	FAIL_UNDERRUN = 8,
	FAIL_SFX_UPLOAD = 9
};

enum {
	READ_ERROR_NONE = 0,
	READ_ERROR_CALLBACK_DISK = 1,
	READ_ERROR_CALLBACK_EVENT = 2,
	READ_ERROR_START = 3,
	READ_ERROR_SYNC_TIMEOUT = 4,
	READ_ERROR_SYNC_ABORT = 5,
	READ_ERROR_SETLOC = 6,
	READ_ERROR_WAIT_TIMEOUT = 7
};

#define SWAP_ENDIAN(x) (((x) << 24) | (((x) & 0x0000ff00u) << 8) | \
	(((x) & 0x00ff0000u) >> 8) | ((x) >> 24))

static void set_read_error(int cause)
{
	if (!read_ctx.read_error) {
		read_ctx.error_cause = cause;
		read_errors++;
	}
	read_ctx.read_error = 1;
}

static void save_sync_result(const uint8_t *result)
{
	for (int i = 0; i < 4; i++)
		read_ctx.last_sync_result[i] = result[i];
}

static const char *read_error_name(int cause)
{
	switch (cause) {
	case READ_ERROR_CALLBACK_DISK: return "CALLBACK DISK ERROR";
	case READ_ERROR_CALLBACK_EVENT: return "UNEXPECTED CALLBACK";
	case READ_ERROR_START: return "CDREAD RETURNED 0";
	case READ_ERROR_SYNC_TIMEOUT: return "CDREADSYNC -1";
	case READ_ERROR_SYNC_ABORT: return "CDREADSYNC -2";
	case READ_ERROR_SETLOC: return "CD SETLOC FAILED";
	case READ_ERROR_WAIT_TIMEOUT: return "READ WAIT TIMEOUT";
	default: return "NONE";
	}
}

static void init_video(void)
{
	ResetGraph(0);
	FntLoad(960, 0);
#if TEST_PLAYABLE_BOPEEBO
		hud_font_id = FntOpen(32, 39, 256, 9, 0, 40);
		/* Keep the 96 px score row below the life-bar frame (y=19..35). */
		score_font_id = FntOpen(208, 37, 96, 9, 0, 16);
		diagnostics_font_id = FntOpen(
			GAME_HEALTH_BAR_TEST_DEFAULT ? 16 : 24, 56,
			GAME_HEALTH_BAR_TEST_DEFAULT ? 288 : 272,
			GAME_HEALTH_BAR_TEST_DEFAULT ? 24 : 164, 0,
			GAME_HEALTH_BAR_TEST_DEFAULT ? 80 : 512);
		menu_font_id = FntOpen(48, 183, 256, 42, 0, 48);
#endif
	for (int i = 0; i < 2; i++) {
		SetDefDrawEnv(&frames[i].draw, 0, i * SCREEN_H, SCREEN_W, SCREEN_H);
		SetDefDispEnv(&frames[i].display, 0, i * SCREEN_H, SCREEN_W, SCREEN_H);
		setRGB0(&frames[i].draw, 8, 8, 20);
		frames[i].draw.isbg = 1;
	}
	draw_index = 0;
	SetDispMask(1);
}

#if TEST_PLAYABLE_BOPEEBO
static void load_bopeebo_visuals(void)
{
	/* Keep the dedicated menu page out of the gameplay VRAM residency set. */
	unsigned menu_page = bopeebo_visual_frames[VIS_MENU_LOGO].page;
	for (unsigned page = 0; page < BOPEEBO_VISUAL_PAGE8_COUNT; page++) {
		if (page == menu_page) continue;
		const BopeeboVisualPage *info = &bopeebo_visual_page_table[page];
		RECT rect = { (short)info->x, (short)info->y, 128, 256 };
		LoadImage(&rect, (uint32_t *)bopeebo_visual_pages8[page]);
	}
	for (unsigned page = 0; page < BOPEEBO_VISUAL_PAGE4_COUNT; page++) {
		unsigned table_index = BOPEEBO_VISUAL_PAGE8_COUNT + page;
		const BopeeboVisualPage *info = &bopeebo_visual_page_table[table_index];
		RECT rect = { (short)info->x, (short)info->y, 64, 256 };
		LoadImage(&rect, (uint32_t *)bopeebo_visual_pages4[page]);
	}
	/* The second 320x240 framebuffer ends at y=495; keep CLUTs below it. */
	RECT palette8_rect = { 0, 496, 256, 1 };
	LoadImage(&palette8_rect, (uint32_t *)bopeebo_visual_palette8);
	RECT bf_palette8_rect = { 0, 480, 256, 1 };
	LoadImage(&bf_palette8_rect, (uint32_t *)bopeebo_visual_palette_bf8);
	RECT bf_palette_rect = { 256, 496, 16, 1 };
	LoadImage(&bf_palette_rect, (uint32_t *)bopeebo_visual_palette4);
	for (unsigned lane = 0; lane < 4u; lane++) {
		short x = lane == 3u ? 256 : (short)(272u + lane * 16u);
		short y = lane == 3u ? 480 : 496;
		RECT palette_rect = { x, y, 16, 1 };
		LoadImage(&palette_rect, (uint32_t *)bopeebo_visual_palette_ui4[lane]);
	}
	RECT popup_palette_rect = { 272, 480, 16, 1 };
	LoadImage(&popup_palette_rect, (uint32_t *)bopeebo_visual_palette_popup4);
	DrawSync(0);
}

static void load_menu_visuals(void)
{
	if (menu_visuals_loaded) return;
	unsigned page = bopeebo_visual_frames[VIS_MENU_LOGO].page;
	if (page >= BOPEEBO_VISUAL_PAGE8_COUNT) return;
	const BopeeboVisualPage *info = &bopeebo_visual_page_table[page];
	RECT rect = { (short)info->x, (short)info->y, 128, 256 };
	LoadImage(&rect, (uint32_t *)bopeebo_visual_pages8[page]);
	DrawSync(0);
	menu_visuals_loaded = true;
}

static void release_menu_visuals(void)
{
	if (!menu_visuals_loaded) return;
	unsigned page = bopeebo_visual_frames[VIS_MENU_LOGO].page;
	const BopeeboVisualPage *info = &bopeebo_visual_page_table[page];
	/* The SDK exposes GPU FILL primitives rather than PsyQ ClearImage(). */
	FILL fill;
	setFill(&fill);
	setRGB0(&fill, 0, 0, 0);
	setXY0(&fill, info->x, info->y);
	setWH(&fill, 128, 256);
	DrawPrim((uint32_t *)&fill);
	DrawSync(0);
	menu_visuals_loaded = false;
}
#endif

static void display_frame(void)
{
	draw_index ^= 1;
	DrawSync(0);
	VSync(0);
	PutDrawEnv(&frames[draw_index].draw);
	PutDispEnv(&frames[draw_index].display);
	SetDispMask(1);
}

static void show_error(int code)
{
	failure_code = code;
	abort_cd_read();
	if (Stream_IsActive(&stream))
		Stream_Stop();
	for (;;) {
		FntPrint(-1, "SPU STREAM ERROR / CODE %d\n\n", code);
		FntPrint(-1, "CD ERRORS %u  UNDERRUNS %u\n", (unsigned)read_errors,
			(unsigned)underruns);
		FntPrint(-1, "BUFFER %u / %u\n", (unsigned)stream.buffer.length,
			(unsigned)stream.config.buffer_size);
		FntPrint(-1, "READ PENDING %d\n", (int)read_ctx.read_pending);
		FntPrint(-1, "SECTORS REQ %lu  LAST %u\n",
			(unsigned long)read_ctx.total_requested_sectors,
			(unsigned)read_ctx.last_read_sectors);
		FntPrint(-1, "CALLBACKS %u  OK %u  ERR %u\n",
			(unsigned)read_ctx.callbacks_received,
			(unsigned)read_ctx.callbacks_complete,
			(unsigned)read_ctx.callbacks_error);
		FntPrint(-1, "SECTORS RX %lu\n", (unsigned long)read_ctx.total_received_sectors);
		FntPrint(-1, "LAST EVT %d  DATA %02X %02X %02X %02X\n",
			(int)read_ctx.last_event, (unsigned)read_ctx.last_payload[0],
			(unsigned)read_ctx.last_payload[1], (unsigned)read_ctx.last_payload[2],
			(unsigned)read_ctx.last_payload[3]);
		FntPrint(-1, "CDREAD %d  CDSYNC %d\n", (int)read_ctx.last_cdread_return,
			(int)read_ctx.last_cdsync_return);
		FntPrint(-1, "SYNC DATA %02X %02X %02X %02X\n",
			(unsigned)read_ctx.last_sync_result[0], (unsigned)read_ctx.last_sync_result[1],
			(unsigned)read_ctx.last_sync_result[2], (unsigned)read_ctx.last_sync_result[3]);
		FntPrint(-1, "CAUSE %d: %s\n", (int)read_ctx.error_cause,
			read_error_name(read_ctx.error_cause));
#if TEST_BOPEEBO_4CH
#if !TEST_PLAYABLE_BOPEEBO
		FntPrint(-1, "SFX WRITE %u/%u DMA %d ADDR %05X\n",
			(unsigned)sfx_write_size, (unsigned)SFX_SAMPLE_SIZE,
			sfx_transfer_completed, (unsigned)SFX_SPU_ADDR);
#endif
#endif
		FntFlush(-1);
		display_frame();
	}
}

static void cd_read_handler(CdlIntrResult event, uint8_t *payload)
{
	read_ctx.last_event = (int)event;
	for (int i = 0; i < 4; i++)
		read_ctx.last_payload[i] = payload ? payload[i] : 0;
	read_ctx.callbacks_received++;
	if (event == CdlDiskError) {
		read_ctx.callbacks_error++;
		set_read_error(READ_ERROR_CALLBACK_DISK);
		read_ctx.read_pending = 0;
		return;
	}
	/* PSn00bSDK 0.24 reports the final sector as CdlDataReady (1).
	 * CdlComplete is not the success callback for CdRead(). */
	if (event != CdlDataReady) {
		read_ctx.callbacks_error++;
		set_read_error(READ_ERROR_CALLBACK_EVENT);
		read_ctx.read_pending = 0;
		return;
	}
	read_ctx.callbacks_complete++;
	if (read_ctx.refill_length) {
		read_ctx.total_received_sectors += read_ctx.last_read_sectors;
		Stream_Feed(&stream, read_ctx.refill_length * CD_SECTOR_SIZE);
	}
	read_ctx.read_pending = 0;
}

static void stream_underrun_handler(void)
{
	underruns++;
}

#if TEST_CHANNELS >= 4
#if TEST_BOPEEBO_4CH
static const uint16_t pan_curve[8][2] = {
	{ 11585, 11585 }, { 12809, 10215 }, { 13872, 8716 }, { 14761, 7108 },
	{ 15464, 5411 }, { 15972, 3646 }, { 16280, 1834 }, { 16383, 0 }
};

static void set_voice_pan(void)
{
	uint16_t left = (uint16_t)((uint32_t)MUSIC_SPAN_GAIN * pan_curve[pan_width][0] / 16383u);
	uint16_t right = (uint16_t)((uint32_t)MUSIC_SPAN_GAIN * pan_curve[pan_width][1] / 16383u);
	SPU_CH_VOL_L(2) = left;
	SPU_CH_VOL_R(2) = right;
	SPU_CH_VOL_L(3) = (voices_muted
#if TEST_PLAYABLE_BOPEEBO
		|| bf_miss_silenced
#endif
		) ? 0 : right;
	SPU_CH_VOL_R(3) = (voices_muted
#if TEST_PLAYABLE_BOPEEBO
		|| bf_miss_silenced
#endif
		) ? 0 : left;
}

static unsigned active_sfx_voice_count(void)
{
	unsigned count = 0;
	for (unsigned i = 0; i < SFX_VOICE_COUNT; i++)
		count += sfx_voice_active[i] ? 1u : 0u;
	return count;
}

static void update_sfx_pool_volumes(void)
{
	unsigned count = active_sfx_voice_count();
	if (!count)
		return;
	unsigned total = 0;
	for (unsigned i = 0; i < SFX_VOICE_COUNT; i++)
		if (sfx_voice_active[i]) total += sfx_voice_requested_volume[i];
	for (unsigned i = 0; i < SFX_VOICE_COUNT; i++) {
		if (!sfx_voice_active[i])
			continue;
		unsigned voice = SFX_FIRST_VOICE + i;
		uint32_t volume = sfx_voice_requested_volume[i];
		if (total > SFX_POOL_VOLUME_BUDGET)
			volume = volume * SFX_POOL_VOLUME_BUDGET / total;
		SPU_CH_VOL_L(voice) = (uint16_t)volume;
		SPU_CH_VOL_R(voice) = (uint16_t)volume;
	}
}

static void maintain_sfx_pool(void)
{
	for (unsigned i = 0; i < SFX_VOICE_COUNT; i++) {
		if (sfx_voice_active[i] && frame_counter >= sfx_voice_until_frame[i]) {
			SpuSetKey(0, 1u << (SFX_FIRST_VOICE + i));
			sfx_voice_active[i] = false;
		}
	}
	update_sfx_pool_volumes();
}

static uint8_t next_sfx_random(void)
{
	/* Small deterministic PRNG: stable selection/volume variation without libc rand(). */
	sfx_random_state ^= (uint8_t)(sfx_random_state << 3);
	sfx_random_state ^= (uint8_t)(sfx_random_state >> 5);
	sfx_random_state ^= (uint8_t)(sfx_random_state << 1);
	return sfx_random_state;
}

static void play_resident_sfx(bool manual, unsigned kind)
{
	maintain_sfx_pool();
	unsigned slot = SFX_VOICE_COUNT;
	for (unsigned offset = 0; offset < SFX_VOICE_COUNT; offset++) {
		unsigned candidate = (sfx_voice_cursor + offset) % SFX_VOICE_COUNT;
		if (!sfx_voice_active[candidate]) {
			slot = candidate;
			break;
		}
	}
	if (slot == SFX_VOICE_COUNT) {
		slot = 0;
		for (unsigned i = 1; i < SFX_VOICE_COUNT; i++) {
			if (sfx_voice_until_frame[i] < sfx_voice_until_frame[slot])
				slot = i;
		}
		SpuSetKey(0, 1u << (SFX_FIRST_VOICE + slot));
		sfx_voice_active[slot] = false;
	}
	unsigned voice = SFX_FIRST_VOICE + slot;
	uint32_t key = 1u << voice;
	uint32_t sample_offset = 0;
	uint32_t duration_frames = SFX_BUSY_FRAMES;
	uint32_t sample_rate =
#if TEST_PLAYABLE_BOPEEBO
		MENU_SFX_RATE;
#else
		SFX_SAMPLE_RATE;
#endif
	uint16_t requested_volume = (uint16_t)(SFX_POOL_VOLUME_BUDGET / SFX_VOICE_COUNT);
#if TEST_PLAYABLE_BOPEEBO
	static const uint32_t miss_offsets[3] = {
		MISS_SFX_MISSNOTE1_OFFSET, MISS_SFX_MISSNOTE2_OFFSET, MISS_SFX_MISSNOTE3_OFFSET
	};
	static const uint32_t miss_frames[3] = {
		MISS_SFX_MISSNOTE1_FRAMES, MISS_SFX_MISSNOTE2_FRAMES, MISS_SFX_MISSNOTE3_FRAMES
	};
	if (kind == SFX_KIND_MISS || kind == SFX_KIND_GHOST_MISS) {
		unsigned variant = next_sfx_random() % 3u;
		sample_offset = miss_offsets[variant];
		duration_frames = miss_frames[variant] + 2u;
		sample_rate = MENU_SFX_RATE;
		unsigned percent = (kind == SFX_KIND_GHOST_MISS ? 10u : 50u) +
			next_sfx_random() % (kind == SFX_KIND_GHOST_MISS ? 11u : 11u);
		requested_volume = (uint16_t)(0x3fffu * percent / 100u);
	}
#else
	(void)kind;
#endif
	SpuSetKey(0, key);
	SPU_CH_ADDR(voice) = getSPUAddr(
#if TEST_PLAYABLE_BOPEEBO
		MENU_SFX_SPURAM_ADDR + sample_offset
#else
		SFX_SPU_ADDR
#endif
	);
	SPU_CH_FREQ(voice) = getSPUSampleRate(sample_rate);
	SPU_CH_ADSR1(voice) = 0x00ff;
	SPU_CH_ADSR2(voice) = 0x0000;
	sfx_voice_active[slot] = true;
	sfx_voice_requested_volume[slot] = requested_volume;
	sfx_voice_until_frame[slot] = frame_counter + duration_frames;
	update_sfx_pool_volumes();
	SpuSetKey(1, key);
	sfx_last_voice = voice;
	sfx_voice_cursor = (uint8_t)((slot + 1u) % SFX_VOICE_COUNT);
	if (manual)
		sfx_manual_trigger_count++;
	else
		sfx_auto_trigger_count++;
}

#if !TEST_PLAYABLE_BOPEEBO
static bool upload_resident_sfx(void)
{
	SpuSetTransferMode(SPU_TRANSFER_BY_DMA);
	SpuSetTransferStartAddr(SFX_SPU_ADDR);
	sfx_write_size = SpuWrite((const uint32_t *)sfx_sample, SFX_SAMPLE_SIZE);
	sfx_transfer_completed = SpuIsTransferCompleted(SPU_TRANSFER_WAIT);
	if (sfx_write_size != SFX_SAMPLE_SIZE || !sfx_transfer_completed)
		return false;
	sfx_uploaded = true;
	return true;
}

static void run_pre_music_sfx_test(void)
{
	play_resident_sfx(false, SFX_KIND_PROBE_AUTO);
	for (unsigned frame = 0; frame < SFX_BUSY_FRAMES + 2u; frame++) {
		maintain_sfx_pool();
		FntPrint(-1, "BOPEEBO SFX DIAGNOSTIC\n\n");
		FntPrint(-1, "AUTOMATIC PRE-MUSIC TEST\n");
		FntPrint(-1, "TRIGGER SENT  VOICE %u\n", sfx_last_voice);
		FntPrint(-1, "UPLOAD %u/%u  ADDR %05X\n", (unsigned)sfx_write_size,
			(unsigned)SFX_SAMPLE_SIZE, (unsigned)SFX_SPU_ADDR);
		FntPrint(-1, "TRANSFER COMPLETE %d\n", sfx_transfer_completed);
		FntFlush(-1);
		display_frame();
		frame_counter++;
	}
}

static void run_during_music_sfx_test(uint32_t samples)
{
	if (!sfx_auto_during_started && samples >= SFX_AUTO_DURING_START_SAMPLES) {
		sfx_auto_during_started = true;
		sfx_auto_during_next_frame = frame_counter;
	}
	if (sfx_auto_during_started && sfx_auto_during_count < SFX_AUTO_DURING_COUNT &&
	    frame_counter >= sfx_auto_during_next_frame) {
		play_resident_sfx(false, SFX_KIND_PROBE_AUTO);
		sfx_auto_during_count++;
		sfx_auto_during_next_frame = frame_counter + 2u;
	}
}
#endif

static bool poll_bopeebo4_controls(void)
{
	PADTYPE *pad = (PADTYPE *)&pad_buffers[0][0];
	bool connected = pad->stat == 0 &&
		(pad->type == PAD_ID_DIGITAL || pad->type == PAD_ID_ANALOG_STICK ||
		 pad->type == PAD_ID_ANALOG);
	if (!connected) {
		previous_pad_buttons = 0xffff;
		pad_was_connected = false;
		circle_down = false;
		sfx_square_down = false;
		game_buttons = 0xffff;
		game_pressed = 0;
		return false;
	}

	uint16_t buttons = (uint16_t)pad->btn;
	game_buttons = buttons;
	circle_down = !(buttons & PAD_CIRCLE);
	sfx_square_down = !(buttons & PAD_SQUARE);
	if (!pad_was_connected) {
		previous_pad_buttons = buttons;
		pad_was_connected = true;
		game_pressed = 0;
	} else {
		game_pressed = (uint16_t)(previous_pad_buttons & (uint16_t)~buttons);
#if TEST_PLAYABLE_BOPEEBO
		if (game_screen == SCREEN_GAMEPLAY &&
		    (previous_pad_buttons & PAD_CIRCLE) && !(buttons & PAD_CIRCLE))
			voices_muted = !voices_muted;
		if (game_screen == SCREEN_GAMEPLAY &&
		    (previous_pad_buttons & PAD_SELECT) && !(buttons & PAD_SELECT))
			diagnostics_visible = !diagnostics_visible;
		if (game_screen == SCREEN_GAMEPLAY &&
		    (previous_pad_buttons & PAD_TRIANGLE) && !(buttons & PAD_TRIANGLE))
			dad_lanes_visible = !dad_lanes_visible;
		if (game_screen == SCREEN_GAMEPLAY &&
		    (previous_pad_buttons & PAD_L1) && !(buttons & PAD_L1) && pan_width)
			pan_width--;
		if (game_screen == SCREEN_GAMEPLAY &&
		    (previous_pad_buttons & PAD_R1) && !(buttons & PAD_R1) && pan_width < 7u)
			pan_width++;
#else
		if ((previous_pad_buttons & PAD_SQUARE) && !(buttons & PAD_SQUARE)) {
			sfx_square_press_count++;
			if (sfx_uploaded)
				play_resident_sfx(true, SFX_KIND_PROBE_MANUAL);
		}
		if ((previous_pad_buttons & PAD_CIRCLE) && !(buttons & PAD_CIRCLE))
			voices_muted = !voices_muted;
		if ((previous_pad_buttons & PAD_LEFT) && !(buttons & PAD_LEFT) && pan_width)
			pan_width--;
		if ((previous_pad_buttons & PAD_RIGHT) && !(buttons & PAD_RIGHT) && pan_width < 7u)
			pan_width++;
#endif
		previous_pad_buttons = buttons;
	}
	maintain_sfx_pool();
	set_voice_pan();
	return true;
}
#else
static bool poll_voice_toggle(void)
{
	PADTYPE *pad = (PADTYPE *)&pad_buffers[0][0];
	bool connected = pad->stat == 0 &&
		(pad->type == PAD_ID_DIGITAL || pad->type == PAD_ID_ANALOG_STICK ||
		 pad->type == PAD_ID_ANALOG);
	if (!connected) {
		previous_pad_buttons = 0xffff;
		pad_was_connected = false;
		circle_down = false;
		return false;
	}

	uint16_t buttons = (uint16_t)pad->btn;
	circle_down = !(buttons & PAD_CIRCLE);
	if (!pad_was_connected) {
		previous_pad_buttons = buttons;
		pad_was_connected = true;
	} else {
		if ((previous_pad_buttons & PAD_CIRCLE) && !(buttons & PAD_CIRCLE))
			voices_muted = !voices_muted;
		previous_pad_buttons = buttons;
	}

	SPU_CH_VOL_L(2) = voices_muted ? 0 :
#if TEST_CHANNELS == 4
		TEST_VOICE_VOLUME;
#else
		SONG_MIX_VOLUME;
#endif
	SPU_CH_VOL_R(2) = 0;
	SPU_CH_VOL_L(3) = 0;
	SPU_CH_VOL_R(3) = voices_muted ? 0 :
#if TEST_CHANNELS == 4
		TEST_VOICE_VOLUME;
#else
		SONG_MIX_VOLUME;
#endif
	return true;
}
#endif
#endif

#if TEST_PLAYABLE_BOPEEBO
static void add_health(int amount)
{
	int value = (int)health_q8 + amount;
	if (value < 0) value = 0;
	if (value > 512) value = 512;
	health_q8 = (uint16_t)value;
}

static int32_t pbot1_score(uint32_t delta_samples, uint32_t rate)
{
	uint64_t scaled = (uint64_t)delta_samples * 1000u;
	if (scaled > (uint64_t)rate * 160u) return -100;
	uint32_t whole_ms = (uint32_t)(scaled / rate);
	uint32_t remainder = (uint32_t)(scaled % rate);
	if (whole_ms >= 160u) return pbot1_score_by_ms[160];
	int32_t a = pbot1_score_by_ms[whole_ms];
	int32_t b = pbot1_score_by_ms[whole_ms + 1u];
	return a + (b - a) * (int32_t)remainder / (int32_t)rate;
}

static void update_combo_popup(uint32_t previous_combo, uint32_t current_combo,
	uint32_t samples, uint32_t rate)
{
	if (current_combo >= 10u)
		combo_popup_value = (int32_t)current_combo;
	else if (previous_combo >= 10u)
		combo_popup_value = 0; /* Original PlayState briefly displays 000 on a break. */
	else {
		combo_popup_value = -1;
		combo_popup_start_samples = 0;
		combo_popup_until = 0;
		return;
	}
	combo_popup_start_samples = samples;

	unsigned tempo_index = 0;
	while (tempo_index + 1u < BOPEEBO_TEMPO_CHANGE_COUNT &&
		bopeebo_tempo_changes[tempo_index + 1u].sample <= samples)
		tempo_index++;
	uint32_t bpm_centi = bopeebo_tempo_changes[tempo_index].bpm_centi;
	uint64_t two_beats = bpm_centi ? (uint64_t)rate * 12000u / bpm_centi : (uint64_t)rate;
	combo_popup_until = samples + (uint32_t)(two_beats + rate / 5u);
}

static int find_player_note(unsigned lane, uint32_t samples)
{
	int best = -1;
	uint32_t best_delta = GAME_WINDOW_SAMPLES + 1u;
	uint32_t rate = stream.config.sample_rate ? (uint32_t)stream.config.sample_rate : BOPEEBO_CHART_RATE;
	for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++) {
		if (game_note_state[i] || bopeebo_notes[i].lane >= 4u ||
		    bopeebo_notes[i].lane != lane)
			continue;
		uint32_t delta = samples > bopeebo_notes[i].head ?
			samples - bopeebo_notes[i].head : bopeebo_notes[i].head - samples;
		if ((uint64_t)delta * 1000u <= (uint64_t)rate * 160u && delta < best_delta) {
			best = (int)i;
			best_delta = delta;
		}
	}
	return best;
}

static void game_miss(unsigned index, uint32_t samples, uint32_t rate)
{
	game_note_state[index] = 2;
	misses++;
	uint32_t previous_combo = combo;
	combo = 0;
	score -= 100;
	update_combo_popup(previous_combo, combo, samples, rate);
	add_health(-20);
	bf_miss_silenced = true;
	bf_visual_state = 2;
	bf_visual_lane = (uint8_t)(bopeebo_notes[index].lane & 3u);
	bf_visual_until = samples + rate * 350u / 1000u;
	last_judgement = 4u; /* miss -> Shit; does not alter existing judgement math */
	last_judgement_delta_ms = 0xffffffffu;
	judgement_until = samples + rate * 650u / 1000u;
	bf_visual_start = samples;
	play_resident_sfx(false, SFX_KIND_MISS);
	set_voice_pan();
}

static void game_hold_drop(unsigned lane, uint32_t remaining_samples, uint32_t rate,
	uint32_t samples)
{
	hold_drops++;
	uint32_t previous_combo = combo;
	combo = 0;
	int32_t hold_penalty = (int32_t)(((uint64_t)remaining_samples * 125u) / rate);
	score -= hold_penalty;
	update_combo_popup(previous_combo, combo, samples, rate);
	bf_miss_silenced = true;
	bf_visual_state = 2;
	bf_visual_lane = (uint8_t)lane;
	bf_visual_start = samples;
	bf_visual_until = samples + rate * 350u / 1000u;
	last_judgement = 4u;
	last_judgement_delta_ms = 0xffffffffu;
	judgement_until = samples + rate * 650u / 1000u;
	play_resident_sfx(false, SFX_KIND_MISS);
	set_voice_pan();
}

static void game_update(uint32_t samples)
{
	uint32_t rate = stream.config.sample_rate ? (uint32_t)stream.config.sample_rate : BOPEEBO_CHART_RATE;
	static const uint16_t masks[4] = { PAD_LEFT, PAD_DOWN, PAD_UP, PAD_RIGHT };
	for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++) {
		if (bopeebo_notes[i].lane >= 4u && !game_note_state[i] && samples >= bopeebo_notes[i].head) {
			game_note_state[i] = 3; /* Dad chart lane: audio stem performs the note. */
			dad_visual_lane = (uint8_t)(bopeebo_notes[i].lane & 3u);
			receiver_flash_until[0][dad_visual_lane] = samples + rate * 140u / 1000u;
			dad_visual_start = samples;
			dad_visual_until = bopeebo_notes[i].tail > bopeebo_notes[i].head ?
				bopeebo_notes[i].tail : samples + rate * 250u / 1000u;
		}
		if (bopeebo_notes[i].lane < 4u && !game_note_state[i] &&
		    samples > bopeebo_notes[i].head &&
		    (uint64_t)(samples - bopeebo_notes[i].head) * 1000u > (uint64_t)rate * 160u)
			game_miss(i, samples, rate);
	}

	for (unsigned lane = 0; lane < 4; lane++) {
		uint16_t mask = masks[lane];
		bool down = (game_buttons & mask) == 0;
		int16_t index = active_hold[lane];
		if (index >= 0) {
			uint32_t end = bopeebo_notes[index].tail;
			uint32_t until = samples < end ? samples : end;
			if (until > hold_last_sample[lane]) {
				uint32_t delta = until - hold_last_sample[lane];
				score += (uint32_t)(((uint64_t)delta * 250u) / rate);
				add_health((int)(((uint64_t)delta * 31u) / rate));
				hold_last_sample[lane] = until;
			}
			if (samples >= end) {
				active_hold[lane] = -1;
			} else if (!down) {
				uint32_t remaining = end - samples;
				if (hold_release_is_miss(remaining, rate))
					game_hold_drop(lane, remaining, rate, samples);
				active_hold[lane] = -1;
			}
		}
	}

	for (unsigned lane = 0; lane < 4; lane++) {
		uint16_t mask = masks[lane];
		if (!(game_pressed & mask)) continue;
		last_game_pressed = mask;
		int target = find_player_note(lane, samples);
		if (target < 0) {
			uint32_t previous_combo = combo;
			combo = 0;
			score -= 10;
			update_combo_popup(previous_combo, combo, samples, rate);
			add_health(-20);
			play_resident_sfx(false, SFX_KIND_GHOST_MISS);
			bf_visual_state = 2;
			bf_visual_lane = (uint8_t)lane;
			bf_visual_start = samples;
			bf_visual_until = samples + rate * 350u / 1000u;
			last_judgement = 4u;
			last_judgement_delta_ms = 0xffffffffu;
			judgement_until = samples + rate * 650u / 1000u;
			continue;
		}
		uint32_t head = bopeebo_notes[target].head;
		uint32_t diff = samples > head ? samples - head : head - samples;
		game_note_state[target] = 1;
		int32_t award = pbot1_score(diff, rate);
		score += award;
		uint32_t previous_combo = combo;
		uint64_t timing = (uint64_t)diff * 1000u;
		last_judgement_delta_ms = (uint32_t)(timing / rate);
		if (timing <= (uint64_t)rate * 45u) { combo++; add_health(8); last_judgement = 1u; }
		else if (timing <= (uint64_t)rate * 90u) { combo++; add_health(4); last_judgement = 2u; }
		else if (timing <= (uint64_t)rate * 135u) { combo = 0; last_judgement = 3u; }
		else { combo = 0; add_health(-5); last_judgement = 4u; }
		update_combo_popup(previous_combo, combo, samples, rate);
		judgement_until = samples + rate * 650u / 1000u;
		hits++;
		receiver_flash_until[1][lane] = samples + rate * 140u / 1000u;
		bf_miss_silenced = false;
		bf_visual_state = 1;
		bf_visual_lane = (uint8_t)lane;
		bf_visual_until = bopeebo_notes[target].tail > samples ?
			bopeebo_notes[target].tail : samples + rate * 220u / 1000u;
		if (bopeebo_notes[target].tail > head && (game_buttons & mask) == 0) {
			active_hold[lane] = (int16_t)target;
			hold_last_sample[lane] = samples;
		}
	}
	if (bf_visual_state && samples >= bf_visual_until) bf_visual_state = 0;
	game_pressed = 0;
	set_voice_pan();
}

#if GAME_JUDGEMENT_TEST_DEFAULT || GAME_JUDGEMENT_VISUAL_TEST_DEFAULT
/* Separate no-controller QA image: press four chart taps through the normal
   game_update path, at offsets that deterministically map to Sick/Good/Bad/Shit. */
static void inject_judgement_test_hit(uint32_t samples, uint32_t rate)
{
	static const uint8_t note_indices[4] = { 3u, 9u, 16u, 22u };
	static const uint8_t offsets_ms[4] = { 0u, 60u, 110u, 150u };
	if (judgement_test_next >= 4u) return;
	/* Retire unrelated BF notes only in this QA build so their misses cannot
	   replace a popup before its 650 ms visual window has elapsed. */
	for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++) {
		if (bopeebo_notes[i].lane >= 4u) continue;
		bool scheduled = false;
		for (unsigned j = judgement_test_next; j < 4u; j++)
			if (note_indices[j] == i) scheduled = true;
		if (!scheduled && !game_note_state[i]) game_note_state[i] = 1u;
	}
	const BopeeboNote *note = &bopeebo_notes[note_indices[judgement_test_next]];
	if (note->lane >= 4u || note->tail != note->head) return;
	uint32_t target = note->head + (uint32_t)(((uint64_t)rate * offsets_ms[judgement_test_next]) / 1000u);
	if (samples < target) return;
	static const uint16_t masks[4] = { PAD_LEFT, PAD_DOWN, PAD_UP, PAD_RIGHT };
	game_buttons = 0xffffu;
	game_pressed = masks[note->lane];
	judgement_test_next++;
}
#endif

static void draw_rect(int x, int y, int width, int height, uint8_t r, uint8_t g, uint8_t b)
{
	if (game_prim_count >= GAME_MAX_PRIMS || width <= 0 || height <= 0) return;
	POLY_F4 *p = &game_prims[game_prim_count++];
	setPolyF4(p);
	setRGB0(p, r, g, b);
	setXY4(p, x, y, x + width, y, x, y + height, x + width, y + height);
	DrawPrim((uint32_t *)p);
}

static void draw_triangle(int x0, int y0, int x1, int y1, int x2, int y2,
	uint8_t r, uint8_t g, uint8_t b)
{
	if (game_prim_count >= GAME_MAX_PRIMS) return;
	POLY_F3 *p = (POLY_F3 *)&game_prims[game_prim_count++];
	setPolyF3(p);
	setRGB0(p, r, g, b);
	setXY3(p, x0, y0, x1, y1, x2, y2);
	DrawPrim((uint32_t *)p);
}

static void set_visual_clut(POLY_FT4 *p, const BopeeboVisualFrame *visual)
{
	if (visual->palette == 1u) setClut(p, 256, 496);
	else if (visual->palette == 2u) setClut(p, 0, 480);
	else if (visual->palette >= 3u && visual->palette <= 5u)
		setClut(p, 272 + (visual->palette - 3u) * 16u, 496);
	else if (visual->palette == 6u) setClut(p, 256, 480);
	else if (visual->palette == 7u) setClut(p, 272, 480);
	else setClut(p, 0, 496);
}

static bool draw_textured_frame_tinted(unsigned frame, int x, int y, int width, int height,
	uint8_t r, uint8_t g, uint8_t b)
{
	if (visual_prim_count >= visual_prim_limit) {
		visual_prim_rejected++;
		return false;
	}
	if (frame >= BOPEEBO_VISUAL_FRAME_COUNT || width <= 0 || height <= 0) return false;
	const BopeeboVisualFrame *visual = &bopeebo_visual_frames[frame];
	const BopeeboVisualPage *page = &bopeebo_visual_page_table[visual->page];
	POLY_FT4 *p = &visual_prims[visual_prim_count++];
	if (visual_prim_count > visual_prim_high_water) visual_prim_high_water = visual_prim_count;
	setPolyFT4(p);
	setRGB0(p, r, g, b);
	setXY4(p, x, y, x + width, y, x, y + height, x + width, y + height);
	setUV4(p, visual->u, visual->v,
		(uint8_t)(visual->u + visual->w - 1u), visual->v,
		visual->u, (uint8_t)(visual->v + visual->h - 1u),
		(uint8_t)(visual->u + visual->w - 1u), (uint8_t)(visual->v + visual->h - 1u));
	p->tpage = getTPage(page->depth, 0, page->x, page->y);
	set_visual_clut(p, visual);
	DrawPrim((uint32_t *)p);
	return true;
}

static bool draw_textured_frame(unsigned frame, int x, int y, int width, int height)
{
	return draw_textured_frame_tinted(frame, x, y, width, height, 128, 128, 128);
}

/* Sustain-only UV flip: rotate body and end-cap 180 degrees, leaving arrows
   and receptors on the existing texture path. */
static bool draw_textured_frame_rotated_180(unsigned frame, int x, int y,
	int width, int height)
{
	if (visual_prim_count >= visual_prim_limit) {
		visual_prim_rejected++;
		return false;
	}
	if (frame >= BOPEEBO_VISUAL_FRAME_COUNT || width <= 0 || height <= 0) return false;
	const BopeeboVisualFrame *visual = &bopeebo_visual_frames[frame];
	const BopeeboVisualPage *page = &bopeebo_visual_page_table[visual->page];
	POLY_FT4 *p = &visual_prims[visual_prim_count++];
	if (visual_prim_count > visual_prim_high_water) visual_prim_high_water = visual_prim_count;
	setPolyFT4(p);
	setRGB0(p, 128, 128, 128);
	setXY4(p, x, y, x + width, y, x, y + height, x + width, y + height);
	uint8_t u0 = visual->u, v0 = visual->v;
	uint8_t u1 = (uint8_t)(visual->u + visual->w - 1u);
	uint8_t v1 = (uint8_t)(visual->v + visual->h - 1u);
	setUV4(p, u1, v1, u0, v1, u1, v0, u0, v0);
	p->tpage = getTPage(page->depth, 0, page->x, page->y);
	set_visual_clut(p, visual);
	DrawPrim((uint32_t *)p);
	return true;
}

static void draw_visual_frame(unsigned frame, int world_x, int world_y,
	int camera_x, int camera_y, unsigned zoom_q8, unsigned scale_q8)
{
	if (visual_prim_count >= visual_prim_limit) {
		visual_prim_rejected++;
		return;
	}
	if (frame >= BOPEEBO_VISUAL_FRAME_COUNT) return;
	const BopeeboVisualFrame *visual = &bopeebo_visual_frames[frame];
	const BopeeboVisualPage *page = &bopeebo_visual_page_table[visual->page];
	POLY_FT4 *p = &visual_prims[visual_prim_count++];
	if (visual_prim_count > visual_prim_high_water) visual_prim_high_water = visual_prim_count;
	unsigned combined_scale = zoom_q8 * scale_q8 / 256u;
	int x0 = 160 + ((world_x - camera_x) * (int)combined_scale) / 256;
	int y0 = 120 + ((world_y - camera_y) * (int)combined_scale) / 256;
	int w = ((int)visual->w * (int)combined_scale) / 256;
	int h = ((int)visual->h * (int)combined_scale) / 256;
	setPolyFT4(p);
	setRGB0(p, 128, 128, 128);
	setXY4(p, x0, y0, x0 + w, y0, x0, y0 + h, x0 + w, y0 + h);
	setUV4(p, visual->u, visual->v,
		(uint8_t)(visual->u + visual->w - 1u), visual->v,
		visual->u, (uint8_t)(visual->v + visual->h - 1u),
		(uint8_t)(visual->u + visual->w - 1u), (uint8_t)(visual->v + visual->h - 1u));
	p->tpage = getTPage(page->depth, 0, page->x, page->y);
	set_visual_clut(p, visual);
	DrawPrim((uint32_t *)p);
}

static int note_screen_y(uint32_t target, uint32_t samples, const NoteGroupLayout *layout,
	uint32_t rate)
{
	int64_t delta = (int64_t)target - (int64_t)samples;
	uint32_t speed = layout->lane_group ? GAME_SCROLL_PIXELS_PER_SECOND : 124u;
	return layout->receptor_y - (int)((delta * speed) / rate);
}

static void draw_hold_body(int center_x, int y0, int y1, unsigned size, unsigned direction,
	int top_clip, int bottom_clip)
{
	int top = y0 < y1 ? y0 : y1;
	int bottom = y0 > y1 ? y0 : y1;
	if (top < top_clip) top = top_clip;
	if (bottom > bottom_clip) bottom = bottom_clip;
	if (bottom <= top) return;
	int width = (int)size / 3;
	if (width < 8) width = 8;
	/* The frame IDs are direction-indexed and retain the official VAG hold art. */
	static const uint8_t hold_body[4] = {
		VIS_UI_HOLD_BODY_LEFT, VIS_UI_HOLD_BODY_DOWN, VIS_UI_HOLD_BODY_UP, VIS_UI_HOLD_BODY_RIGHT
	};
	static const uint8_t hold_tail[4] = {
		VIS_UI_HOLD_TAIL_LEFT, VIS_UI_HOLD_TAIL_DOWN, VIS_UI_HOLD_TAIL_UP, VIS_UI_HOLD_TAIL_RIGHT
	};
	/* The cap belongs at the upper end of a hold. Draw it first, then let
	   the body overlap it so the seam is hidden behind the sustain column. */
	draw_textured_frame_rotated_180(hold_tail[direction & 3u], center_x - width / 2, top,
		width, 12);
	if (bottom - top > 12)
		draw_textured_frame_rotated_180(hold_body[direction & 3u], center_x - width / 2, top + 8,
			width, bottom - top - 8);
}

static void draw_note_group(uint32_t samples, unsigned group_index)
{
	const NoteGroupLayout *layout = &note_groups[group_index];
	uint32_t rate = stream.config.sample_rate ? (uint32_t)stream.config.sample_rate : BOPEEBO_CHART_RATE;
	if (group_index == 0u && !dad_lanes_visible) return;
	int bottom_clip = layout->receptor_y + (int)layout->arrow_size / 2 + 4;
	static const uint8_t note_frame[4] = {
		VIS_UI_NOTE_LEFT, VIS_UI_NOTE_DOWN, VIS_UI_NOTE_UP, VIS_UI_NOTE_RIGHT
	};
	static const uint8_t idle_frame[4] = {
		VIS_UI_RECEPTOR_LEFT_IDLE, VIS_UI_RECEPTOR_DOWN_IDLE,
		VIS_UI_RECEPTOR_UP_IDLE, VIS_UI_RECEPTOR_RIGHT_IDLE
	};
	static const uint8_t press_frame[4] = {
		VIS_UI_RECEPTOR_LEFT_PRESS, VIS_UI_RECEPTOR_DOWN_PRESS,
		VIS_UI_RECEPTOR_UP_PRESS, VIS_UI_RECEPTOR_RIGHT_PRESS
	};
	static const uint8_t confirm_frame[4][4] = {
		{ VIS_UI_RECEPTOR_LEFT_CONFIRM_0, VIS_UI_RECEPTOR_LEFT_CONFIRM_1,
		  VIS_UI_RECEPTOR_LEFT_CONFIRM_2, VIS_UI_RECEPTOR_LEFT_CONFIRM_3 },
		{ VIS_UI_RECEPTOR_DOWN_CONFIRM_0, VIS_UI_RECEPTOR_DOWN_CONFIRM_1,
		  VIS_UI_RECEPTOR_DOWN_CONFIRM_2, VIS_UI_RECEPTOR_DOWN_CONFIRM_3 },
		{ VIS_UI_RECEPTOR_UP_CONFIRM_0, VIS_UI_RECEPTOR_UP_CONFIRM_1,
		  VIS_UI_RECEPTOR_UP_CONFIRM_2, VIS_UI_RECEPTOR_UP_CONFIRM_3 },
		{ VIS_UI_RECEPTOR_RIGHT_CONFIRM_0, VIS_UI_RECEPTOR_RIGHT_CONFIRM_1,
		  VIS_UI_RECEPTOR_RIGHT_CONFIRM_2, VIS_UI_RECEPTOR_RIGHT_CONFIRM_3 }
	};
	for (unsigned lane = 0; lane < 4u; lane++) {
		int center_x = layout->first_center_x + (int)lane * layout->lane_step;
		uint16_t mask = (uint16_t[]){ PAD_LEFT, PAD_DOWN, PAD_UP, PAD_RIGHT }[lane];
		bool pressed = group_index == 1u && !(game_buttons & mask);
		uint32_t until = receiver_flash_until[group_index][lane];
		uint32_t confirm_duration = rate * 140u / 1000u;
		bool confirmed = samples < until;
		unsigned frame = pressed ? press_frame[lane] : idle_frame[lane];
		if (confirmed && confirm_duration) {
			uint32_t remaining = until - samples;
			uint32_t elapsed = remaining < confirm_duration ? confirm_duration - remaining : 0u;
			unsigned phase = (unsigned)((uint64_t)elapsed * 4u / confirm_duration);
			if (phase > 3u) phase = 3u;
			frame = confirm_frame[lane][phase];
		}
		draw_textured_frame(frame, center_x - layout->arrow_size / 2,
			layout->receptor_y - layout->arrow_size / 2,
			layout->arrow_size, layout->arrow_size);
	}

	for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++) {
		const BopeeboNote *note = &bopeebo_notes[i];
		bool dad_note = note->lane >= 4u;
		if ((group_index == 0u) != dad_note) continue;
		unsigned lane = note->lane & 3u;
		unsigned color_lane = lane;
		int center_x = layout->first_center_x + (int)lane * layout->lane_step;
		uint32_t state = game_note_state[i];
		bool holding = !dad_note && active_hold[lane] == (int16_t)i;
		if (state == 2u || (state == 1u && !holding) || (dad_note && state == 3u && samples >= note->tail))
			continue;

		if (note->tail > note->head && (state == 0u || holding || (dad_note && state == 3u))) {
			uint32_t visible_start = samples > note->head && (holding || (dad_note && state == 3u)) ?
				samples : note->head;
			int y0 = note_screen_y(visible_start, samples, layout, rate);
			int y1 = note_screen_y(note->tail, samples, layout, rate);
			draw_hold_body(center_x, y0, y1, layout->arrow_size, color_lane,
				layout->top_clip, bottom_clip);
		}

		if (state != 0u) continue;
		int y = note_screen_y(note->head, samples, layout, rate);
		int top = y - layout->arrow_size / 2;
		if (top + layout->arrow_size <= layout->top_clip || top >= bottom_clip) continue;
		draw_textured_frame(note_frame[lane], center_x - layout->arrow_size / 2, top,
			layout->arrow_size, layout->arrow_size);
	}
}

/* Select toggles a GPU-side comparison sheet over the live song. Keeping the
   art in the normal primitive path makes this useful for checking CLUT/tpage
   residency after menu -> song transitions, rather than only inspecting the
   generated atlas offline. */
static void draw_arrow_diagnostic_sheet(void)
{
	static const uint8_t note[4] = {
		VIS_UI_NOTE_LEFT, VIS_UI_NOTE_DOWN, VIS_UI_NOTE_UP, VIS_UI_NOTE_RIGHT
	};
	static const uint8_t idle[4] = {
		VIS_UI_RECEPTOR_LEFT_IDLE, VIS_UI_RECEPTOR_DOWN_IDLE,
		VIS_UI_RECEPTOR_UP_IDLE, VIS_UI_RECEPTOR_RIGHT_IDLE
	};
	static const uint8_t press[4] = {
		VIS_UI_RECEPTOR_LEFT_PRESS, VIS_UI_RECEPTOR_DOWN_PRESS,
		VIS_UI_RECEPTOR_UP_PRESS, VIS_UI_RECEPTOR_RIGHT_PRESS
	};
	static const uint8_t confirm[4] = {
		VIS_UI_RECEPTOR_LEFT_CONFIRM_0, VIS_UI_RECEPTOR_DOWN_CONFIRM_0,
		VIS_UI_RECEPTOR_UP_CONFIRM_0, VIS_UI_RECEPTOR_RIGHT_CONFIRM_0
	};
	static const uint8_t body[4] = {
		VIS_UI_HOLD_BODY_LEFT, VIS_UI_HOLD_BODY_DOWN,
		VIS_UI_HOLD_BODY_UP, VIS_UI_HOLD_BODY_RIGHT
	};
	static const uint8_t tail[4] = {
		VIS_UI_HOLD_TAIL_LEFT, VIS_UI_HOLD_TAIL_DOWN,
		VIS_UI_HOLD_TAIL_UP, VIS_UI_HOLD_TAIL_RIGHT
	};
	static const int column_x[4] = { 48, 120, 192, 264 };
	draw_rect(8, 82, 304, 136, 8, 8, 18);
	for (unsigned lane = 0; lane < 4u; lane++) {
		int x = column_x[lane] - 10;
		draw_textured_frame(note[lane], x, 91, 20, 20);
		draw_textured_frame(idle[lane], x, 116, 20, 20);
		draw_textured_frame(press[lane], x, 141, 20, 20);
		draw_textured_frame(confirm[lane], x, 166, 20, 20);
		draw_textured_frame(body[lane], column_x[lane] - 6, 193, 6, 16);
		draw_textured_frame(tail[lane], column_x[lane] + 1, 193, 12, 16);
	}
}

static void camera_target_for_focus(int focus, int *x, int *y)
{
	switch (focus) {
	case 1: /* mainStage.json: Dad origin and camera offset */
		*x = BOPEEBO_DAD_X + BOPEEBO_DAD_CAMERA_X;
		*y = BOPEEBO_DAD_Y - (int)(BOPEEBO_DAD_FRAME_H / 2u) + BOPEEBO_DAD_CAMERA_Y;
		break;
	case 0: /* mainStage.json: BF origin and camera offset */
		*x = BOPEEBO_BF_X + BOPEEBO_BF_CAMERA_X;
		*y = BOPEEBO_BF_Y - (int)(BOPEEBO_BF_FRAME_H / 2u) + BOPEEBO_BF_CAMERA_Y;
		break;
	case 2: /* Girlfriend */
		*x = BOPEEBO_GF_X + BOPEEBO_GF_CAMERA_X;
		*y = BOPEEBO_GF_Y - (int)(BOPEEBO_GF_FRAME_H / 2u) + BOPEEBO_GF_CAMERA_Y;
		break;
	default: /* Static chart focus */
		*x = SCREEN_W / 2;
		*y = SCREEN_H / 2;
		break;
	}
}

static uint32_t music_beat_q16(uint32_t samples)
{
	uint32_t rate = BOPEEBO_CHART_RATE;
	unsigned tempo_index = 0;
	while (tempo_index + 1u < BOPEEBO_TEMPO_CHANGE_COUNT &&
	       bopeebo_tempo_changes[tempo_index + 1u].sample <= samples) tempo_index++;
	const BopeeboTempoChange *tempo = &bopeebo_tempo_changes[tempo_index];
	uint64_t beat = tempo->beat_q16 +
		(uint64_t)(samples - tempo->sample) * tempo->bpm_centi * 65536u /
		((uint64_t)rate * 6000u);
	return beat > 0xffffffffu ? 0xffffffffu : (uint32_t)beat;
}

static void draw_scene(uint32_t samples)
{
	uint32_t rate = stream.config.sample_rate ?
		(uint32_t)stream.config.sample_rate : BOPEEBO_CHART_RATE;
	uint32_t beat_q16 = music_beat_q16(samples);
	uint32_t beat = beat_q16 >> 16;
	uint32_t beat_phase = beat_q16 & 0xffffu;
	const uint32_t pulse_window_q16 = 22937u; /* first 35% of each tempo-mapped beat */
	unsigned pulse_q8 = beat_phase < pulse_window_q16 ?
		(unsigned)(((uint64_t)(pulse_window_q16 - beat_phase) * 7u) / pulse_window_q16) : 0u;
	unsigned zoom_q8 = BOPEEBO_STAGE_CAMERA_ZOOM_Q8 + pulse_q8;
	/* Focus targets and stage transforms are generated from the official stage
	   data; smooth transitions follow chart events, never individual note hits. */
	unsigned event_index = 0;
	while (event_index + 1u < BOPEEBO_CAMERA_EVENT_COUNT &&
	       bopeebo_camera_events[event_index + 1u].sample <= samples) event_index++;
	int target_focus = BOPEEBO_CAMERA_EVENT_COUNT ? bopeebo_camera_events[event_index].focus : 1;
	int previous_focus = event_index ? bopeebo_camera_events[event_index - 1u].focus : target_focus;
	int from_x, from_y, to_x, to_y;
	camera_target_for_focus(previous_focus, &from_x, &from_y);
	camera_target_for_focus(target_focus, &to_x, &to_y);
	uint32_t transition = rate * CAMERA_FOCUS_TIME_MS / 1000u;
	uint32_t elapsed = samples >= bopeebo_camera_events[event_index].sample ?
		samples - bopeebo_camera_events[event_index].sample : transition;
	if (elapsed > transition) elapsed = transition;
	uint32_t t = transition ? (uint32_t)(((uint64_t)elapsed * 256u) / transition) : 256u;
	uint32_t smooth = t * t * (768u - 2u * t) / 65536u;
	int camera_x = from_x + (to_x - from_x) * (int)smooth / 256;
	int camera_y = from_y + (to_y - from_y) * (int)smooth / 256;
	camera_focus_display = (uint8_t)target_focus;
	camera_transitioning = event_index && elapsed < transition;

	/* One world transform covers official stage props and characters; the
	   extended stage composition safely overfills all camera crop edges. */
	draw_visual_frame(VIS_STAGE_SCENE_0, BOPEEBO_STAGE_SCENE_X, BOPEEBO_STAGE_SCENE_Y,
		camera_x, camera_y, zoom_q8, 256);
	draw_visual_frame(VIS_STAGE_SCENE_1, BOPEEBO_STAGE_SCENE_X + 256,
		BOPEEBO_STAGE_SCENE_Y, camera_x, camera_y, zoom_q8, 256);

	unsigned dad_frame;
	if (samples < dad_visual_until) {
		static const uint8_t sing_frames[4][2] = {
			{ VIS_DAD_LEFT_0, VIS_DAD_LEFT_1 }, { VIS_DAD_DOWN_0, VIS_DAD_DOWN_1 },
			{ VIS_DAD_UP_0, VIS_DAD_UP_1 }, { VIS_DAD_RIGHT_0, VIS_DAD_RIGHT_1 }
		};
		dad_frame = sing_frames[dad_visual_lane & 3u][(beat_phase >> 15) & 1u];
	} else {
		unsigned idle_pose = (unsigned)((uint64_t)beat_phase * 6u >> 16);
		if (idle_pose > 5u) idle_pose = 5u;
		dad_frame = VIS_DAD_IDLE_0 + idle_pose;
	}
	/* GF's pinned character config alternates two 15-frame dances each beat.
	   Nine source poses per side are sampled across that beat, including the
	   original speaker rig's embedded pulse. */
	unsigned gf_side = (beat & 1u) ? 0u : BOPEEBO_GF_DANCE_FRAMES_PER_BEAT;
	unsigned gf_pose = (unsigned)((uint64_t)beat_phase * BOPEEBO_GF_DANCE_FRAMES_PER_BEAT >> 16);
	if (gf_pose >= BOPEEBO_GF_DANCE_FRAMES_PER_BEAT)
		gf_pose = BOPEEBO_GF_DANCE_FRAMES_PER_BEAT - 1u;
	draw_visual_frame(VIS_GF_DANCE_0 + gf_side + gf_pose,
		BOPEEBO_GF_X - (int)(BOPEEBO_GF_FRAME_W / 2u),
		BOPEEBO_GF_Y - (int)BOPEEBO_GF_FRAME_H,
		camera_x, camera_y, zoom_q8, 256);
	/* mainStage z-indices: GF=100, Dad=200, BF=300; stage props are behind. */
	draw_visual_frame(dad_frame,
		BOPEEBO_DAD_X - (int)(BOPEEBO_DAD_FRAME_W / 2u),
		BOPEEBO_DAD_Y - (int)BOPEEBO_DAD_FRAME_H,
		camera_x, camera_y, zoom_q8, 256);

	unsigned bf_frame;
	if (bf_visual_state == 2u) {
		uint32_t elapsed = samples >= bf_visual_start ? samples - bf_visual_start : 0u;
		uint32_t miss_duration = BOPEEBO_CHART_RATE * 350u / 1000u;
		/* Restart on every existing miss event; use the two official miss poses
		   on a local timeline so same-lane misses inside one beat are visible. */
		unsigned miss_pose = elapsed >= miss_duration / 3u ? 1u : 0u;
		bf_frame = VIS_BF_MISS_LEFT_0 + (unsigned)bf_visual_lane * 2u + miss_pose;
	}
	else if (bf_visual_state == 1u)
		bf_frame = VIS_BF_LEFT_0 + (unsigned)bf_visual_lane * 2u + ((beat_phase >> 15) & 1u);
	else
		{
			unsigned idle_step = (unsigned)((uint64_t)beat_phase * BOPEEBO_BF_IDLE_SEQUENCE_LENGTH >> 16);
			if (idle_step >= BOPEEBO_BF_IDLE_SEQUENCE_LENGTH)
				idle_step = BOPEEBO_BF_IDLE_SEQUENCE_LENGTH - 1u;
			bf_frame = VIS_BF_IDLE_0 + bopeebo_bf_idle_sequence[idle_step];
		}
	draw_visual_frame(bf_frame,
		BOPEEBO_BF_X - (int)(BOPEEBO_BF_FRAME_W / 2u),
		BOPEEBO_BF_Y - (int)BOPEEBO_BF_FRAME_H,
		camera_x, camera_y, zoom_q8, 256);
}

static void draw_gameplay(uint32_t samples)
{
	game_prim_count = 0;
	visual_prim_count = 0;
	visual_prim_limit = VISUAL_WORLD_PRIM_LIMIT;
	visual_prim_rejected = 0;
	judgement_drawn = false;
	draw_scene(samples);
	draw_note_group(samples, 0);
	draw_note_group(samples, 1);
	if (diagnostics_visible)
		draw_arrow_diagnostic_sheet();
	/* Reserve primitives for the final screen-space feedback layer. */
	gameplay_visual_prim_count = visual_prim_count;
	visual_prim_limit = VISUAL_MAX_PRIMS;

	/* HUD and transient judgment sprites are screen-space, independent of camera.
	   The stage remains visible outside the narrow bar and score backplate. */
	/* FNF-style force balance: red opponent left, green BF right. This is
	   display-only; health_q8 and game-over logic remain untouched. */
	uint16_t hud_health_q8 = health_q8;
#if GAME_HEALTH_BAR_TEST_DEFAULT
	/* Deterministic visual-only diagnostic: five fixed values, then a triangle
	   sweep. It never writes back to health_q8 or affects gameplay rules. */
	uint32_t seconds = stream.config.sample_rate ? samples / (uint32_t)stream.config.sample_rate : 0;
	if (seconds < 50u)
		hud_health_q8 = (uint16_t)((seconds / 10u) * 128u);
	else {
		uint32_t phase = (seconds - 50u) % 40u;
		hud_health_q8 = (uint16_t)(phase <= 20u ? (phase * 512u) / 20u : ((40u - phase) * 512u) / 20u);
	}
#endif
	unsigned player_width = ((unsigned)hud_health_q8 * 124u + 256u) / 512u;
	if (player_width > 124u) player_width = 124u;
	unsigned opponent_width = 124u - player_width;
	const int bar_left = 98;
	const int bar_right = 222;
	draw_rect(94, 19, 132, 16, 18, 18, 24);
	if (opponent_width) draw_rect(bar_left, 23, (int)opponent_width, 8, 218, 63, 76);
	if (player_width) draw_rect(bar_right - (int)player_width, 23, (int)player_width, 8, 76, 211, 121);
	int boundary = bar_right - (int)player_width;
	hud_health_boundary_x = boundary;
	hud_actual_health_percent = ((unsigned)health_q8 * 100u + 256u) / 512u;
	hud_display_health_percent = ((unsigned)hud_health_q8 * 100u + 256u) / 512u;
	/* The original engine anchors both icons to its bar frontier, then offsets
	   by POSITION_OFFSET=26 on a 150 px icon. Scale that ratio to 24 px; clamp
	   only the portraits to the 95% CRT title-safe rectangle, never the bar. */
	const int icon_w = 24;
	const int icon_offset = (icon_w * 26 + 75) / 150;
	int dad_x = boundary - (icon_w - icon_offset);
	int bf_x = boundary - icon_offset;
	if (dad_x < 16) dad_x = 16;
	if (dad_x > 304 - icon_w) dad_x = 304 - icon_w;
	if (bf_x < 16) bf_x = 16;
	if (bf_x > 304 - icon_w) bf_x = 304 - icon_w;
	hud_dad_icon_x = dad_x;
	hud_bf_icon_x = bf_x;
	/* Transparent official portraits sit above fills/frame and share one anchor. */
	draw_textured_frame(VIS_UI_ICON_DAD, dad_x, 13, icon_w, icon_w);
	/* The legacy two-frame BF sheet is idle/default + losing, not win + loss.
	   Match HealthIcon's original 20% loss threshold; its 80% winning state has
	   no distinct source frame in this sheet, so it uses the idle/default art. */
	draw_textured_frame(hud_health_q8 <= 102u ? VIS_UI_ICON_BF_LOSE : VIS_UI_ICON_BF_WIN,
		bf_x, 13, icon_w, icon_w);
	if (diagnostics_visible) {
		/* Approximate title/action-safe frames for 4:3 CRT setup checks. */
		draw_rect(8, 6, 304, 1, 48, 96, 112);
		draw_rect(8, 233, 304, 1, 48, 96, 112);
		draw_rect(8, 6, 1, 228, 48, 96, 112);
		draw_rect(311, 6, 1, 228, 48, 96, 112);
		draw_rect(16, 12, 288, 1, 96, 160, 128);
		draw_rect(16, 227, 288, 1, 96, 160, 128);
		draw_rect(16, 12, 1, 216, 96, 160, 128);
		draw_rect(303, 12, 1, 216, 96, 160, 128);
	}
}

/* This is the final screen-space pass. The normal frontend draws score and font
   HUD after draw_gameplay(), so submit judgements only after those layers. */
static void draw_judgement_popup(uint32_t samples, uint32_t rate)
{
	judgement_drawn = false;
	if (samples >= judgement_until || !last_judgement || last_judgement > 4u)
		return;
	static const uint8_t popup_frame[5] = {
		0u, VIS_UI_JUDGEMENT_SICK, VIS_UI_JUDGEMENT_GOOD,
		VIS_UI_JUDGEMENT_BAD, VIS_UI_JUDGEMENT_SHIT
	};
	const BopeeboVisualFrame *popup = &bopeebo_visual_frames[popup_frame[last_judgement]];
	/* Recreate PopUpStuff's rise, gravity and fade as a deterministic audio-clock tween. */
	const uint32_t lifetime = rate * 650u / 1000u;
	const uint32_t elapsed = lifetime - (judgement_until - samples);
	const uint32_t elapsed_ms = rate ? (uint32_t)(((uint64_t)elapsed * 1000u) / rate) : 0u;
	const uint32_t scale_permille = elapsed_ms >= 100u ? 1000u : 900u + elapsed_ms;
	int popup_w = ((int)popup->w * 164 * (int)scale_permille + 50000) / 100000;
	int popup_h = ((int)popup->h * 164 * (int)scale_permille + 50000) / 100000;
	int popup_x = (SCREEN_W - popup_w) / 2;
	int y_delta = -(int)(40u * elapsed_ms / 1000u) + (int)(70u * elapsed_ms * elapsed_ms / 1000000u);
	int popup_y = 57 + y_delta;
	uint8_t tint = 128u;
	if (elapsed_ms > 450u) {
		uint32_t fade_ms = elapsed_ms >= 650u ? 200u : elapsed_ms - 450u;
		tint = (uint8_t)(128u - (fade_ms * 80u) / 200u);
	}
	judgement_drawn = draw_textured_frame_tinted(popup_frame[last_judgement],
		popup_x, popup_y, popup_w, popup_h, tint, tint, tint);
}

static void draw_score_display(void)
{
	/* The VCR atlas quads are present in the atlas but are not visible in the
	   current GPU output. Use the SDK bitmap-font path that is already visible
	   in diagnostics, keeping the score at the right end of the life-bar row. */
	score_text_flushed = false;
	if (score_font_id < 0) return;
	FntPrint(score_font_id, "SCORE %ld", (long)score);
	FntFlush(score_font_id);
	score_text_flushed = true;
}

static void draw_combo_popup(uint32_t samples, uint32_t rate)
{
	if (combo_popup_value < 0 || samples >= combo_popup_until)
		return;
	static const uint8_t combo_frames[10] = {
		VIS_UI_COMBO_NUM_0, VIS_UI_COMBO_NUM_1, VIS_UI_COMBO_NUM_2,
		VIS_UI_COMBO_NUM_3, VIS_UI_COMBO_NUM_4, VIS_UI_COMBO_NUM_5,
		VIS_UI_COMBO_NUM_6, VIS_UI_COMBO_NUM_7, VIS_UI_COMBO_NUM_8,
		VIS_UI_COMBO_NUM_9
	};
	uint32_t remaining = (uint32_t)combo_popup_value;
	uint8_t digits[6];
	unsigned count = 0;
	do {
		digits[count++] = (uint8_t)(remaining % 10u);
		remaining /= 10u;
	} while (remaining && count < 6u);
	while (count < 3u) digits[count++] = 0;
	uint32_t elapsed_ms = rate ? (uint32_t)(((uint64_t)(samples - combo_popup_start_samples) * 1000u) / rate) : 0u;
	uint32_t remaining_ms = rate ? (uint32_t)(((uint64_t)(combo_popup_until - samples) * 1000u) / rate) : 0u;
	/* Match the official float-up/gravity tween; fade across the final 200 ms. */
	int y_delta = -(int)(36u * elapsed_ms / 1000u) + (int)(34u * elapsed_ms * elapsed_ms / 1000000u);
	uint32_t scale_permille = elapsed_ms >= 100u ? 1000u : 900u + elapsed_ms;
	uint8_t tint = remaining_ms >= 200u ? 128u : (uint8_t)(48u + remaining_ms * 80u / 200u);
	for (unsigned i = 0; i < count; i++) {
		unsigned frame = combo_frames[digits[i]];
		const BopeeboVisualFrame *digit = &bopeebo_visual_frames[frame];
		int width = ((int)digit->w * (int)scale_permille + 500) / 1000;
		int height = ((int)digit->h * (int)scale_permille + 500) / 1000;
		int center_x = 165 - (int)i * 9 + (int)digit->w / 2;
		int x = center_x - width / 2;
		draw_textured_frame_tinted(frame, x, 99 + y_delta, width, height, tint, tint, tint);
	}
}

static void draw_menu_screen(void)
{
	game_prim_count = 0;
	visual_prim_count = 0;
	visual_prim_limit = VISUAL_MAX_PRIMS;
	if (game_screen == SCREEN_PAUSE) {
		/* Keep the paused stage visible under a compact, screen-space overlay. */
		draw_rect(55, 158, 210, 74, 14, 12, 28);
		draw_rect(59, 162, 202, 66, 66, 51, 111);
		FntPrint(menu_font_id, "PAUSED\nCROSS RESUME\nCIRCLE FREEPLAY");
		FntFlush(menu_font_id);
		return;
	}

	/* Use separate title/main/freeplay compositions. All menu art is official
	   pinned material; the only selectable destination remains Freeplay. */
	if (game_screen == SCREEN_TITLE) {
		draw_textured_frame(VIS_MENU_LOGO, 42, 8, 176, 132);
	} else if (game_screen == SCREEN_MAIN_MENU) {
		draw_textured_frame(VIS_MENU_LOGO, 18, 8, 142, 106);
		draw_textured_frame(VIS_MENU_FREEPLAY_BUTTON, 18, 128, 150, 42);
	} else {
		draw_textured_frame(VIS_MENU_FREEPLAY_BG, 132, 18, 176, 99);
	}
	unsigned beat = (menu_ticks / 36u) & 1u;
	unsigned pose = (menu_ticks / 4u) % BOPEEBO_GF_DANCE_FRAMES_PER_BEAT;
	if (game_screen != SCREEN_FREEPLAY)
		draw_textured_frame(VIS_GF_DANCE_0 + beat * BOPEEBO_GF_DANCE_FRAMES_PER_BEAT + pose,
			game_screen == SCREEN_TITLE ? 210 : 206,
			game_screen == SCREEN_TITLE ? 142 : 126,
			BOPEEBO_GF_FRAME_W, BOPEEBO_GF_FRAME_H);
	if (game_screen == SCREEN_TITLE)
		FntPrint(menu_font_id, "PRESS START TO CONTINUE");
	else if (game_screen == SCREEN_MAIN_MENU)
		FntPrint(menu_font_id, "CROSS FREEPLAY");
	else
		FntPrint(menu_font_id, "FREEPLAY\n> %s - %s\nCROSS PLAY  CIRCLE BACK",
			freeplay_catalog[0].song, freeplay_catalog[0].difficulty);
	FntFlush(menu_font_id);
}

static void reset_game_state(void)
{
	memset(game_note_state, 0, sizeof(game_note_state));
	memset(receiver_flash_until, 0, sizeof(receiver_flash_until));
	for (unsigned lane = 0; lane < 4; lane++) active_hold[lane] = -1;
	score = combo = misses = hits = 0;
	hold_drops = 0;
	health_q8 = 256;
	bf_miss_silenced = false;
	bf_visual_state = 0;
	bf_visual_lane = 0;
	bf_visual_until = 0;
	dad_visual_lane = 0;
	dad_visual_start = 0;
	dad_visual_until = 0;
	last_judgement = 0;
	judgement_until = 0;
	combo_popup_value = -1;
	combo_popup_start_samples = 0;
	combo_popup_until = 0;
	last_judgement_delta_ms = 0;
#if GAME_JUDGEMENT_TEST_DEFAULT
	judgement_test_next = 0;
	judgement_test_hits = 0;
#endif
	dad_lanes_visible = GAME_DAD_LANES_DEFAULT != 0;
	diagnostics_visible = GAME_DIAGNOSTICS_DEFAULT != 0 || GAME_ARROW_DIAGNOSTIC_DEFAULT != 0;
}

#if GAME_SCENE_DEMO_DEFAULT
/* Camera QA drives poses from chart time but intentionally skips scoring,
   health, input judgments, misses and all audio controls/game-over logic. */
static void update_scene_demo_visuals(uint32_t samples)
{
	dad_visual_until = 0;
	bf_visual_until = 0;
	for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++) {
		const BopeeboNote *note = &bopeebo_notes[i];
		if (note->head > samples) break;
		uint32_t until = note->tail > note->head ? note->tail :
			note->head + BOPEEBO_CHART_RATE * 280u / 1000u;
		if (samples > until) continue;
		if (note->lane >= 4u) {
			dad_visual_lane = (uint8_t)(note->lane - 4u);
			dad_visual_start = note->head;
			dad_visual_until = until;
		} else {
			bf_visual_lane = (uint8_t)note->lane;
			bf_visual_state = 1u;
			bf_visual_until = until;
		}
	}
	if (!bf_visual_until) bf_visual_state = 0;
}
#endif

static bool restart_bopeebo(void)
{
	if (Stream_IsActive(&stream)) Stream_Stop();
	abort_cd_read();
	CdReadCallback(0);
	if (stream_initialized) {
		Stream_Destroy(&stream);
		stream_initialized = false;
	}
	memset(&stream, 0, sizeof(stream));
	memset(&read_ctx, 0, sizeof(read_ctx));
	underruns = read_errors = 0;
	read_ctx.last_cdsync_return = 0;
	for (unsigned i = 0; i < SFX_VOICE_COUNT; i++) {
		sfx_voice_active[i] = false;
		SpuSetKey(0, 1u << (SFX_FIRST_VOICE + i));
	}
	reset_game_state();
	song_finished = false;
	if (CdControlB(CdlPause, 0, 0) != 1 || !start_stream_from_disc()) return false;
	return true;
}

static bool upload_menu_sfx(void)
{
	if (MENU_SFX_SPURAM_ADDR + MENU_SFX_BANK_SIZE > SPU_RAM_SIZE)
		return false;
	SpuSetTransferMode(SPU_TRANSFER_BY_DMA);
	SpuSetTransferStartAddr(MENU_SFX_SPURAM_ADDR);
	size_t written = SpuWrite((const uint32_t *)menu_sfx_bank, MENU_SFX_BANK_SIZE);
	return written == MENU_SFX_BANK_SIZE &&
		SpuIsTransferCompleted(SPU_TRANSFER_WAIT);
}

static void play_menu_sfx(unsigned sound)
{
	static const uint32_t offsets[MENU_SFX_VOICE_COUNT] = {
		MENU_SFX_SCROLLMENU_OFFSET, MENU_SFX_CONFIRMMENU_OFFSET,
		MENU_SFX_CANCELMENU_OFFSET
	};
	if (sound >= MENU_SFX_VOICE_COUNT) return;
	unsigned voice = MENU_SFX_FIRST_VOICE + sound;
	uint32_t key = 1u << voice;
	SpuSetKey(0, key);
	SPU_CH_ADDR(voice) = getSPUAddr(MENU_SFX_SPURAM_ADDR + offsets[sound]);
	SPU_CH_FREQ(voice) = getSPUSampleRate(MENU_SFX_RATE);
	SPU_CH_ADSR1(voice) = 0x00ff;
	SPU_CH_ADSR2(voice) = 0x0000;
	/* Three navigation cues together stay below the menu music's mix headroom. */
	SPU_CH_VOL_L(voice) = 0x0600;
	SPU_CH_VOL_R(voice) = 0x0600;
	SpuSetKey(1, key);
}

static void release_song_resources(void)
{
	abort_cd_read();
	CdReadCallback(0);
	if (Stream_IsActive(&stream)) Stream_Stop();
	if (stream_initialized) {
		Stream_Destroy(&stream);
		stream_initialized = false;
	}
	memset(&stream, 0, sizeof(stream));
	memset(&read_ctx, 0, sizeof(read_ctx));
	(void)CdControlB(CdlPause, 0, 0);
}

static bool enter_bopeebo(void)
{
	release_song_resources();
	release_menu_visuals();
	reset_game_state();
	song_finished = false;
	if (!start_stream_from_disc()) return false;
	game_screen = SCREEN_GAMEPLAY;
	return true;
}

static void return_to_freeplay(void)
{
	release_song_resources();
	load_menu_visuals();
	song_finished = true;
	game_screen = SCREEN_FREEPLAY;
	if (CdControlB(CdlPause, 0, 0) != 1 ||
		!start_stream_file("\\MENU.VAG", MENU_MUSIC_CHANNELS, true, true))
		show_error(failure_code ? failure_code : FAIL_CD_READ);
}

static void run_playable_frontend(void)
{
	reset_game_state();
	game_screen = SCREEN_TITLE;
	menu_ticks = 0;
	if (!upload_menu_sfx() ||
		!start_stream_file("\\MENU.VAG", MENU_MUSIC_CHANNELS, true, true))
		show_error(failure_code ? failure_code : FAIL_CD_READ);
#if GAME_ARROW_DIAGNOSTIC_DEFAULT
	/* QA-only disc mode: enter the real Bopeebo stream without requiring input,
	   so the official arrow atlas can be inspected in its gameplay path. */
	if (!enter_bopeebo()) show_error(failure_code ? failure_code : FAIL_CD_READ);
#elif GAME_JUDGEMENT_TEST_DEFAULT
	judgement_test_font_id = FntOpen(16, 208, 288, 28, 0, 80);
	if (!enter_bopeebo()) show_error(failure_code ? failure_code : FAIL_CD_READ);
#endif
	for (;;) {
		bool pad_connected = poll_bopeebo4_controls();
		uint32_t samples = 0;
		unsigned rate = BOPEEBO_CHART_RATE;
		if (game_screen != SCREEN_GAMEPLAY && game_screen != SCREEN_PAUSE &&
			stream_initialized) {
			(void)feed_stream();
			if (read_ctx.read_error || underruns)
				show_error(read_ctx.read_error ? FAIL_CD_READ : FAIL_UNDERRUN);
			rate = (unsigned)stream.config.sample_rate;
			samples = Stream_GetSamplesPlayed(&stream);
			menu_ticks = rate ? (uint32_t)(((uint64_t)samples * 60u) / rate) : menu_ticks;
		}
		if (game_screen == SCREEN_GAMEPLAY) {
			(void)feed_stream();
			if (read_ctx.read_error || underruns)
				show_error(read_ctx.read_error ? FAIL_CD_READ : FAIL_UNDERRUN);
			samples = Stream_GetSamplesPlayed(&stream);
			rate = (unsigned)stream.config.sample_rate;
			uint32_t song_end = TEST_TOTAL_SAMPLES +
				(uint32_t)(2u * (stream.config.interleave / 16u * 28u));
			if (!song_finished && samples >= song_end) {
				Stream_Stop();
				song_finished = true;
			}
			if (samples > TEST_TOTAL_SAMPLES) samples = TEST_TOTAL_SAMPLES;
			if (game_pressed & PAD_START) {
				abort_cd_read();
				Stream_Stop();
				game_screen = SCREEN_PAUSE;
			} else if (!song_finished) {
#if GAME_SCENE_DEMO_DEFAULT
				update_scene_demo_visuals(samples);
#else
				#if GAME_JUDGEMENT_TEST_DEFAULT
				uint32_t hits_before_test = hits;
				inject_judgement_test_hit(samples, rate);
				#endif
				game_update(samples);
				#if GAME_JUDGEMENT_TEST_DEFAULT
				if (hits > hits_before_test) judgement_test_hits++;
				#endif
				if (!health_q8 && Stream_IsActive(&stream)) {
					Stream_Stop();
					song_finished = true;
				}
#endif
			}
			if (song_finished) return_to_freeplay();
		} else if (game_screen == SCREEN_PAUSE) {
			if (game_pressed & PAD_CROSS) {
				play_menu_sfx(1u);
				if (!Stream_Start(&stream, true)) show_error(FAIL_STREAM_START);
				game_screen = SCREEN_GAMEPLAY;
			} else if (game_pressed & PAD_CIRCLE) {
				play_menu_sfx(2u);
				return_to_freeplay();
			}
		} else if (game_screen == SCREEN_TITLE) {
			if (game_pressed & PAD_START) {
				play_menu_sfx(1u);
				game_screen = SCREEN_MAIN_MENU;
			}
		} else if (game_screen == SCREEN_MAIN_MENU) {
			if (game_pressed & PAD_CROSS) {
				play_menu_sfx(1u);
				game_screen = SCREEN_FREEPLAY;
			}
		} else if (game_screen == SCREEN_FREEPLAY) {
			if (game_pressed & PAD_CIRCLE) {
				play_menu_sfx(2u);
				game_screen = SCREEN_MAIN_MENU;
			}
			else if (game_pressed & PAD_CROSS) {
				play_menu_sfx(1u);
				if (!enter_bopeebo()) show_error(failure_code ? failure_code : FAIL_CD_READ);
				samples = 0;
			}
		}

		if (game_screen == SCREEN_GAMEPLAY || game_screen == SCREEN_PAUSE) {
			uint32_t milliseconds = rate ? (uint32_t)(((uint64_t)samples * 1000u) / rate) : 0;
			draw_gameplay(samples);
			if (game_screen == SCREEN_PAUSE) {
				draw_menu_screen();
			} else {
				draw_score_display();
				draw_judgement_popup(samples, rate);
				draw_combo_popup(samples, rate);
				if (diagnostics_visible) {
					FntPrint(diagnostics_font_id, "AUDIO %02u:%02u.%03u  PAD %s\n",
						milliseconds / 60000u, (milliseconds / 1000u) % 60u,
						milliseconds % 1000u, pad_connected ? "ON" : "OFF");
					FntPrint(diagnostics_font_id, "BUF %u/%u CD %u U %u\n",
						(unsigned)stream.buffer.length, (unsigned)stream.config.buffer_size,
						(unsigned)read_errors, (unsigned)underruns);
					FntPrint(diagnostics_font_id, "VIS %u/%u J %u LEFT %lu MISS %u\n",
						visual_prim_count, VISUAL_MAX_PRIMS, (unsigned)last_judgement,
						(unsigned long)(samples < judgement_until ? judgement_until - samples : 0u),
						misses + hold_drops);
					FntPrint(diagnostics_font_id, "WORLD %u HIGH %u DROP %u\n",
						gameplay_visual_prim_count, visual_prim_high_water, visual_prim_rejected);
					FntPrint(diagnostics_font_id, "SCORE FONT %u J DRAW %u\n",
						(unsigned)score_text_flushed, (unsigned)judgement_drawn);
					FntPrint(diagnostics_font_id, "HITS %u EDGE %04x J %u DMS %lu\n",
						(unsigned)hits, (unsigned)last_game_pressed, (unsigned)last_judgement,
						(unsigned long)last_judgement_delta_ms);
					FntPrint(diagnostics_font_id, "TRI DAD  C VOICE  L1/R1 PAN  J SFX  START PAUSE\n");
					FntFlush(diagnostics_font_id);
				}
#if GAME_JUDGEMENT_TEST_DEFAULT
				static const char *const judgement_names[] = { "NONE", "SICK", "GOOD", "BAD", "SHIT" };
				FntPrint(judgement_test_font_id, "AUTO HITS %u/4  %s  DRAW %u\nT %u.%03u  DELTA %lu MS LEFT %lu",
					(unsigned)judgement_test_hits,
					last_judgement <= 4u ? judgement_names[last_judgement] : "INVALID",
					(unsigned)judgement_drawn, milliseconds / 1000u, milliseconds % 1000u,
					(unsigned long)last_judgement_delta_ms,
					(unsigned long)(samples < judgement_until ?
						((uint64_t)(judgement_until - samples) * 1000u) / rate : 0u));
				FntFlush(judgement_test_font_id);
#endif
			}
		} else {
			draw_menu_screen();
		}
		display_frame();
		menu_ticks++;
	}
}

#if GAME_JUDGEMENT_VISUAL_TEST_DEFAULT
/* No-audio visual isolation disc. Uses the same atlas loader, CLUT setup,
   primitive helper and gameplay renderer; it never opens or overlays the game. */
static void run_judgement_visual_test(void)
{
	static const char *const names[4] = { "SICK", "GOOD", "BAD", "SHIT" };
	static const uint8_t note_indices[4] = { 3u, 9u, 16u, 22u };
	static const uint8_t offsets_ms[4] = { 0u, 60u, 110u, 150u };
	static const uint16_t lane_masks[4] = { PAD_LEFT, PAD_DOWN, PAD_UP, PAD_RIGHT };
	const uint32_t rate = BOPEEBO_CHART_RATE;
	uint32_t frame = 0;
	uint32_t test_sample = 0;
	unsigned active_phase = 4u;
	game_screen = SCREEN_GAMEPLAY;
	judgement_visual_font_id = FntOpen(16, 208, 288, 28, 0, 80);
	for (;;) {
		unsigned phase = (frame / 150u) & 3u;
		unsigned phase_frame = frame % 150u;
		if (phase != active_phase) {
			active_phase = phase;
			reset_game_state();
			for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++)
				if (bopeebo_notes[i].lane < 4u && i != note_indices[phase])
					game_note_state[i] = 1u;
			const BopeeboNote *note = &bopeebo_notes[note_indices[phase]];
			test_sample = note->head + (uint32_t)(((uint64_t)rate * offsets_ms[phase]) / 1000u);
			game_buttons = 0xffffu;
			game_pressed = lane_masks[note->lane];
			game_update(test_sample);
			if (hits) judgement_test_hits++;
		}
		/* Quarter-speed synthetic sample clock keeps the real 650 ms audio-time
		   lifetime intact while giving the visual QA result a capture window. */
		uint32_t samples = test_sample + (uint32_t)(((uint64_t)phase_frame * rate) / 240u);
		draw_gameplay(samples);
		draw_judgement_popup(samples, rate);
		FntPrint(judgement_visual_font_id, "GAME UPDATE QA x0.25 %u/4  %s  DRAW %u\nDELTA %lu MS",
			phase + 1u, names[phase], (unsigned)judgement_drawn,
			(unsigned long)last_judgement_delta_ms);
		FntFlush(judgement_visual_font_id);
		display_frame();
		frame++;
	}
}
#endif
#endif

static void reset_spu_channels(void)
{
	SpuSetKey(0, 0x00ffffff);
	for (int channel = 0; channel < 24; channel++) {
		SPU_CH_ADDR(channel) = getSPUAddr(DUMMY_BLOCK_ADDR);
		SPU_CH_FREQ(channel) = 0x1000;
	}
	SpuSetKey(1, 0x00ffffff);
}

static bool wait_for_cd_read(unsigned max_frames)
{
	for (unsigned frame = 0; frame < max_frames; frame++) {
		int pending = CdReadSync(1, 0);
		read_ctx.last_cdsync_return = pending;
		if (pending < 0) {
			read_ctx.read_pending = 0;
			set_read_error(pending == -2 ? READ_ERROR_SYNC_ABORT : READ_ERROR_SYNC_TIMEOUT);
			CdReadCallback(0);
			return false;
		}
		if (pending == 0) {
			uint8_t result[4] = {0};
			read_ctx.last_cdsync_return = CdReadSync(0, result);
			save_sync_result(result);
			read_ctx.read_pending = 0;
			return !read_ctx.read_error;
		}
		VSync(0);
	}
	set_read_error(READ_ERROR_WAIT_TIMEOUT);
	abort_cd_read();
	return false;
}

static void abort_cd_read(void)
{
	if (!read_ctx.read_pending)
		return;
	CdReadBreak();
	for (unsigned frame = 0; frame < 120u; frame++) {
		int pending = CdReadSync(1, 0);
		read_ctx.last_cdsync_return = pending;
		if (pending == -2 || pending == 0) {
			read_ctx.read_pending = 0;
			CdReadCallback(0);
			return;
		}
		if (pending == -1) {
			set_read_error(READ_ERROR_SYNC_TIMEOUT);
			read_ctx.read_pending = 0;
			CdReadCallback(0);
			return;
		}
		VSync(0);
	}
}

static bool feed_stream(void)
{
	if (read_ctx.read_error)
		return false;
	if (read_ctx.read_pending)
		return true;
	if (Stream_GetRefillLength(&stream) < REFILL_THRESHOLD)
		return false;

	uint8_t *ptr;
	size_t sectors = Stream_GetFeedPtr(&stream, &ptr) / CD_SECTOR_SIZE;
	int next_sector = read_ctx.next_sector;
	int max_length = read_ctx.stream_length - next_sector;
	if (max_length <= 0) {
		if (!read_ctx.loop)
		return false;
		next_sector = 0;
		max_length = read_ctx.stream_length;
	}
	if (sectors > (size_t)max_length)
		sectors = (size_t)max_length;
	if (sectors == 0)
		return false;

	CdlLOC position;
	CdIntToPos(read_ctx.start_lba + next_sector, &position);
	if (CdControl(CdlSetloc, &position, 0) != 1) {
		set_read_error(READ_ERROR_SETLOC);
		return false;
	}
	read_ctx.refill_length = sectors;
	read_ctx.last_read_sectors = (unsigned)sectors;
	read_ctx.next_sector = next_sector + (int)sectors;
	read_ctx.read_pending = 1;
	read_ctx.total_requested_sectors += (unsigned)sectors;
	CdReadCallback(cd_read_handler);
	read_ctx.last_cdread_return = CdRead((int)sectors, (uint32_t *)ptr, CdlModeSpeed);
	if (read_ctx.last_cdread_return <= 0) {
		read_ctx.read_pending = 0;
		set_read_error(READ_ERROR_START);
		CdReadCallback(0);
		return false;
	}
	return true;
}

static bool valid_header(const VAG_Header *header, unsigned expected_channels,
	unsigned *channels_out,
	unsigned *interleave_out, unsigned *sample_rate_out, unsigned *chunks_out,
	int file_size)
{
	if (memcmp(&header->magic, "VAGi", 4) != 0)
		return false;
	unsigned interleave = header->interleave;
	unsigned channels = header->channels ? header->channels : 2u;
	unsigned bytes_per_channel = SWAP_ENDIAN(header->size);
	unsigned sample_rate = SWAP_ENDIAN(header->sample_rate);
	if (header->version != 0x20000000u || channels != expected_channels ||
		interleave < 2048u || interleave > 8192u ||
		(interleave % CD_SECTOR_SIZE) != 0 || (interleave % 16u) != 0 ||
		bytes_per_channel == 0 || (bytes_per_channel % 16u) != 0 ||
		sample_rate < 4000u || sample_rate > 44100u)
		return false;
	unsigned chunks = (bytes_per_channel + interleave - 1u) / interleave;
	uint64_t file_bytes = 2048u + (uint64_t)channels * chunks * interleave;
	uint64_t spu_bytes = (uint64_t)interleave * channels * 2u;
	if (!chunks || file_size < 2048 || file_bytes > (uint64_t)file_size ||
		file_bytes > 0x7fffffffu ||
		RAM_BUFFER_SIZE < REFILL_THRESHOLD + channels * interleave ||
		STREAM_BUFFER_ADDR + spu_bytes > SPU_RAM_SIZE)
		return false;
	*channels_out = channels;
	*interleave_out = interleave;
	*sample_rate_out = sample_rate;
	*chunks_out = chunks;
	return true;
}

static bool start_stream_file(const char *path, unsigned expected_channels,
	bool loop, bool menu_music)
{
	CdlFILE file;
	if (!CdSearchFile(&file, path)) {
		failure_code = FAIL_NOT_FOUND;
		return false;
	}
	memset(&read_ctx, 0, sizeof(read_ctx));
	uint32_t header_sector[CD_SECTOR_SIZE / sizeof(uint32_t)];
	if (CdControl(CdlSetloc, &file.pos, 0) != 1) {
		failure_code = FAIL_CD_COMMAND;
		return false;
	}
	CdReadCallback(0);
	read_ctx.read_pending = 1;
	read_ctx.read_error = 0;
	read_ctx.last_read_sectors = 0;
	read_ctx.last_cdread_return = CdRead(1, header_sector, CdlModeSpeed);
	if (read_ctx.last_cdread_return <= 0) {
		read_ctx.read_pending = 0;
		set_read_error(READ_ERROR_START);
		failure_code = FAIL_HEADER_READ;
		return false;
	}
	if (!wait_for_cd_read(MAX_WAIT_FRAMES)) {
		failure_code = FAIL_HEADER_READ;
		return false;
	}

	unsigned channels, interleave, sample_rate, chunks;
	const VAG_Header *header = (const VAG_Header *)header_sector;
	if (!valid_header(header, expected_channels, &channels, &interleave, &sample_rate, &chunks,
		file.size)) {
		failure_code = FAIL_HEADER_FORMAT;
		return false;
	}

	Stream_Config config = {0};
	config.spu_address = STREAM_BUFFER_ADDR;
	config.channel_mask = (1u << channels) - 1u;
	config.interleave = interleave;
	config.buffer_size = RAM_BUFFER_SIZE;
	config.refill_threshold = REFILL_THRESHOLD;
	config.sample_rate = (int)sample_rate;
	config.underrun_callback = stream_underrun_handler;
	Stream_Init(&stream, &config);
	stream_initialized = true;
	read_ctx.channels = channels;
	read_ctx.loop = loop;
	read_ctx.menu_music = menu_music;
#if TEST_CHANNELS == 2
	SPU_CH_VOL_L(0) = 0x3fff;
	SPU_CH_VOL_R(0) = 0;
	SPU_CH_VOL_L(1) = 0;
	SPU_CH_VOL_R(1) = 0x3fff;
#else
#if TEST_BOPEEBO_4CH
	if (menu_music) {
		/* FreakyMenu is stereo in channels 0/1; 2/3 are silent VAGi padding. */
		SPU_CH_VOL_L(0) = MUSIC_SPAN_GAIN;
		SPU_CH_VOL_R(0) = 0;
		SPU_CH_VOL_L(1) = 0;
		SPU_CH_VOL_R(1) = MUSIC_SPAN_GAIN;
		SPU_CH_VOL_L(2) = SPU_CH_VOL_R(2) = 0;
		SPU_CH_VOL_L(3) = SPU_CH_VOL_R(3) = 0;
	} else {
		SPU_CH_VOL_L(0) = MUSIC_SPAN_GAIN;
		SPU_CH_VOL_R(0) = 0;
		SPU_CH_VOL_L(1) = 0;
		SPU_CH_VOL_R(1) = MUSIC_SPAN_GAIN;
		set_voice_pan();
	}
#else
	SPU_CH_VOL_L(0) = TEST_INSTRUMENT_VOLUME;
	SPU_CH_VOL_R(0) = 0;
	SPU_CH_VOL_L(1) = 0;
	SPU_CH_VOL_R(1) = TEST_INSTRUMENT_VOLUME;
	SPU_CH_VOL_L(2) = TEST_VOICE_VOLUME;
	SPU_CH_VOL_R(2) = 0;
	SPU_CH_VOL_L(3) = 0;
	SPU_CH_VOL_R(3) = TEST_VOICE_VOLUME;
#endif
#endif
#if TEST_CHANNELS == 6
	/* Apply one common attenuation to preserve stem balance. */
	for (int channel = 0; channel < 6; channel++) {
		SPU_CH_VOL_L(channel) = SONG_MIX_VOLUME;
		SPU_CH_VOL_R(channel) = 0;
	}
	SPU_CH_VOL_R(1) = SONG_MIX_VOLUME;
	SPU_CH_VOL_R(3) = SONG_MIX_VOLUME;
	SPU_CH_VOL_R(5) = SONG_MIX_VOLUME;
#endif

	read_ctx.start_lba = CdPosToInt(&file.pos) + 1;
	read_ctx.stream_length = (int)(((uint64_t)channels * chunks * interleave +
		CD_SECTOR_SIZE - 1u) / CD_SECTOR_SIZE);
	read_ctx.next_sector = 0;
	read_ctx.refill_length = 0;
	read_ctx.read_pending = 0;
	read_ctx.read_error = 0;

	unsigned frame;
	for (frame = 0; frame < MAX_WAIT_FRAMES; frame++) {
		if (read_ctx.read_error)
			break;
		(void)feed_stream();
		if (!read_ctx.read_pending && read_ctx.callbacks_received &&
		    read_ctx.last_cdsync_return == 0) {
			uint8_t result[4] = {0};
			read_ctx.last_cdsync_return = CdReadSync(0, result);
			save_sync_result(result);
		}
		if (stream.buffer.length >= REFILL_THRESHOLD + interleave * channels)
			break;
		if (read_ctx.read_pending) {
			int pending = CdReadSync(1, 0);
			read_ctx.last_cdsync_return = pending;
			if (pending < 0) {
				set_read_error(pending == -2 ? READ_ERROR_SYNC_ABORT : READ_ERROR_SYNC_TIMEOUT);
				read_ctx.read_pending = 0;
				CdReadCallback(0);
				break;
			}
		}
		VSync(0);
	}
	if (frame == MAX_WAIT_FRAMES)
		abort_cd_read();
	if (read_ctx.read_error) {
		failure_code = FAIL_CD_READ;
		return false;
	}
	if (stream.buffer.length < interleave * channels) {
		failure_code = FAIL_BUFFER_TIMEOUT;
		return false;
	}
	if (frame == MAX_WAIT_FRAMES) {
		failure_code = FAIL_BUFFER_TIMEOUT;
		return false;
	}
	if (!Stream_Start(&stream, false)) {
		failure_code = FAIL_STREAM_START;
		return false;
	}
	return true;
}

static bool start_stream_from_disc(void)
{
	return start_stream_file("\\STREAM.VAG", TEST_CHANNELS,
		TEST_NO_LOOP ? false : true, false);
}

int main(void)
{
	init_video();
#if TEST_PLAYABLE_BOPEEBO
	load_bopeebo_visuals();
	load_menu_visuals();
#if GAME_JUDGEMENT_VISUAL_TEST_DEFAULT
	run_judgement_visual_test();
	return 0;
#endif
#endif
	SpuInit();
	reset_spu_channels();
	CdInit();
#if TEST_CHANNELS >= 4
	InitPAD(pad_buffers[0], PAD_BYTES, pad_buffers[1], PAD_BYTES);
	StartPAD();
	ChangeClearPAD(0);
#endif
#if TEST_BOPEEBO_4CH
#if !TEST_PLAYABLE_BOPEEBO
	if (!upload_resident_sfx())
		show_error(FAIL_SFX_UPLOAD);
	run_pre_music_sfx_test();
#endif
#endif
	if (CdControlB(CdlPause, 0, 0) != 1)
		show_error(FAIL_CD_COMMAND);

#if TEST_PLAYABLE_BOPEEBO
	run_playable_frontend();
	return 0;
#else
	if (!start_stream_from_disc())
		show_error(failure_code ? failure_code : FAIL_HEADER_FORMAT);
#endif

	for (;;) {
		(void)feed_stream();
		if (read_ctx.read_error || underruns)
			show_error(read_ctx.read_error ? FAIL_CD_READ : FAIL_UNDERRUN);
#if TEST_BOPEEBO_4CH
		bool pad_connected = poll_bopeebo4_controls();
#elif TEST_CHANNELS >= 4
		bool pad_connected = poll_voice_toggle();
#endif
		uint32_t samples = Stream_GetSamplesPlayed(&stream);
		unsigned rate = (unsigned)stream.config.sample_rate;
#if TEST_BOPEEBO_4CH
#if !TEST_PLAYABLE_BOPEEBO
			run_during_music_sfx_test(samples);
#endif
#endif
#if TEST_NO_LOOP
		uint32_t song_end_samples = TEST_TOTAL_SAMPLES +
			(uint32_t)(2u * (stream.config.interleave / 16u * 28u));
		if (!song_finished && samples >= song_end_samples) {
			Stream_Stop();
			song_finished = true;
		}
		if (samples > TEST_TOTAL_SAMPLES)
			samples = TEST_TOTAL_SAMPLES;
#endif
		#if TEST_PLAYABLE_BOPEEBO
		if (!song_finished) {
			if (game_pressed & PAD_START) {
				if (!restart_bopeebo()) show_error(failure_code ? failure_code : FAIL_CD_READ);
				samples = 0;
			} else {
#if GAME_SCENE_DEMO_DEFAULT
				update_scene_demo_visuals(samples);
#else
				game_update(samples);
				if (!health_q8 && Stream_IsActive(&stream)) {
					Stream_Stop();
					song_finished = true;
				}
#endif
			}
		} else if (game_pressed & PAD_START) {
			if (!restart_bopeebo()) show_error(failure_code ? failure_code : FAIL_CD_READ);
			samples = 0;
		}
		#endif
		uint32_t milliseconds = rate ? (uint32_t)(((uint64_t)samples * 1000u) / rate) : 0;
		unsigned beat_period_samples = rate * 60u / TEST_BPM;
		unsigned beat_phase_samples = beat_period_samples ? samples % beat_period_samples : 0;
#if TEST_PLAYABLE_BOPEEBO
		draw_gameplay(samples);
#endif
#if !TEST_PLAYABLE_BOPEEBO
		FntPrint(-1, "SPU STREAM / VAGi\n\n");
		FntPrint(-1, "AUDIO %02u:%02u.%03u\n",
			milliseconds / 60000u, (milliseconds / 1000u) % 60u, milliseconds % 1000u);
		FntPrint(-1, "%s\n", beat_phase_samples < rate / 10u ? ">>> BEAT <<<" : "    beat    ");
		FntPrint(-1, "SAMPLES %lu\n", (unsigned long)samples);
		FntPrint(-1, "BUFFER %u / %u\n", (unsigned)stream.buffer.length,
			(unsigned)stream.config.buffer_size);
		FntPrint(-1, "UNDERRUNS %u  CD ERRORS %u\n", (unsigned)underruns, (unsigned)read_errors);
#endif
#if TEST_BOPEEBO_4CH
#if TEST_PLAYABLE_BOPEEBO
		/* Keep the production HUD compact; camera QA is explicitly labelled. */
#if GAME_SCENE_DEMO_DEFAULT
		{
			static const char *const focus_names[] = { "BF", "DAD", "GF", "STATIC" };
			unsigned focus_index = camera_focus_display <= 2u ? camera_focus_display : 3u;
		FntPrint(hud_font_id, "CAMERA DEMO %s %02u.%03u\n", focus_names[focus_index],
				milliseconds / 1000u, milliseconds % 1000u);
		}
#else
		draw_score_display();
		draw_judgement_popup(samples, rate);
		draw_combo_popup(samples, rate);
#endif
		if (GAME_SCENE_DEMO_DEFAULT) FntFlush(hud_font_id);
		if (diagnostics_visible) {
#if GAME_HEALTH_BAR_TEST_DEFAULT
			FntPrint(diagnostics_font_id, "HEALTH TEST REAL %u%% DRAW %u%%\n",
				hud_actual_health_percent, hud_display_health_percent);
			FntPrint(diagnostics_font_id, "EDGE X=%d  DAD X=%d  BF X=%d\n",
				hud_health_boundary_x, hud_dad_icon_x, hud_bf_icon_x);
			FntFlush(diagnostics_font_id);
#else
			static const char *const focus_names[] = { "BF", "DAD", "GF", "STATIC" };
			unsigned focus_index = camera_focus_display <= 2u ? camera_focus_display : 3u;
			FntPrint(diagnostics_font_id, "CRT SAFE 95/90 SELECT:HIDE\n");
			FntPrint(diagnostics_font_id, "AUDIO %02u:%02u.%03u FOCUS %s%s  TRI:%s\n",
				milliseconds / 60000u, (milliseconds / 1000u) % 60u, milliseconds % 1000u,
				focus_names[focus_index], camera_transitioning ? " ->" : "",
				dad_lanes_visible ? "ON" : "OFF");
			FntPrint(diagnostics_font_id, "BUF %u/%u CD %u U %u PAD %s\n", (unsigned)stream.buffer.length,
				(unsigned)stream.config.buffer_size, (unsigned)read_errors, (unsigned)underruns,
				pad_connected ? "ON" : "OFF");
			FntPrint(diagnostics_font_id, "SCORE %ld COMBO %lu HIT %lu MISS %lu DROP %lu\n",
				(long)score, (unsigned long)combo, (unsigned long)hits,
				(unsigned long)misses, (unsigned long)hold_drops);
			FntPrint(diagnostics_font_id, "VIS WORLD %u HIGH %u DROP %u HUD %u J %u\n",
				gameplay_visual_prim_count, visual_prim_high_water, visual_prim_rejected,
				(unsigned)score_text_flushed, (unsigned)judgement_drawn);
			FntPrint(diagnostics_font_id, "HP REAL %u%% HUD %u%% EDGE X=%d\n",
				hud_actual_health_percent, hud_display_health_percent, hud_health_boundary_x);
			FntPrint(diagnostics_font_id, "ICONS D=%d BF=%d SAFE 16..280\n", hud_dad_icon_x, hud_bf_icon_x);
			FntPrint(diagnostics_font_id, "BF %s PAN %u/7 SFX %u\n",
				(voices_muted || bf_miss_silenced) ? "MUTED" : "LIVE",
				(unsigned)pan_width, (unsigned)sfx_manual_trigger_count);
#if GAME_HEALTH_BAR_TEST_DEFAULT
			FntPrint(diagnostics_font_id, "HEALTH VISUAL TEST ONLY\n");
#endif
			FntPrint(diagnostics_font_id, "D-PAD PLAY C MUTE L1/R1 PAN J SFX  START:RESTART\n");
			FntFlush(diagnostics_font_id);
#endif
		}
#else
		FntPrint(-1, "BOPEEBO 4CH  INST / DAD-L / BF-R\n");
		FntPrint(-1, "PAD %s  CIRCLE %s\n", pad_connected ? "CONNECTED" : "OFFLINE",
			circle_down ? "DOWN" : "UP");
		FntPrint(-1, "BF VOICE: %s (CIRCLE TOGGLES)\n", voices_muted ? "MUTED" : "AUDIBLE");
		FntPrint(-1, "PAN WIDTH %u/7 (DEFAULT 5)\n", (unsigned)pan_width);
		FntPrint(-1, "SQUARE %s  PRESSES %u\n", sfx_square_down ? "DOWN" : "UP",
			(unsigned)sfx_square_press_count);
		FntPrint(-1, "SFX TRIGGERS MAN %u AUTO %u\n", sfx_manual_trigger_count,
			(unsigned)sfx_auto_trigger_count);
		FntPrint(-1, "AUTO DURING %u/%u  LAST VOICE %u\n", sfx_auto_during_count,
			(unsigned)SFX_AUTO_DURING_COUNT, sfx_last_voice);
		FntPrint(-1, "SFX ACTIVE %u/%u VOL BUDGET %u\n", active_sfx_voice_count(),
			(unsigned)SFX_VOICE_COUNT, (unsigned)SFX_POOL_VOLUME_BUDGET);
		FntPrint(-1, "UPLOAD %u/%u DMA %d\n", (unsigned)sfx_write_size,
			(unsigned)SFX_SAMPLE_SIZE, sfx_transfer_completed);
		FntPrint(-1, "PLAYBACK: %s (NO LOOP)\n", song_finished ? "FINISHED" : "PLAYING");
#endif
#elif TEST_CHANNELS == 4
		FntPrint(-1, "4CH: INST L/R + VOICES L/R\n");
		FntPrint(-1, "PAD %s  CIRCLE %s\n", pad_connected ? "CONNECTED" : "OFFLINE",
			circle_down ? "DOWN" : "UP");
		FntPrint(-1, "VOICES: %s (CIRCLE TOGGLES)\n", voices_muted ? "MUTED" : "AUDIBLE");
		FntPrint(-1, "VOICE CHANNELS KEEP PLAYING\n");
#elif TEST_CHANNELS == 6
		FntPrint(-1, "6CH: INST / BF VOICE / DAD VOICE\n");
		FntPrint(-1, "PAD %s  CIRCLE %s\n", pad_connected ? "CONNECTED" : "OFFLINE",
			circle_down ? "DOWN" : "UP");
		FntPrint(-1, "BF VOICE: %s (CIRCLE TOGGLES)\n", voices_muted ? "MUTED" : "AUDIBLE");
		FntPrint(-1, "DAD VOICE: AUDIBLE / UNCHANGED\n");
		FntPrint(-1, "PLAYBACK: %s (NO LOOP)\n", song_finished ? "FINISHED" : "PLAYING");
#else
		FntPrint(-1, "STEREO SPU / 120 BPM TEST\n");
#endif
		FntFlush(-1);
		display_frame();
#if TEST_PLAYABLE_BOPEEBO
		if (!health_q8 && song_finished) {
			/* Keep the post-failure screen live for the Start restart prompt. */
		}
#endif
#if TEST_BOPEEBO_4CH
		frame_counter++;
#endif
	}
}

