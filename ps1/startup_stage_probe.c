#include <stdint.h>
#include <stdlib.h>
#include <psxapi.h>
#include <psxgpu.h>
#include <psxpad.h>
#include <psxcd.h>
#include <psxspu.h>
#include "bopeebo_visual_data.h"

#define SCREEN_W 320
#define SCREEN_H 240
#define PAD_BYTES 34
#define CRT_BSS_PAD_BYTES 34640u
#define SCENE_PAGE_SECTORS 32u
#define SCENE_PAGE_BYTES (SCENE_PAGE_SECTORS * 2048u)
#define SCENE_FIRST_PAGE_CRC32 0xA3BEABD8u
#define SCENE_PAGE_CRC32 0xA3BEABD8u
#define CD_READ_TIMEOUT_FRAMES 300u

/* Bring the uninitialized data footprint close to the game's linked BSS. */
static volatile uint8_t crt_bss_padding[CRT_BSS_PAD_BYTES];
static char pad_buffers[2][PAD_BYTES];
static volatile unsigned read_callback_count;
static volatile int read_callback_event;
static volatile unsigned read_callback_has_payload;
static volatile uint8_t read_callback_payload[4];

static void probe_cd_read_handler(CdlIntrResult event, uint8_t *payload)
{
	read_callback_count++;
	read_callback_event = (int)event;
	read_callback_has_payload = payload != 0;
	for (unsigned i = 0; i < 4u; i++)
		read_callback_payload[i] = payload ? payload[i] : 0xFFu;
}

static uint32_t crc32_update(uint32_t crc, const uint8_t *data, unsigned length)
{
	for (unsigned i = 0; i < length; i++) {
		crc ^= data[i];
		for (unsigned bit = 0; bit < 8; bit++)
			crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
	}
	return crc;
}

static uint32_t crc32_bytes(const uint8_t *data, unsigned length)
{
	return ~crc32_update(0xFFFFFFFFu, data, length);
}

static void show_stage(unsigned stage, uint8_t r, uint8_t g, uint8_t b)
{
	static DISPENV display;
	static DRAWENV draw;
	static FILL fill;
	(void)stage;
	setFill(&fill);
	setRGB0(&fill, r, g, b);
	setXY0(&fill, 0, 0);
	setWH(&fill, SCREEN_W, SCREEN_H);
	DrawPrim((uint32_t *)&fill);
	DrawSync(0);
	SetDispMask(1);
}

int main(void)
{
	DISPENV display;
	DRAWENV draw;
	FILL fill;
	int fonts[6];

	/* First marker means crt -> main and ResetGraph have both completed. */
	ResetGraph(0);
	SetDefDrawEnv(&draw, 0, 0, SCREEN_W, SCREEN_H);
	SetDefDispEnv(&display, 0, 0, SCREEN_W, SCREEN_H);
	PutDrawEnv(&draw);
	PutDispEnv(&display);
	setFill(&fill);
	setRGB0(&fill, 32, 96, 160);
	setXY0(&fill, 0, 0);
	setWH(&fill, SCREEN_W, SCREEN_H);
	DrawPrim((uint32_t *)&fill);
	DrawSync(0);
	SetDispMask(1);
	if (crt_bss_padding[CRT_BSS_PAD_BYTES - 1] != 0)
		show_stage(1, 200, 255, 0); /* Lime means BSS did not clear. */

	show_stage(2, 0, 64, 255);   /* Before FntLoad. */
	FntLoad(960, 0);
	show_stage(3, 0, 208, 64);   /* After FntLoad. */

	show_stage(4, 255, 192, 0);  /* Before six FntOpen allocations. */
	fonts[0] = FntOpen(32, 39, 256, 9, 0, 40);
	fonts[1] = FntOpen(208, 37, 96, 9, 0, 16);
	fonts[2] = FntOpen(8, 104, 304, 48, 0, 160);
	fonts[3] = FntOpen(8, 191, 304, 45, 0, 96);
	fonts[4] = FntOpen(164, 15, 152, 10, 0, 24);
	fonts[5] = FntOpen(24, 177, 272, 34, 0, 64);
	show_stage(5, 0, 220, 220);   /* After FntOpen allocations. */

	show_stage(6, 160, 0, 200);   /* Before the loading-card text/GPU flush. */
	FntPrint(fonts[4], "FUNKIN' PS1");
	FntFlush(fonts[4]);
	FntPrint(fonts[5], "LOADING GAME");
	FntFlush(fonts[5]);
	DrawSync(0);
	show_stage(7, 128, 0, 0);     /* After loading-card font rendering. */

	show_stage(8, 255, 128, 0);   /* Before SpuInit. */
	SpuInit();
	show_stage(9, 255, 0, 0);     /* After SpuInit. */

	show_stage(10, 255, 255, 255); /* Before SPU channel reset. */
	SpuSetKey(0, 0x00ffffff);
	for (int channel = 0; channel < 24; channel++) {
		SPU_CH_ADDR(channel) = getSPUAddr(0x1000u);
		SPU_CH_FREQ(channel) = 0x1000;
	}
	SpuSetKey(1, 0x00ffffff);
	show_stage(11, 220, 30, 150); /* After SPU channel reset. */

	show_stage(12, 50, 180, 80);  /* Before CdInit; no CD reads are issued. */
	CdInit();
	show_stage(13, 150, 80, 30);  /* After CdInit. */

	show_stage(14, 0, 120, 220);  /* Before controller initialization. */
	InitPAD(pad_buffers[0], PAD_BYTES, pad_buffers[1], PAD_BYTES);
	StartPAD();
	ChangeClearPAD(0);
	show_stage(15, 80, 200, 255); /* After controller initialization. */

	(void)fonts;
	show_stage(16, 20, 140, 100); /* CdInit and PAD initialization returned. */
	show_stage(17, 10, 40, 180);  /* Before the first game CD command. */
	int pause_result = CdControlB(CdlPause, 0, 0);
	if (pause_result != 1) {
		show_stage(19, 255, 0, 80);   /* CdlPause returned failure. */
		for (;;) VSync(0);
	}
	show_stage(18, 255, 220, 40);   /* CdlPause returned success. */

	show_stage(20, 255, 128, 0);   /* Before the game's 64 KiB staging allocation. */
	void *page_data = malloc(65536u);
	if (!page_data) {
		show_stage(21, 255, 0, 80); /* Allocation failed. */
		for (;;) VSync(0);
	}
	show_stage(22, 0, 200, 220);   /* Allocation succeeded. */

	show_stage(23, 0, 40, 180);    /* Before CdSearchFile, no sectors read. */
	CdlFILE scene_file;
	if (!CdSearchFile(&scene_file, "\\W1SCENE.BIN")) {
		free(page_data);
		show_stage(24, 255, 0, 80); /* File lookup failed. */
		for (;;) VSync(0);
	}
	if ((unsigned)scene_file.size != 655360u) {
		free(page_data);
		show_stage(25, 255, 180, 0); /* Found, but unexpected file size. */
		for (;;) VSync(0);
	}
	show_stage(26, 0, 220, 80);    /* Found W1SCENE.BIN at expected size. */

	show_stage(28, 128, 0, 180);   /* Before position conversion. */
	int file_sector = CdPosToInt(&scene_file.pos);
	CdlLOC location;
	CdIntToPos(file_sector, &location);
	show_stage(29, 0, 220, 220);   /* After CdPosToInt/CdIntToPos. */

	show_stage(30, 0, 40, 180);    /* Before asynchronous CdlSetloc command. */
	int setloc_result = CdControl(CdlSetloc, &location, 0);
	if (setloc_result != 1) {
		free(page_data);
		show_stage(31, 255, 0, 80); /* CdlSetloc returned failure. */
		for (;;) VSync(0);
	}
	show_stage(32, 0, 220, 80);    /* CdlSetloc returned success. */
	show_stage(33, 255, 255, 255); /* v83: commands passed; staging buffer still valid. */

	/* Read W1SCENE in the same 32-sector pages as the loader; never touch VRAM. */
	show_stage(34, 128, 0, 180);   /* Before callback registration. */
	CdReadCallback(probe_cd_read_handler);
	uint8_t cd_status[8] = {0};
	show_stage(46, 0, 40, 180);   /* Before positioning at scene page 0. */
	CdIntToPos(file_sector, &location);
	if (CdControl(CdlSetloc, &location, 0) != 1) {
		CdReadCallback(0);
		free(page_data);
		show_stage(47, 255, 0, 80);
		for (;;) VSync(0);
	}
	read_callback_count = 0;
	read_callback_event = -1;
	read_callback_has_payload = 0;
	for (unsigned i = 0; i < 4u; i++) read_callback_payload[i] = 0;
	show_stage(48, 0, 40, 180);   /* Before reading the first 8bpp page. */
	int read_result = CdRead((int)SCENE_PAGE_SECTORS, (uint32_t *)page_data, CdlModeSpeed);
	if (read_result != 1) {
		CdReadCallback(0);
		free(page_data);
		show_stage(49, 255, 0, 80);
		for (;;) VSync(0);
	}
	show_stage(50, 0, 220, 220);  /* Page read started. */
	int read_pending = 1;
	for (unsigned frame = 0; frame < CD_READ_TIMEOUT_FRAMES; frame++) {
		read_pending = CdReadSync(1, cd_status);
		if (read_pending <= 0) break;
		VSync(0);
	}
	if (read_pending < 0) {
		CdReadCallback(0);
		free(page_data);
		show_stage(51, 255, 0, 180);
		for (;;) VSync(0);
	}
	if (read_pending > 0) {
		CdReadBreak();
		(void)CdReadSync(0, cd_status);
		CdReadCallback(0);
		free(page_data);
		show_stage(52, 255, 180, 0);
		for (;;) VSync(0);
	}
	if (read_callback_count != 1u) {
		CdReadCallback(0);
		free(page_data);
		show_stage(53, 255, 128, 0);
		for (;;) VSync(0);
	}
	if (read_callback_event != CdlDataReady) {
		CdReadCallback(0);
		free(page_data);
		show_stage(54, 180, 0, 255);
		for (;;) VSync(0);
	}
	if (crc32_bytes((const uint8_t *)page_data, SCENE_PAGE_BYTES) != SCENE_PAGE_CRC32) {
		CdReadCallback(0);
		free(page_data);
		show_stage(55, 255, 0, 0);
		for (;;) VSync(0);
	}
	CdReadCallback(0);
	show_stage(56, 0, 40, 180);   /* First page CRC passed; before LoadImage. */
	DrawSync(0);
	RECT page_rect = {384, 0, 128, 256}; /* 8bpp: 256 texels = 128 VRAM words. */
	LoadImage(&page_rect, (const uint32_t *)page_data);
	DrawSync(0);
	free(page_data);
	show_stage(57, 0, 220, 80);   /* Page transfer completed and DMA buffer freed. */

	show_stage(58, 255, 192, 0);  /* Before uploading the actual page-0 CLUT. */
	RECT palette_rect = {0, 496, 256, 1};
	LoadImage(&palette_rect, (const uint32_t *)bopeebo_visual_palette8);
	DrawSync(0);
	show_stage(59, 0, 220, 220);  /* Palette transfer completed. */

	show_stage(60, 128, 0, 180);  /* Before submitting the textured scene quad. */
	POLY_FT4 scene;
	setPolyFT4(&scene);
	setRGB0(&scene, 128, 128, 128);
	setXY4(&scene, 0, 0, SCREEN_W, 0, 0, SCREEN_H, SCREEN_W, SCREEN_H);
	setUV4(&scene, 0, 0, 255, 0, 0, 191, 255, 191);
	scene.tpage = getTPage(1, 0, 384, 0);
	setClut(&scene, 0, 496);
	DrawPrim((uint32_t *)&scene);
	DrawSync(0);
	/* Small marker confirms a later primitive is visible over the scene. */
	FILL marker;
	setFill(&marker);
	setRGB0(&marker, 0, 255, 0);
	setXY0(&marker, 0, 0);
	setWH(&marker, 8, 8);
	DrawPrim((uint32_t *)&marker);
	DrawSync(0);
	SetDispMask(1);
	for (;;) VSync(0);
}







