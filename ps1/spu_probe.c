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
#define SFX_VOLUME 0x0800u
#define SFX_SPU_ADDR 0x10000u
#define SFX_FIRST_VOICE 4u
#define SFX_VOICE_COUNT 4u

#if TEST_BOPEEBO_4CH
#include "bopeebo_sfx_data.h"
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
#if TEST_CHANNELS >= 4
#define PAD_BYTES 34
static uint8_t pad_buffers[2][PAD_BYTES];
static uint16_t previous_pad_buttons = 0xffff;
static bool pad_was_connected;
static bool voices_muted;
static bool circle_down;
#endif
#if TEST_NO_LOOP
static bool song_finished;
#endif
#if TEST_BOPEEBO_4CH
static uint8_t pan_width = 7;
static uint8_t sfx_voice_cursor;
static unsigned sfx_trigger_count;
static bool sfx_uploaded;
#endif

static void abort_cd_read(void);

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
	SPU_CH_VOL_L(3) = voices_muted ? 0 : right;
	SPU_CH_VOL_R(3) = voices_muted ? 0 : left;
}

static void play_resident_sfx(void)
{
	unsigned voice = SFX_FIRST_VOICE + sfx_voice_cursor;
	uint32_t key = 1u << voice;
	SpuSetKey(0, key);
	SPU_CH_ADDR(voice) = getSPUAddr(SFX_SPU_ADDR);
	SPU_CH_FREQ(voice) = getSPUSampleRate(SFX_SAMPLE_RATE);
	SPU_CH_VOL_L(voice) = SFX_VOLUME;
	SPU_CH_VOL_R(voice) = SFX_VOLUME;
	SPU_CH_ADSR1(voice) = 0x00ff;
	SPU_CH_ADSR2(voice) = 0x0000;
	SpuSetKey(1, key);
	sfx_voice_cursor = (uint8_t)((sfx_voice_cursor + 1u) % SFX_VOICE_COUNT);
	sfx_trigger_count++;
}

static bool upload_resident_sfx(void)
{
	SpuSetTransferMode(SPU_TRANSFER_BY_DMA);
	SpuSetTransferStartAddr(SFX_SPU_ADDR);
	SpuWrite((const uint32_t *)sfx_sample, SFX_SAMPLE_SIZE);
	if (!SpuIsTransferCompleted(SPU_TRANSFER_WAIT))
		return false;
	sfx_uploaded = true;
	return true;
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
		if ((previous_pad_buttons & PAD_LEFT) && !(buttons & PAD_LEFT) && pan_width)
			pan_width--;
		if ((previous_pad_buttons & PAD_RIGHT) && !(buttons & PAD_RIGHT) && pan_width < 7u)
			pan_width++;
		if ((previous_pad_buttons & PAD_SQUARE) && !(buttons & PAD_SQUARE) && sfx_uploaded)
			play_resident_sfx();
		previous_pad_buttons = buttons;
	}
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
#endif
	if (CdControlB(CdlPause, 0, 0) != 1)
		show_error(FAIL_CD_COMMAND);

	if (!start_stream_from_disc())
		show_error(failure_code ? failure_code : FAIL_HEADER_FORMAT);

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
		uint32_t milliseconds = rate ? (uint32_t)(((uint64_t)samples * 1000u) / rate) : 0;
		unsigned beat_period_samples = rate * 60u / TEST_BPM;
		unsigned beat_phase_samples = beat_period_samples ? samples % beat_period_samples : 0;
		FntPrint(-1, "SPU STREAM / VAGi\n\n");
		FntPrint(-1, "AUDIO %02u:%02u.%03u\n",
			milliseconds / 60000u, (milliseconds / 1000u) % 60u, milliseconds % 1000u);
		FntPrint(-1, "%s\n", beat_phase_samples < rate / 10u ? ">>> BEAT <<<" : "    beat    ");
		FntPrint(-1, "SAMPLES %lu\n", (unsigned long)samples);
		FntPrint(-1, "BUFFER %u / %u\n", (unsigned)stream.buffer.length,
			(unsigned)stream.config.buffer_size);
		FntPrint(-1, "UNDERRUNS %u  CD ERRORS %u\n", (unsigned)underruns, (unsigned)read_errors);
#if TEST_BOPEEBO_4CH
		FntPrint(-1, "BOPEEBO 4CH  INST / DAD-L / BF-R\n");
		FntPrint(-1, "PAD %s  CIRCLE %s\n", pad_connected ? "CONNECTED" : "OFFLINE",
			circle_down ? "DOWN" : "UP");
		FntPrint(-1, "BF VOICE: %s (CIRCLE TOGGLES)\n", voices_muted ? "MUTED" : "AUDIBLE");
		FntPrint(-1, "PAN WIDTH %u/7 (LEFT/RIGHT)\n", (unsigned)pan_width);
		FntPrint(-1, "SQUARE: PLAY SFX (%u VOICES)\n", (unsigned)SFX_VOICE_COUNT);
		FntPrint(-1, "SFX TRIGGERS %u  VOLUME %u/16383\n", sfx_trigger_count,
			(unsigned)SFX_VOLUME);
		FntPrint(-1, "PLAYBACK: %s (NO LOOP)\n", song_finished ? "FINISHED" : "PLAYING");
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
	}
}
