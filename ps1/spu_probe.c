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
#define SFX_POOL_VOLUME_BUDGET 0x1800u
#define SFX_SPU_ADDR 0x10000u
#define SFX_FIRST_VOICE 4u
#define SFX_VOICE_COUNT 4u
#define SFX_BUSY_FRAMES 9u
#define SFX_AUTO_DURING_COUNT 4u
#define SFX_AUTO_DURING_START_SAMPLES (2u * 43008u)

#if TEST_BOPEEBO_4CH
#include "bopeebo_sfx_data.h"
#endif
#if TEST_PLAYABLE_BOPEEBO
#include "bopeebo_chart.h"
#include "bopeebo_visual_data.h"
#define GAME_WINDOW_SAMPLES ((uint32_t)(BOPEEBO_CHART_RATE * 160u / 1000u))
#define GAME_MAX_PRIMS 220u
#define BOPEEBO_BPM 100u
static uint8_t game_note_state[BOPEEBO_NOTE_COUNT];
static int16_t active_hold[4] = { -1, -1, -1, -1 };
static uint32_t hold_last_sample[4];
static uint32_t hold_drops;
static int32_t score;
static uint32_t combo;
static uint32_t misses;
static uint32_t hits;
static uint16_t health_q8 = 256;
static bool bf_miss_silenced;
static uint8_t bf_visual_state;
static uint8_t bf_visual_lane;
static uint32_t bf_visual_until;
static uint8_t dad_visual_lane;
static uint32_t dad_visual_until;
static bool diagnostics_visible;
static POLY_F4 game_prims[GAME_MAX_PRIMS];
static unsigned game_prim_count;
static POLY_FT4 visual_prims[16];
static unsigned visual_prim_count;

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
	FntOpen(8, 16, 304, 208, 0, 512);
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
	/* 4bpp pages begin below the SDK font and to the right of both framebuffers. */
	for (unsigned page = 0; page < BOPEEBO_VISUAL_PAGE_COUNT; page++) {
		RECT rect = { (short)(320 + (int)page * 64), 256, 64, 256 };
		LoadImage(&rect, (uint32_t *)bopeebo_visual_pages[page]);
	}
	for (unsigned palette = 0; palette < 4; palette++) {
		RECT rect = { (short)(palette * 16u), 480, 16, 1 };
		LoadImage(&rect, (uint32_t *)bopeebo_visual_palettes[palette]);
	}
	DrawSync(0);
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
		FntPrint(-1, "SFX WRITE %u/%u DMA %d ADDR %05X\n",
			(unsigned)sfx_write_size, (unsigned)SFX_SAMPLE_SIZE,
			sfx_transfer_completed, (unsigned)SFX_SPU_ADDR);
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
	uint16_t volume = (uint16_t)(SFX_POOL_VOLUME_BUDGET / count);
	for (unsigned i = 0; i < SFX_VOICE_COUNT; i++) {
		if (!sfx_voice_active[i])
			continue;
		unsigned voice = SFX_FIRST_VOICE + i;
		SPU_CH_VOL_L(voice) = volume;
		SPU_CH_VOL_R(voice) = volume;
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

static void play_resident_sfx(bool manual)
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
	SpuSetKey(0, key);
	SPU_CH_ADDR(voice) = getSPUAddr(SFX_SPU_ADDR);
	SPU_CH_FREQ(voice) = getSPUSampleRate(SFX_SAMPLE_RATE);
	SPU_CH_ADSR1(voice) = 0x00ff;
	SPU_CH_ADSR2(voice) = 0x0000;
	sfx_voice_active[slot] = true;
	sfx_voice_until_frame[slot] = frame_counter + SFX_BUSY_FRAMES;
	update_sfx_pool_volumes();
	SpuSetKey(1, key);
	sfx_last_voice = voice;
	sfx_voice_cursor = (uint8_t)((slot + 1u) % SFX_VOICE_COUNT);
	if (manual)
		sfx_manual_trigger_count++;
	else
		sfx_auto_trigger_count++;
}

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
	play_resident_sfx(false);
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
		play_resident_sfx(false);
		sfx_auto_during_count++;
		sfx_auto_during_next_frame = frame_counter + 2u;
	}
}

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
		if ((previous_pad_buttons & PAD_SQUARE) && !(buttons & PAD_SQUARE)) {
			sfx_square_press_count++;
			if (sfx_uploaded)
				play_resident_sfx(true);
		}
		if ((previous_pad_buttons & PAD_CIRCLE) && !(buttons & PAD_CIRCLE))
			voices_muted = !voices_muted;
#if TEST_PLAYABLE_BOPEEBO
		if ((previous_pad_buttons & PAD_SELECT) && !(buttons & PAD_SELECT))
			diagnostics_visible = !diagnostics_visible;
		if ((previous_pad_buttons & PAD_L1) && !(buttons & PAD_L1) && pan_width)
			pan_width--;
		if ((previous_pad_buttons & PAD_R1) && !(buttons & PAD_R1) && pan_width < 7u)
			pan_width++;
#else
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

static void game_miss(unsigned index)
{
	game_note_state[index] = 2;
	misses++;
	combo = 0;
	score -= 100;
	add_health(-20);
	bf_miss_silenced = true;
	bf_visual_state = 2;
	bf_visual_lane = (uint8_t)(bopeebo_notes[index].lane & 3u);
	bf_visual_until = Stream_GetSamplesPlayed(&stream) + BOPEEBO_CHART_RATE * 350u / 1000u;
	play_resident_sfx(false);
	set_voice_pan();
}

static void game_hold_drop(unsigned lane, uint32_t remaining_samples, uint32_t rate)
{
	hold_drops++;
	combo = 0;
	score -= (int32_t)(((uint64_t)remaining_samples * 125u) / rate);
	bf_miss_silenced = true;
	bf_visual_state = 2;
	bf_visual_lane = (uint8_t)lane;
	bf_visual_until = Stream_GetSamplesPlayed(&stream) + rate * 350u / 1000u;
	play_resident_sfx(false);
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
			dad_visual_until = bopeebo_notes[i].tail > bopeebo_notes[i].head ?
				bopeebo_notes[i].tail : samples + rate * 250u / 1000u;
		}
		if (bopeebo_notes[i].lane < 4u && !game_note_state[i] &&
		    samples > bopeebo_notes[i].head &&
		    (uint64_t)(samples - bopeebo_notes[i].head) * 1000u > (uint64_t)rate * 160u)
			game_miss(i);
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
					game_hold_drop(lane, remaining, rate);
				active_hold[lane] = -1;
			}
		}
	}

	for (unsigned lane = 0; lane < 4; lane++) {
		uint16_t mask = masks[lane];
		if (!(game_pressed & mask)) continue;
		int target = find_player_note(lane, samples);
		if (target < 0) {
			combo = 0;
			score -= 10;
			add_health(-20);
			play_resident_sfx(false);
			bf_visual_state = 2;
			bf_visual_lane = (uint8_t)lane;
			bf_visual_until = samples + rate * 350u / 1000u;
			continue;
		}
		uint32_t head = bopeebo_notes[target].head;
		uint32_t diff = samples > head ? samples - head : head - samples;
		game_note_state[target] = 1;
		int32_t award = pbot1_score(diff, rate);
		score += award;
		uint64_t timing = (uint64_t)diff * 1000u;
		if (timing <= (uint64_t)rate * 45u) { combo++; add_health(8); }
		else if (timing <= (uint64_t)rate * 90u) { combo++; add_health(4); }
		else if (timing <= (uint64_t)rate * 135u) { combo = 0; }
		else { combo = 0; add_health(-5); }
		hits++;
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

static void draw_rect(int x, int y, int width, int height, uint8_t r, uint8_t g, uint8_t b)
{
	if (game_prim_count >= GAME_MAX_PRIMS || width <= 0 || height <= 0) return;
	POLY_F4 *p = &game_prims[game_prim_count++];
	setPolyF4(p);
	setRGB0(p, r, g, b);
	setXY4(p, x, y, x + width, y, x, y + height, x + width, y + height);
	DrawPrim((uint32_t *)p);
}

static void draw_visual_frame(unsigned frame, int x, int y)
{
	if (visual_prim_count >= 16u || frame >= BOPEEBO_VISUAL_FRAME_COUNT) return;
	const BopeeboVisualFrame *visual = &bopeebo_visual_frames[frame];
	POLY_FT4 *p = &visual_prims[visual_prim_count++];
	setPolyFT4(p);
	setRGB0(p, 128, 128, 128);
	setXY4(p, x, y, x + visual->w, y, x, y + visual->h, x + visual->w, y + visual->h);
	setUV4(p, visual->u, visual->v,
		(uint8_t)(visual->u + visual->w - 1u), visual->v,
		visual->u, (uint8_t)(visual->v + visual->h - 1u),
		(uint8_t)(visual->u + visual->w - 1u), (uint8_t)(visual->v + visual->h - 1u));
	p->tpage = getTPage(0, 0, 320 + (int)visual->page * 64, 256);
	setClut(p, visual->palette * 16, 480);
	DrawPrim((uint32_t *)p);
}

static void draw_stage_scene(uint32_t samples)
{
	/* Official stage layers are reduced with nearest-neighbour scaling. */
	draw_visual_frame(VIS_STAGE_BACK_0, 0, 0);
	draw_visual_frame(VIS_STAGE_BACK_1, 256, 0);
	draw_visual_frame(VIS_STAGE_CURTAINS_0, 0, 0);
	draw_visual_frame(VIS_STAGE_CURTAINS_1, 256, 0);

	unsigned beat = (unsigned)(((uint64_t)samples * BOPEEBO_BPM * 4u) /
		((uint64_t)BOPEEBO_CHART_RATE * 60u));
	unsigned dad_frame = (samples < dad_visual_until) ? dad_visual_lane % 6u : (beat / 2u) % 6u;
	draw_visual_frame(VIS_DAD_IDLE_0 + dad_frame, 18, 62);
	draw_visual_frame(VIS_GF_IDLE_0 + (beat / 2u) % 4u, 122, 73);

	unsigned bf_frame;
	if (bf_visual_state == 2u) {
		bf_frame = VIS_BF_MISS_LEFT_0 + (unsigned)bf_visual_lane * 2u + ((beat & 1u) ? 1u : 0u);
	} else if (bf_visual_state == 1u) {
		bf_frame = VIS_BF_LEFT_0 + (unsigned)bf_visual_lane * 2u + ((beat & 1u) ? 1u : 0u);
	} else {
		bf_frame = VIS_BF_IDLE_0 + ((beat & 1u) ? 1u : 0u);
	}
	draw_visual_frame(bf_frame, 234, 60);

	/* The official foreground stage rail stays behind the readable note lanes. */
	draw_visual_frame(VIS_STAGE_FRONT_0, 0, 184);
	draw_visual_frame(VIS_STAGE_FRONT_1, 256, 184);
}

static void draw_gameplay(uint32_t samples)
{
	game_prim_count = 0;
	visual_prim_count = 0;
	draw_stage_scene(samples);
	for (unsigned side = 0; side < 2; side++) {
		int origin = side ? 170 : 20;
		for (unsigned lane = 0; lane < 4; lane++) {
			int x = origin + (int)lane * 24;
			draw_rect(x, 124, 20, 92, 16, 18, 31);
			draw_rect(x, 199, 20, 3, 104, 104, 128);
			/* Dad is drawn on the left; BF is on the right. Chart lanes stay unchanged. */
			draw_rect(x + 2, 197, 16, 7, side ? 52 : 224, side ? 198 : 118, side ? 240 : 74);
		}
	}
	for (unsigned i = 0; i < BOPEEBO_NOTE_COUNT; i++) {
		const BopeeboNote *note = &bopeebo_notes[i];
		int is_dad = note->lane >= 4u;
		unsigned lane = note->lane & 3u;
		int x = (is_dad ? 20 : 170) + (int)lane * 24 + 3;
		int y = 200 - (int)(((int64_t)note->head - (int64_t)samples) * 40 / (int64_t)BOPEEBO_CHART_RATE);
		int tail_y = 200 - (int)(((int64_t)note->tail - (int64_t)samples) * 40 / (int64_t)BOPEEBO_CHART_RATE);
		if (note->tail > note->head) {
			int top = y < tail_y ? y : tail_y;
			int bottom = y > tail_y ? y : tail_y;
			if (bottom > 124 && top < 216)
				draw_rect(x + 4, top < 124 ? 124 : top, 8, (bottom > 216 ? 216 : bottom) - (top < 124 ? 124 : top),
					is_dad ? 176 : 48, is_dad ? 78 : 158, is_dad ? 56 : 220);
		}
		if (game_note_state[i] == 1u || game_note_state[i] == 2u || (is_dad && game_note_state[i] == 3u)) continue;
		if (y >= 124 && y <= 216)
			draw_rect(x, y - 5, 18, 10, is_dad ? 248 : 80, is_dad ? 145 : 220, is_dad ? 96 : 255);
	}
}

static void reset_game_state(void)
{
	memset(game_note_state, 0, sizeof(game_note_state));
	for (unsigned lane = 0; lane < 4; lane++) active_hold[lane] = -1;
	score = combo = misses = hits = 0;
	hold_drops = 0;
	health_q8 = 256;
	bf_miss_silenced = false;
	bf_visual_state = 0;
	bf_visual_lane = 0;
	bf_visual_until = 0;
	dad_visual_lane = 0;
	dad_visual_until = 0;
	diagnostics_visible = false;
}

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
#if TEST_NO_LOOP
		return false;
#else
		next_sector = 0;
		max_length = read_ctx.stream_length;
#endif
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

static bool valid_header(const VAG_Header *header, unsigned *channels_out,
	unsigned *interleave_out, unsigned *sample_rate_out, unsigned *chunks_out,
	int file_size)
{
	if (memcmp(&header->magic, "VAGi", 4) != 0)
		return false;
	unsigned interleave = header->interleave;
	unsigned channels = header->channels ? header->channels : 2u;
	unsigned bytes_per_channel = SWAP_ENDIAN(header->size);
	unsigned sample_rate = SWAP_ENDIAN(header->sample_rate);
	if (header->version != 0x20000000u || channels != TEST_CHANNELS ||
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

static bool start_stream_from_disc(void)
{
	CdlFILE file;
	if (!CdSearchFile(&file, "\\STREAM.VAG")) {
		failure_code = FAIL_NOT_FOUND;
		return false;
	}
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
	if (!valid_header(header, &channels, &interleave, &sample_rate, &chunks,
		file.size)) {
		failure_code = FAIL_HEADER_FORMAT;
		return false;
	}

	Stream_Config config = {0};
	config.spu_address = STREAM_BUFFER_ADDR;
	config.channel_mask = (1u << TEST_CHANNELS) - 1u;
	config.interleave = interleave;
	config.buffer_size = RAM_BUFFER_SIZE;
	config.refill_threshold = REFILL_THRESHOLD;
	config.sample_rate = (int)sample_rate;
	config.underrun_callback = stream_underrun_handler;
	Stream_Init(&stream, &config);
	stream_initialized = true;
#if TEST_CHANNELS == 2
	SPU_CH_VOL_L(0) = 0x3fff;
	SPU_CH_VOL_R(0) = 0;
	SPU_CH_VOL_L(1) = 0;
	SPU_CH_VOL_R(1) = 0x3fff;
#else
#if TEST_BOPEEBO_4CH
	SPU_CH_VOL_L(0) = MUSIC_SPAN_GAIN;
	SPU_CH_VOL_R(0) = 0;
	SPU_CH_VOL_L(1) = 0;
	SPU_CH_VOL_R(1) = MUSIC_SPAN_GAIN;
	set_voice_pan();
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

int main(void)
{
	init_video();
#if TEST_PLAYABLE_BOPEEBO
	load_bopeebo_visuals();
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
	if (!upload_resident_sfx())
		show_error(FAIL_SFX_UPLOAD);
#if !TEST_PLAYABLE_BOPEEBO
	run_pre_music_sfx_test();
#endif
#endif
	if (CdControlB(CdlPause, 0, 0) != 1)
		show_error(FAIL_CD_COMMAND);

	if (!start_stream_from_disc())
		show_error(failure_code ? failure_code : FAIL_HEADER_FORMAT);
#if TEST_PLAYABLE_BOPEEBO
	reset_game_state();
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
				game_update(samples);
				if (!health_q8 && Stream_IsActive(&stream)) {
					Stream_Stop();
					song_finished = true;
				}
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
		draw_rect(20, 220, 264, 6, 48, 48, 58);
		draw_rect(20, 220, (int)((uint32_t)health_q8 * 132u / 256u), 6, 80, 210, 112);
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
		FntPrint(-1, "BOPEEBO %02u:%02u  DAD LEFT / BF RIGHT\n",
			milliseconds / 60000u, (milliseconds / 1000u) % 60u);
		if (diagnostics_visible) {
			FntPrint(-1, "BUF %u/%u CD %u U %u PAD %s\n", (unsigned)stream.buffer.length,
				(unsigned)stream.config.buffer_size, (unsigned)read_errors, (unsigned)underruns,
				pad_connected ? "ON" : "OFF");
			FntPrint(-1, "SCORE %ld COMBO %lu HIT %lu MISS %lu DROP %lu\n",
				(long)score, (unsigned long)combo, (unsigned long)hits,
				(unsigned long)misses, (unsigned long)hold_drops);
			FntPrint(-1, "HP %u.%02u BF %s PAN %u/7 SFX %u\n",
				(unsigned)(health_q8 / 256u), (unsigned)((health_q8 % 256u) * 100u / 256u),
				(voices_muted || bf_miss_silenced) ? "MUTED" : "LIVE",
				(unsigned)pan_width, (unsigned)sfx_manual_trigger_count);
			FntPrint(-1, "D-PAD PLAY C MUTE L1/R1 PAN J SFX\n");
		}
		FntPrint(-1, "SELECT INFO  START RESTART  %s\n", pad_connected ? "PAD ON" : "PAD OFF");
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
