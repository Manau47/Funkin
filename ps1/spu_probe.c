/* CD-to-SPU VAGi streaming probe; audio data is supplied locally at build time. */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <psxapi.h>
#include <psxetc.h>
#include <psxgpu.h>
#include <psxspu.h>
#include <psxcd.h>

#include "stream.h"

#define SCREEN_W 320
#define SCREEN_H 240
#define RAM_BUFFER_SIZE 0x18000
#define REFILL_THRESHOLD (24 * 2048)
#define DUMMY_BLOCK_ADDR 0x1000
#define STREAM_BUFFER_ADDR 0x1010
#define TEST_BPM 120

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

#define SWAP_ENDIAN(x) (((x) << 24) | (((x) & 0x0000ff00u) << 8) | \
	(((x) & 0x00ff0000u) >> 8) | ((x) >> 24))

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

static unsigned bcd_to_uint(uint8_t value)
{
	return (unsigned)((value >> 4) * 10 + (value & 0x0f));
}

static void cd_read_handler(CdlIntrResult event, uint8_t *payload)
{
	(void)payload;
	if (event == CdlDiskError) {
		read_errors++;
		return;
	}
	Stream_Feed(&stream, read_ctx.refill_length * 2048u);
}

static void stream_underrun_handler(void)
{
	underruns++;
}

static void reset_spu_channels(void)
{
	SpuSetKey(0, 0x00ffffff);
	for (int channel = 0; channel < 24; channel++) {
		SPU_CH_ADDR(channel) = getSPUAddr(DUMMY_BLOCK_ADDR);
		SPU_CH_FREQ(channel) = 0x1000;
	}
	SpuSetKey(1, 0x00ffffff);
}

static bool feed_stream(void)
{
	if (CdReadSync(1, 0) > 0)
		return true;
	if (Stream_GetRefillLength(&stream) < REFILL_THRESHOLD)
		return false;

	uint8_t *ptr;
	size_t sectors = Stream_GetFeedPtr(&stream, &ptr) / 2048u;
	int next_sector = read_ctx.next_sector;
	int max_length = read_ctx.stream_length - next_sector;
	while (max_length <= 0) {
		next_sector -= read_ctx.stream_length;
		max_length += read_ctx.stream_length;
	}
	if (sectors > (size_t)max_length)
		sectors = (size_t)max_length;
	if (sectors == 0)
		return false;

	CdlLOC position;
	CdIntToPos(read_ctx.start_lba + next_sector, &position);
	CdControl(CdlSetloc, &position, 0);
	CdReadCallback(cd_read_handler);
	CdRead((int)sectors, (uint32_t *)ptr, CdlModeSpeed);
	read_ctx.next_sector = next_sector + (int)sectors;
	read_ctx.refill_length = sectors;
	return true;
}

static bool start_stream_from_disc(void)
{
	CdlFILE file;
	if (!CdSearchFile(&file, "\\STREAM.VAG"))
		return false;

	uint32_t header_sector[512];
	CdControl(CdlSetloc, &file.pos, 0);
	CdReadCallback(0);
	CdRead(1, header_sector, CdlModeSpeed);
	CdReadSync(0, 0);
	const VAG_Header *header = (const VAG_Header *)header_sector;
	if (header->magic != 0x69474156u || header->interleave == 0)
		return false;

	unsigned channels = header->channels ? header->channels : 2;
	if (channels != 2)
		return false;
	unsigned interleave = header->interleave;
	unsigned bytes_per_channel = SWAP_ENDIAN(header->size);
	unsigned sample_rate = SWAP_ENDIAN(header->sample_rate);
	unsigned chunks = (bytes_per_channel + interleave - 1u) / interleave;

	Stream_Config config = {0};
	config.spu_address = STREAM_BUFFER_ADDR;
	config.channel_mask = 3;
	config.interleave = interleave;
	config.buffer_size = RAM_BUFFER_SIZE;
	config.refill_threshold = REFILL_THRESHOLD;
	config.sample_rate = (int)sample_rate;
	config.underrun_callback = stream_underrun_handler;
	Stream_Init(&stream, &config);
	SPU_CH_VOL_L(0) = 0x3fff;
	SPU_CH_VOL_R(0) = 0;
	SPU_CH_VOL_L(1) = 0;
	SPU_CH_VOL_R(1) = 0x3fff;

	read_ctx.start_lba = CdPosToInt(&file.pos) + 1;
	read_ctx.stream_length = (int)((channels * chunks * interleave + 2047u) / 2048u);
	read_ctx.next_sector = 0;
	read_ctx.refill_length = 0;
	while (feed_stream())
		__asm__ volatile("");
	return Stream_Start(&stream, false);
}

int main(void)
{
	init_video();
	SpuInit();
	reset_spu_channels();
	CdInit();
	CdControlB(CdlPause, 0, 0);

	if (!start_stream_from_disc()) {
		FntPrint(-1, "SPU STREAM SETUP FAILED\n\nCHECK STREAM.VAG FORMAT");
		FntFlush(-1);
		for (;;)
			display_frame();
	}

	for (;;) {
		(void)feed_stream();
		uint32_t samples = Stream_GetSamplesPlayed(&stream);
		unsigned rate = (unsigned)stream.config.sample_rate;
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
		FntPrint(-1, "STEREO SPU / 120 BPM TEST\n");
		FntFlush(-1);
		display_frame();
	}
}
